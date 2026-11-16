# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

"""Gym Admin dashboard endpoints for doctor-issued gym requests (Patient
Encounter -> Gym Requests table). See integrations/healthcare.py for the
overall flow and the payment sync."""

import frappe
from frappe import _
from frappe.utils import cint, flt, formatdate, nowdate

from gym_management import admin_api
from gym_management.admin_api import _check_staff
from gym_management.integrations.healthcare import GYM_TABLE, REALTIME_EVENT, healthcare_installed


def _require_healthcare():
	if not healthcare_installed():
		frappe.throw(_("The Healthcare app is not installed on this site."))


@frappe.whitelist()
def get_gym_requests(query=""):
	"""Requests prescribed on a non-cancelled encounter that haven't been
	accepted (invoiced) yet, highest priority first."""
	_check_staff()
	if not healthcare_installed():
		return []

	conditions = [
		"gp.parenttype = 'Patient Encounter'",
		f"gp.parentfield = '{GYM_TABLE}'",
		"IFNULL(gp.invoice, '') = ''",
		"pe.docstatus < 2",
	]
	values = {}
	if query:
		conditions.append("(pe.patient LIKE %(q)s OR pe.patient_name LIKE %(q)s)")
		values["q"] = f"%{query}%"

	rows = frappe.db.sql(
		f"""
		SELECT
			gp.name AS request_id, gp.request_type, gp.membership_plan, gp.pt_package,
			gp.priority, gp.notes,
			mp.plan_name, mp.duration_months, mp.price AS plan_price,
			pk.package_name, pk.no_of_sessions, pk.validity_days, pk.price AS package_price,
			pe.name AS encounter, pe.encounter_date, pe.patient, pe.patient_name,
			pe.practitioner_name
		FROM `tabGym Prescription` gp
		INNER JOIN `tabPatient Encounter` pe ON pe.name = gp.parent
		LEFT JOIN `tabMembership Plan` mp ON mp.name = gp.membership_plan
		LEFT JOIN `tabPT Package` pk ON pk.name = gp.pt_package
		WHERE {" AND ".join(conditions)}
		ORDER BY FIELD(gp.priority, 'Low', 'Medium', 'High') DESC, pe.encounter_date DESC, pe.creation DESC
		""",
		values,
		as_dict=True,
	)

	patients = {
		p.name: p
		for p in frappe.get_all(
			"Patient",
			{"name": ["in", list({r.patient for r in rows}) or [""]]},
			["name", "mobile", "phone", "customer"],
		)
	}
	for r in rows:
		p = patients.get(r.patient) or {}
		r["phone"] = p.get("mobile") or p.get("phone") or ""
		r["gym_member"] = _find_member(r.patient, p.get("customer"))
		r["price"] = r.plan_price if r.request_type == "Membership" else r.package_price
		r["encounter_date_label"] = formatdate(r.encounter_date)
	return rows


@frappe.whitelist()
def get_gym_request_count():
	_check_staff()
	return len(get_gym_requests())


def _find_member(patient, customer=None):
	member = frappe.db.get_value("Gym Member", {"custom_patient": patient}, "name")
	if not member and customer:
		member = frappe.db.get_value("Gym Member", {"customer": customer}, "name")
	return member


def _get_or_create_member(patient, phone, notes_line):
	member_name = _find_member(patient.name, patient.customer)
	if member_name:
		member = frappe.get_doc("Gym Member", member_name)
		if not member.get("custom_patient"):
			member.custom_patient = patient.name
		if notes_line:
			member.health_notes = "\n".join(n for n in [member.health_notes, notes_line] if n)
		member.flags.ignore_permissions = True
		member.save(ignore_permissions=True)
		return member

	if not phone:
		frappe.throw(_("Please enter a phone number for {0}").format(patient.patient_name))
	gender_options = (frappe.get_meta("Gym Member").get_field("gender").options or "").split("\n")
	member = frappe.new_doc("Gym Member")
	member.member_name = patient.patient_name
	member.phone = phone
	member.email = patient.get("email") or None
	member.gender = patient.sex if patient.sex in gender_options else None
	member.date_of_birth = patient.get("dob") or None
	member.date_joined = nowdate()
	member.customer = patient.customer
	member.custom_patient = patient.name
	member.health_notes = notes_line or None
	member.insert(ignore_permissions=True)
	return member


def _make_invoice(patient, company, items, taxes_and_charges=None):
	settings = frappe.get_cached_doc("Gym Settings")
	invoice = frappe.new_doc("Sales Invoice")
	invoice.customer = patient.customer
	invoice.patient = patient.name
	invoice.company = company
	invoice.posting_date = nowdate()
	invoice.set_posting_time = 1
	for item in items:
		if settings.get("default_income_account"):
			item["income_account"] = settings.default_income_account
		if settings.get("default_cost_center"):
			item["cost_center"] = settings.default_cost_center
		invoice.append("items", item)
	if taxes_and_charges:
		from erpnext.controllers.accounts_controller import get_taxes_and_charges

		invoice.taxes_and_charges = taxes_and_charges
		for tax in get_taxes_and_charges("Sales Taxes and Charges Template", taxes_and_charges) or []:
			invoice.append("taxes", tax)
	invoice.insert(ignore_permissions=True)
	invoice.submit()
	return invoice


@frappe.whitelist()
def accept_gym_request(
	request_id,
	phone=None,
	membership_plan_type=None,
	trainer=None,
	time_slot_start=None,
	time_slot_end=None,
	start_date=None,
	valid_number_of_days=None,
):
	"""Accept one doctor-issued request: link/create the Gym Member, create
	the membership or PT purchase (Unpaid), raise + submit the Sales
	Invoice for the Cashier Portal, and stamp everything back on the
	encounter row. All in one transaction - any failure rolls it all back."""
	_check_staff()
	_require_healthcare()

	row = frappe.get_doc("Gym Prescription", request_id)
	if row.parenttype != "Patient Encounter":
		frappe.throw(_("Gym request {0} is not linked to a Patient Encounter").format(request_id))
	if row.invoice:
		frappe.throw(_("Gym request {0} has already been accepted ({1})").format(request_id, row.invoice))

	encounter = frappe.get_doc("Patient Encounter", row.parent)
	if encounter.docstatus == 2:
		frappe.throw(_("Encounter {0} is cancelled").format(encounter.name))

	patient = frappe.get_doc("Patient", encounter.patient)
	if not patient.customer:
		frappe.throw(_("Patient {0} has no linked Customer, so the Cashier Portal can't bill them").format(patient.name))

	phone = (phone or "").strip() or patient.get("mobile") or patient.get("phone")
	notes_line = None
	if row.notes:
		notes_line = "{0} - {1} ({2}): {3}".format(
			formatdate(encounter.encounter_date), encounter.practitioner_name or encounter.practitioner, encounter.name, row.notes
		)
	member = _get_or_create_member(patient, phone, notes_line)
	company = encounter.company or frappe.defaults.get_global_default("company")
	settings = frappe.get_cached_doc("Gym Settings")

	stamp = {"gym_member": member.name}
	if row.request_type == "Membership":
		for label, value in (
			(_("Membership Plan Type"), membership_plan_type),
			(_("Trainer"), trainer),
			(_("Time Slot Start"), time_slot_start),
			(_("Time Slot End"), time_slot_end),
		):
			if not value:
				frappe.throw(_("{0} is required").format(label))
		created = admin_api.create_membership(
			member=member.name,
			membership_plan=row.membership_plan,
			membership_plan_type=membership_plan_type,
			trainer=trainer,
			time_slot_start=time_slot_start,
			time_slot_end=time_slot_end,
			start_date=start_date or nowdate(),
			company=company,
			valid_number_of_days=valid_number_of_days,
		)
		membership = frappe.get_doc("Gym Membership", created["name"])
		items = [
			{
				"item_code": it.item_code,
				"description": it.description,
				"qty": it.qty,
				"rate": it.rate,
			}
			for it in membership.items
		]
		if not all(i["item_code"] for i in items):
			frappe.throw(_("Set Default Gym Membership Item in Gym Settings before accepting membership requests."))
		invoice = _make_invoice(patient, company, items, membership.taxes_and_charges)
		membership.db_set("invoice_reference", invoice.name)
		stamp["gym_membership"] = membership.name
	else:
		item_code = settings.get("default_pt_package_item")
		if not item_code:
			frappe.throw(_("Set Default PT Package Item in Gym Settings before accepting PT requests."))
		purchase = admin_api.create_pt_purchase(member=member.name, pt_package=row.pt_package, company=company)
		package = frappe.get_cached_doc("PT Package", row.pt_package)
		invoice = _make_invoice(
			patient,
			company,
			[
				{
					"item_code": item_code,
					"description": _("PT Package: {0} ({1} sessions)").format(package.package_name, package.no_of_sessions),
					"qty": 1,
					"rate": purchase["amount"],
				}
			],
		)
		frappe.db.set_value("PT Package Purchase", purchase["name"], "invoice_reference", invoice.name)
		stamp["pt_package_purchase"] = purchase["name"]

	stamp["invoice"] = invoice.name
	frappe.db.set_value("Gym Prescription", row.name, stamp)

	frappe.publish_realtime(
		"queue_update",
		{"department": "cashier", "message": f"New invoice pending: {invoice.name}", "encounter": None},
		after_commit=True,
	)
	frappe.publish_realtime(REALTIME_EVENT, {"accepted": row.name}, after_commit=True)

	return {
		"member": member.name,
		"member_name": member.member_name,
		"invoice": invoice.name,
		"grand_total": invoice.grand_total,
		"gym_membership": stamp.get("gym_membership"),
		"pt_package_purchase": stamp.get("pt_package_purchase"),
	}


# ---------------------------------------------------------------------------
# Paying a doctor-request invoice from the gym side
# ---------------------------------------------------------------------------
# A membership / PT purchase accepted from a doctor's request is billed by a
# Sales Invoice (the one the hospital Cashier sees). Collecting money for it
# in Gym Admin (Collect Payment, or a Paystack link) must therefore pay that
# invoice with a Payment Entry - not create a Gym Membership Payment / PT
# Payment, whose own Journal Entry would book the income a second time and
# leave the invoice open at the Cashier. integrations/healthcare.py's
# Payment Entry hook then updates paid_amount/status on the gym record, so
# both desks see the same balance whichever one took the money.


def linked_request_invoice(doctype, name):
	"""The submitted doctor-request Sales Invoice billing this record, if any."""
	ref = frappe.db.get_value(doctype, name, "invoice_reference")
	if not ref or not frappe.db.exists("Gym Prescription", {"invoice": ref}):
		return None
	if frappe.db.get_value("Sales Invoice", ref, "docstatus") != 1:
		return None
	return ref


def pay_request_invoice(invoice_name, amount, mode_of_payment, reference_no=None, remarks=None, posting_date=None):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	amount = flt(amount)
	outstanding = flt(frappe.db.get_value("Sales Invoice", invoice_name, "outstanding_amount"))
	if amount <= 0:
		frappe.throw(_("Amount must be greater than zero."))
	if outstanding <= 0:
		frappe.throw(_("Invoice {0} is already fully paid.").format(invoice_name))
	if amount > outstanding:
		frappe.throw(_("Amount {0} is more than the {1} still owed on invoice {2}.").format(amount, outstanding, invoice_name))

	pe = get_payment_entry("Sales Invoice", invoice_name, party_amount=amount)
	pe.mode_of_payment = mode_of_payment
	pe.posting_date = posting_date or nowdate()
	pe.reference_no = reference_no or invoice_name
	pe.reference_date = posting_date or nowdate()
	if remarks:
		pe.remarks = remarks
	pe.flags.ignore_permissions = True
	pe.insert(ignore_permissions=True)
	pe.submit()

	frappe.publish_realtime(
		"queue_update",
		{"department": "front_desk", "message": f"Payment received for {invoice_name}", "encounter": None},
		after_commit=True,
	)
	return pe


def route_payment_to_invoice(doctype, name, amount, mode_of_payment, payment_type="Payment", reference_no=None, remarks=None):
	"""Called at the top of admin_api.collect_payment()/collect_pt_payment().
	Returns None for ordinary gym records (caller carries on as before), or
	the caller's usual response shape after paying the linked invoice."""
	invoice = linked_request_invoice(doctype, name)
	if not invoice:
		return None
	if payment_type == "Refund":
		frappe.throw(
			_("This was billed through hospital invoice {0}. Refunds must be done there (a credit note), not from the gym.").format(invoice)
		)
	pe = pay_request_invoice(invoice, amount, mode_of_payment, reference_no, remarks)
	record = frappe.get_doc(doctype, name)
	if doctype == "Gym Membership":
		return {
			"name": pe.name,
			"membership": {
				"name": record.name,
				"paid_amount": record.paid_amount,
				"outstanding_amount": record.outstanding_amount,
				"payment_status": record.payment_status,
				"status": record.status,
			},
		}
	return {
		"name": pe.name,
		"purchase": {
			"name": record.name,
			"paid_amount": record.paid_amount,
			"outstanding_amount": record.outstanding_amount,
			"payment_status": record.payment_status,
		},
	}
