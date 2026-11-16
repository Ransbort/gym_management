# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

"""Healthcare -> Gym integration.

A doctor adds rows to the Patient Encounter's "Gym Requests" table
(custom field `custom_gym_prescription`, child doctype Gym Prescription)
asking for either a Membership Plan or a PT Package. Gym staff see the
un-accepted rows on the Gym Admin dashboard's Requests page
(healthcare_requests.py), and accepting one creates/links the Gym Member,
creates the Gym Membership / PT Package Purchase, and raises a submitted
Sales Invoice that the hospital Cashier Portal collects.

Payment flows back here: when that invoice is paid (Payment Entry) or
cancelled, the membership / purchase paid_amount is recomputed from the
invoice. This deliberately does NOT go through Gym Membership Payment /
PT Payment - those post their own Journal Entry, and the Sales Invoice
has already booked the income, so going through them would double-count.

Everything here is a no-op on sites without the healthcare app: the
custom fields are only created when Patient Encounter exists, and the
doc_events on Patient Encounter simply never fire.
"""

import frappe
from frappe import _
from frappe.utils import flt

GYM_TABLE = "custom_gym_prescription"
REALTIME_EVENT = "gym_request_update"


def healthcare_installed():
	return bool(frappe.db.exists("DocType", "Patient Encounter"))


# ---------------------------------------------------------------------------
# Custom fields (run from install.after_install / after_migrate)
# ---------------------------------------------------------------------------


def setup_custom_fields():
	if not healthcare_installed():
		return
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	encounter_meta = frappe.get_meta("Patient Encounter")
	anchor = "spa_prescription" if encounter_meta.has_field("spa_prescription") else "therapies"

	create_custom_fields(
		{
			"Patient Encounter": [
				{
					"fieldname": "custom_gym_section",
					"label": "Gym",
					"fieldtype": "Section Break",
					"insert_after": anchor,
					"collapsible": 1,
					"collapsible_depends_on": GYM_TABLE,
				},
				{
					"fieldname": GYM_TABLE,
					"label": "Gym Requests",
					"fieldtype": "Table",
					"options": "Gym Prescription",
					"insert_after": "custom_gym_section",
				},
			],
			"Gym Member": [
				{
					"fieldname": "custom_patient",
					"label": "Patient",
					"fieldtype": "Link",
					"options": "Patient",
					"insert_after": "customer",
					"search_index": 1,
				},
			],
		},
		update=True,
	)


# ---------------------------------------------------------------------------
# Patient Encounter doc_events
# ---------------------------------------------------------------------------


def validate_encounter(doc, method=None):
	for row in doc.get(GYM_TABLE) or []:
		if row.request_type == "Membership":
			if not row.membership_plan:
				frappe.throw(_("Row #{0} (Gym Requests): Membership Plan is mandatory").format(row.idx))
			row.pt_package = None
		elif row.request_type == "PT Package":
			if not row.pt_package:
				frappe.throw(_("Row #{0} (Gym Requests): PT Package is mandatory").format(row.idx))
			row.membership_plan = None


def notify_new_gym_requests(doc, method=None):
	"""Same diff-against-before-save pattern as the lab/rehab/spa
	notifiers in healthcare, so unrelated saves don't re-announce."""
	before_save = doc.get_doc_before_save()
	old_names = {row.name for row in before_save.get(GYM_TABLE, [])} if before_save else set()
	new_rows = [r for r in doc.get(GYM_TABLE) or [] if not r.invoice and r.name not in old_names]
	if not new_rows:
		return
	frappe.publish_realtime(
		REALTIME_EVENT,
		{"message": _("New gym request(s) for {0} ({1})").format(doc.patient_name, len(new_rows))},
		after_commit=True,
	)


def block_cancel_with_accepted_requests(doc, method=None):
	accepted = [
		r for r in doc.get(GYM_TABLE) or []
		if r.invoice and frappe.db.get_value("Sales Invoice", r.invoice, "docstatus") == 1
	]
	if accepted:
		frappe.throw(
			_("Cannot cancel this encounter: gym request(s) were already accepted and invoiced ({0}). Cancel those invoices first.").format(
				", ".join(r.invoice for r in accepted)
			)
		)


# ---------------------------------------------------------------------------
# Cashier payment -> gym record sync
# ---------------------------------------------------------------------------


def sync_from_payment_entry(doc, method=None):
	for ref in doc.get("references") or []:
		if ref.reference_doctype == "Sales Invoice":
			sync_invoice(ref.reference_name)


def sync_from_sales_invoice(doc, method=None):
	sync_invoice(doc.name)


def sync_invoice(invoice_name):
	"""Recompute paid_amount on every Gym Membership / PT Package Purchase
	billed through this invoice, as the paid share of the invoice."""
	targets = [
		("Gym Membership", "grand_total"),
		("PT Package Purchase", "amount"),
	]
	linked = [
		(dt, name, total_field)
		for dt, total_field in targets
		for name in frappe.get_all(dt, {"invoice_reference": invoice_name}, pluck="name")
	]
	if not linked:
		return

	inv = frappe.db.get_value(
		"Sales Invoice", invoice_name, ["docstatus", "grand_total", "outstanding_amount"], as_dict=True
	)
	fraction = 0.0
	if inv and inv.docstatus == 1 and flt(inv.grand_total) > 0:
		fraction = max(0.0, min(1.0, (flt(inv.grand_total) - flt(inv.outstanding_amount)) / flt(inv.grand_total)))

	for dt, name, total_field in linked:
		record = frappe.get_doc(dt, name)
		record.paid_amount = flt(flt(record.get(total_field)) * fraction, 2)
		record.flags.ignore_permissions = True
		record.flags.ignore_mandatory = True
		record.save(ignore_permissions=True)
