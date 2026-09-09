# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt
"""Whitelisted server methods for the Gym Admin dashboard
(gym_management/admin_frontend - a fullscreen staff-facing Vue SPA served at
/gym-admin, modelled on POSNext's /pos app: frappe-ui components, Dexie
offline cache, a PWA-installable shell, Socket.IO realtime).

Unlike portal.py (website users with no DocType permissions, every action
does its own ownership check before an ignore_permissions=True write), every
caller here is a Desk-capable staff member (System Manager / Gym Manager /
Gym Staff - see STAFF_ROLES) who already holds real DocType-level
permissions from generate.py's manager_full()/staff_rw(), so reads/writes
below mostly go through normally. ignore_permissions=True is only used
where this module reads across doctypes the current role may not have direct
read access to (e.g. Mode of Payment) purely to populate dropdowns.
"""

from urllib.parse import quote

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_days, cint, flt, get_datetime, get_url, getdate, nowdate
from frappe.utils.password import check_password

STAFF_ROLES = {"System Manager", "Gym Manager", "Gym Staff"}
MANAGER_ROLES = {"System Manager", "Gym Manager"}


def _check_staff():
	if not STAFF_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Not permitted to use the Gym Admin dashboard."), frappe.PermissionError)


def _check_manager():
	"""Stricter than _check_staff(): Gym Settings is manager_full()/staff_ro()
	in generate.py (Gym Staff can only read it), so the in-dashboard Gym
	Settings popup (Sidebar's gear icon) needs its own check rather than the
	dashboard-wide staff one everything else here uses.
	"""
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Not permitted to change Gym Settings."), frappe.PermissionError)


def _resolve_file_url(path):
	"""Uploaded file URLs (Gym Member.photo, User.user_image) keep spaces and
	other special characters as-is in File.file_url (e.g. "/files/Jane
	Doe.jpg") - quote() avoids relying on the browser to auto-encode an
	unescaped space, same treatment www/gym-admin/index.py already gives the
	gym logo and the signed-in staff member's own avatar.
	"""
	return get_url(quote(path, safe="/")) if path else None


def _attach_member_images(rows):
	"""Resolve each row's own `photo` plus, for any row linked to a portal
	User, that user's `user_image` too - a member often has a login (and
	therefore an avatar) before ever uploading their own gym photo, so the
	frontend can fall back to it. Mutates `rows` in place; each row must
	already carry a `photo` key and, if applicable, a `user` key.
	"""
	user_names = {row.get("user") for row in rows if row.get("user")}
	user_images = {}
	if user_names:
		for u in frappe.get_all("User", filters={"name": ["in", list(user_names)]}, fields=["name", "user_image"]):
			user_images[u.name] = _resolve_file_url(u.user_image)
	for row in rows:
		row["photo"] = _resolve_file_url(row.get("photo"))
		row["user_image"] = user_images.get(row.get("user"))


# ---------------------------------------------------------------------------
# Gym Settings popup (Sidebar's gear icon opens GymSettingsModal.vue instead
# of navigating out to the Desk form) - starts with just theme_color; add a
# field here and to the modal's form together as more of Gym Settings gets
# an in-dashboard editor.
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_gym_settings():
	# Read-only for any dashboard staff (matches Gym Settings' own
	# manager_full()/staff_ro() doctype permissions) - only the save below
	# is manager-only.
	_check_staff()
	settings = frappe.get_cached_doc("Gym Settings")
	return {
		"theme_color": getattr(settings, "theme_color", None) or "#4f46e5",
		"enable_paystack_payments": cint(getattr(settings, "enable_paystack_payments", 0)),
		"default_payment_gateway": getattr(settings, "default_payment_gateway", None),
		# Populates the popup's own gateway dropdown, so turning Paystack on
		# doesn't require a trip to Desk just to pick one - see
		# Gym Settings.validate_paystack_settings(), which now requires this
		# to be set before the checkbox above can be saved checked.
		"payment_gateways": frappe.get_all("Payment Gateway", fields=["name"], order_by="name asc", ignore_permissions=True),
	}


@frappe.whitelist()
def update_gym_settings(theme_color=None, enable_paystack_payments=None, default_payment_gateway=None):
	_check_manager()
	settings = frappe.get_single("Gym Settings")
	if theme_color:
		settings.theme_color = theme_color
	if enable_paystack_payments is not None:
		settings.enable_paystack_payments = cint(enable_paystack_payments)
	if default_payment_gateway is not None:
		settings.default_payment_gateway = default_payment_gateway or None
	settings.save()
	# get_gym_settings()/www/gym-admin/index.py's own settings read both go
	# through get_cached_doc() - without this, the next full page load would
	# keep serving the old color until the site's own cache naturally expired.
	frappe.clear_cache(doctype="Gym Settings")
	return {
		"theme_color": settings.theme_color,
		"enable_paystack_payments": cint(settings.enable_paystack_payments),
		"default_payment_gateway": settings.default_payment_gateway,
	}


# ---------------------------------------------------------------------------
# Session lock (see admin_frontend's useSessionLock.js) - ported from
# POSNext's pos_next.api.auth.verify_session_password
# ---------------------------------------------------------------------------


@frappe.whitelist()
@rate_limit(limit=5, seconds=60)
def verify_session_password(password=None):
	"""Verify the current session user's password for session-lock
	re-authentication. Deliberately not gated by _check_staff() - the point
	of the lock screen is just confirming "is this still the same signed-in
	person", not re-checking dashboard permissions, which can't have changed
	mid-session anyway.

	NOTE: must NOT raise frappe.AuthenticationError here - Frappe's own error
	handler clears the session cookies for that exception type, which would
	log the user out on a single wrong password instead of just rejecting
	the unlock attempt. A structured {"verified": bool} response avoids that.
	"""
	if frappe.session.user == "Guest":
		return {"verified": False, "message": _("Not logged in.")}
	if not password:
		return {"verified": False, "message": _("Password is required")}
	try:
		check_password(frappe.session.user, password)
		return {"verified": True}
	except frappe.AuthenticationError:
		return {"verified": False, "message": _("Incorrect password")}


# ---------------------------------------------------------------------------
# Operational overview
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_overview():
	"""Stat-card + list data for the Overview page. Kept as a handful of cheap
	counts/queries rather than one big report - new cards can be added here
	independently as the dashboard grows.
	"""
	_check_staff()
	today = nowdate()

	checked_in = frappe.get_all(
		"Gym Attendance",
		filters={"check_out_time": ["is", "not set"]},
		fields=["name", "member", "check_in_time"],
		order_by="check_in_time desc",
		ignore_permissions=True,
	)
	member_names = list({row.member for row in checked_in})
	member_lookup = {}
	if member_names:
		for row in frappe.get_all(
			"Gym Member",
			filters={"name": ["in", member_names]},
			fields=["name", "member_name"],
			ignore_permissions=True,
		):
			member_lookup[row.name] = row.member_name
	for row in checked_in:
		row["member_name"] = member_lookup.get(row.member, row.member)

	expiring = frappe.get_all(
		"Gym Membership",
		filters={"status": "Active", "end_date": ["between", [today, add_days(today, 7)]]},
		fields=["name", "member", "member_name", "end_date", "outstanding_amount"],
		order_by="end_date asc",
		limit_page_length=20,
		ignore_permissions=True,
	)

	todays_payments = frappe.get_all(
		"Gym Membership Payment",
		filters={"payment_date": today},
		fields=["amount"],
		ignore_permissions=True,
	)

	return {
		"stats": {
			"total_members": frappe.db.count("Gym Member"),
			"active_members": frappe.db.count("Gym Member", {"membership_status": "Active"}),
			"checked_in_now": len(checked_in),
			"todays_checkins": frappe.db.count("Gym Attendance", {"check_in_time": [">=", today]}),
			"expiring_soon": len(expiring),
			"todays_revenue": sum(flt(row.amount) for row in todays_payments),
		},
		"checked_in": checked_in,
		"expiring_memberships": expiring,
	}


# ---------------------------------------------------------------------------
# Front-desk check-in
# ---------------------------------------------------------------------------


@frappe.whitelist()
def search_members(query=""):
	"""Front-desk member search (name or mobile number) for both the
	check-in screen and the "create membership" member picker.
	"""
	_check_staff()
	query = (query or "").strip()
	filters = {}
	or_filters = None
	if query:
		or_filters = [
			["member_name", "like", f"%{query}%"],
			["phone", "like", f"%{query}%"],
		]
	members = frappe.get_all(
		"Gym Member",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "member_name", "phone", "membership_status"],
		order_by="member_name asc",
		limit_page_length=25,
		ignore_permissions=True,
	)
	open_checkins = frappe.get_all(
		"Gym Attendance",
		filters={"check_out_time": ["is", "not set"]},
		fields=["member"],
		ignore_permissions=True,
	)
	checked_in = {row.member for row in open_checkins}
	for m in members:
		m["checked_in"] = m.name in checked_in
	return members


@frappe.whitelist()
def get_member_form_options():
	"""Dropdown data for CreateMemberModal.vue's one Link field (Customer) -
	everything else on Gym Member is a plain Data/Select/Date field the form
	can just send straight through.

	Portal Access (Gym Member.user) is deliberately left out of quick-create:
	linking a member to a login is still available from the full Desk form,
	but granting portal sign-in isn't a decision a front-desk quick-add
	should make in passing.
	"""
	_check_staff()
	return {
		"customers": frappe.get_all(
			"Customer", fields=["name", "customer_name"], order_by="customer_name asc", limit_page_length=100, ignore_permissions=True
		),
	}


@frappe.whitelist()
def create_member(
	member_name,
	phone,
	email=None,
	gender=None,
	date_of_birth=None,
	address=None,
	emergency_contact_name=None,
	emergency_contact_phone=None,
	date_joined=None,
	health_notes=None,
	customer=None,
):
	"""Quick "Create New Member" popup (see admin_frontend's CreateMemberModal.vue,
	styled after POSNext's own Create New Customer dialog) - used both from the
	check-in search (no match found) and the New Membership member picker, so a
	front-desk staff member never has to leave the dashboard to sign someone up.

	Covers every Gym Member field except: naming_series (auto), photo (Desk-
	only sidebar avatar upload, not part of quick-create), membership_status
	(read-only, kept in sync automatically once this member has memberships -
	see Gym Membership's own sync_member_status()), and user/Portal Access
	(see get_member_form_options()'s docstring - stays a deliberate Desk-only
	step, not part of quick-create).
	"""
	_check_staff()
	member_name = (member_name or "").strip()
	phone = (phone or "").strip()
	if not member_name:
		frappe.throw(_("Member name is required."))
	if not phone:
		frappe.throw(_("Mobile number is required."))

	member = frappe.new_doc("Gym Member")
	member.member_name = member_name
	member.phone = phone
	member.email = (email or "").strip() or None
	member.gender = gender or None
	member.date_of_birth = date_of_birth or None
	member.address = (address or "").strip() or None
	member.emergency_contact_name = (emergency_contact_name or "").strip() or None
	member.emergency_contact_phone = (emergency_contact_phone or "").strip() or None
	member.date_joined = date_joined or nowdate()
	member.health_notes = (health_notes or "").strip() or None
	member.customer = customer or None
	member.insert()
	return {"name": member.name, "member_name": member.member_name, "phone": member.phone}


@frappe.whitelist()
def list_members(query="", status="", limit=50):
	"""Full member directory for the sidebar's Members page (admin_frontend's
	Members.vue) - unlike search_members (a 25-row autocomplete for the
	check-in box and the New Membership member picker), this is the paged,
	filterable table view of every Gym Member.
	"""
	_check_staff()
	filters = {}
	if status:
		filters["membership_status"] = status
	or_filters = None
	query = (query or "").strip()
	if query:
		or_filters = [
			["member_name", "like", f"%{query}%"],
			["phone", "like", f"%{query}%"],
			["email", "like", f"%{query}%"],
		]
	members = frappe.get_all(
		"Gym Member",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "member_name", "phone", "email", "gender", "membership_status", "date_joined", "photo", "user"],
		order_by="member_name asc",
		limit_page_length=cint(limit) or 50,
	)
	_attach_member_images(members)
	return members


@frappe.whitelist()
def get_member(name):
	"""Detail panel for Members.vue - the member's own record plus their
	membership history, mirroring get_membership()'s "doc + related rows"
	shape.
	"""
	_check_staff()
	member = frappe.get_doc("Gym Member", name)
	memberships = frappe.get_all(
		"Gym Membership",
		filters={"member": name},
		fields=["name", "membership_plan", "status", "start_date", "end_date", "outstanding_amount", "payment_status"],
		order_by="start_date desc",
	)
	member_dict = member.as_dict()
	_attach_member_images([member_dict])
	return {
		"member": member_dict,
		"memberships": memberships,
	}


@frappe.whitelist()
def get_checked_in_members():
	_check_staff()
	rows = frappe.get_all(
		"Gym Attendance",
		filters={"check_out_time": ["is", "not set"]},
		fields=["name", "member", "check_in_time"],
		order_by="check_in_time desc",
	)
	member_names = list({row.member for row in rows})
	lookup = {}
	if member_names:
		for row in frappe.get_all(
			"Gym Member", filters={"name": ["in", member_names]}, fields=["name", "member_name", "phone"]
		):
			lookup[row.name] = row
	for row in rows:
		info = lookup.get(row.member) or {}
		row["member_name"] = info.get("member_name", row.member)
		row["phone"] = info.get("phone")
	return rows


@frappe.whitelist()
def check_in(member):
	_check_staff()
	if not frappe.db.exists("Gym Member", member):
		frappe.throw(_("Gym Member {0} not found.").format(member))
	existing = frappe.get_all(
		"Gym Attendance", filters={"member": member, "check_out_time": ["is", "not set"]}, limit_page_length=1
	)
	if existing:
		frappe.throw(_("This member is already checked in."))
	att = frappe.new_doc("Gym Attendance")
	att.member = member
	att.check_in_time = get_datetime()
	att.checked_in_by = frappe.session.user
	att.insert()
	return {"name": att.name, "check_in_time": att.check_in_time}


@frappe.whitelist()
def check_out(member):
	_check_staff()
	open_att = frappe.get_all(
		"Gym Attendance",
		filters={"member": member, "check_out_time": ["is", "not set"]},
		fields=["name"],
		order_by="check_in_time desc",
		limit_page_length=1,
	)
	if not open_att:
		frappe.throw(_("No open check-in found for this member."))
	att = frappe.get_doc("Gym Attendance", open_att[0].name)
	att.check_out_time = get_datetime()
	att.save()
	return {"name": att.name}


# ---------------------------------------------------------------------------
# Memberships & payments
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_membership_form_options():
	"""Dropdown data + defaults for the "New Membership" form - covers every
	Link/Select field on Gym Membership so the form can offer (optional,
	pre-filled) overrides for the ones validate() would otherwise default
	silently (company, payment terms, valid number of days, taxes, cost
	center), not just the handful that were always exposed.
	"""
	_check_staff()
	settings = frappe.get_cached_doc("Gym Settings")
	return {
		# NewMembershipModal.vue's Member field is a plain dropdown, not a
		# type-ahead search (search_members() is still what backs the
		# check-in screen's own search box) - capped at 500 so a very large
		# gym doesn't ship its whole roster on every "New Membership" open;
		# the modal's own "Can't find them?" link still covers anyone past
		# that cap, or brand new.
		"members": frappe.get_all(
			"Gym Member", fields=["name", "member_name", "phone"], order_by="member_name asc", limit_page_length=500
		),
		"membership_plans": frappe.get_all(
			"Membership Plan", fields=["name", "plan_name", "duration_months", "price"], order_by="plan_name asc"
		),
		"membership_plan_types": frappe.get_all(
			"Membership Plan Type", fields=["name", "plan_type_name"], order_by="plan_type_name asc"
		),
		"gym_services": frappe.get_all("Gym Service", fields=["name", "service_name"], order_by="service_name asc"),
		"trainers": frappe.get_all(
			"Trainer", filters={"employment_status": "Active"}, fields=["name", "trainer_name"], order_by="trainer_name asc"
		),
		"mode_of_payments": frappe.get_all("Mode of Payment", fields=["name"], order_by="name asc", ignore_permissions=True),
		"companies": frappe.get_all("Company", fields=["name"], order_by="name asc", ignore_permissions=True),
		"taxes_and_charges_templates": frappe.get_all(
			"Sales Taxes and Charges Template", fields=["name"], order_by="name asc", ignore_permissions=True
		),
		"cost_centers": frappe.get_all("Cost Center", fields=["name"], order_by="name asc", ignore_permissions=True),
		"default_valid_number_of_days": cint(settings.default_valid_number_of_days) or 30,
		"default_company": frappe.defaults.get_global_default("company"),
		# Lets Memberships.vue hide "Send Paystack Payment Link" entirely
		# when the switch is off, instead of showing it and only then
		# failing from send_payment_link()'s own check.
		"enable_paystack_payments": cint(getattr(settings, "enable_paystack_payments", 0)),
	}


@frappe.whitelist()
def backfill_membership_member_names():
	"""One-off repair for Gym Membership rows left with stale/blank derived
	fields, called once, harmlessly, from Memberships.vue's own mount -
	cheap (a filtered get_all plus one set_value per row that still needs
	fixing) and a no-op once every row has already been fixed. Covers three
	unrelated gaps that all share the same root cause and the same fix
	shape, so they're repaired together rather than in three endpoints:

	- member_name / customer: both have fetch_from on the doctype (see
	  create_membership()'s own comments), but fetch_from is a Desk-form
	  (browser JS) convenience only and never ran for memberships created
	  through this dashboard's API before create_membership() was fixed to
	  set them explicitly - older rows were saved with these blank even
	  though member itself was set correctly.
	- conversion_rate: added later than the doctype itself, with a
	  DocType-level default of 1 - but `bench migrate` only adds the new
	  column, it doesn't backfill that default onto rows that already
	  existed, so those rows are left with conversion_rate NULL. That's
	  fatal (not just cosmetic) for frappe_paystack's checkout page, whose
	  PaystackPaymentLog.get_data() does `self.amount * order.conversion_rate`
	  - a plain `float * None` TypeError for any pre-existing membership.
	"""
	_check_staff()
	rows = frappe.get_all(
		"Gym Membership",
		or_filters={
			"member_name": ["in", ["", None]],
			"customer": ["in", ["", None]],
			"conversion_rate": ["in", [0, None]],
		},
		fields=["name", "member", "member_name", "customer", "conversion_rate"],
	)
	fixed = 0
	for row in rows:
		updates = {}
		if not row.member_name and row.member:
			member_name = frappe.db.get_value("Gym Member", row.member, "member_name")
			if member_name:
				updates["member_name"] = member_name
		if not row.customer and row.member:
			customer = frappe.db.get_value("Gym Member", row.member, "customer")
			if customer:
				updates["customer"] = customer
		if not row.conversion_rate:
			updates["conversion_rate"] = 1
		if updates:
			frappe.db.set_value("Gym Membership", row.name, updates, update_modified=False)
			fixed += 1
	if fixed:
		frappe.db.commit()
	return {"fixed": fixed}


@frappe.whitelist()
def list_memberships(membership_plan="", status="", limit=50):
	"""List + filter for Memberships.vue's own table. Filtered by Membership
	Plan (and Status) rather than a free-text search - picking a plan here
	is how staff find "which members are subscribed to Plan X".
	"""
	_check_staff()
	filters = {}
	if status:
		filters["status"] = status
	if membership_plan:
		filters["membership_plan"] = membership_plan
	return frappe.get_all(
		"Gym Membership",
		filters=filters,
		fields=[
			"name", "member", "member_name", "membership_plan", "status",
			"start_date", "end_date", "grand_total", "paid_amount",
			"outstanding_amount", "payment_status",
		],
		order_by="modified desc",
		limit_page_length=cint(limit) or 50,
	)


@frappe.whitelist()
def create_membership(
	member,
	membership_plan,
	membership_plan_type,
	trainer,
	time_slot,
	mode_of_payment,
	start_date=None,
	is_admission_fee=0,
	gym_services=None,
	company=None,
	date=None,
	valid_number_of_days=None,
	number_of_service=None,
	taxes_and_charges=None,
	cost_center=None,
	invoice_reference=None,
):
	"""Covers every settable Gym Membership field. A handful stay
	server-computed and are never accepted here even though they're real
	fields on the doctype: `items` (Order Line - auto-derived from the
	Membership Plan in validate(), same as Desk leaves it unless someone
	adds add-on lines later), `net_total`/`tax_amount`/`grand_total`/
	`end_date`/`status`/`outstanding_amount`/`payment_status` (all computed
	in validate()/calculate_totals()), and `paid_amount` (only ever moved by
	a real Gym Membership Payment record via collect_payment(), so there's
	an honest per-payment audit trail instead of a directly-editable total).
	"""
	_check_staff()
	settings = frappe.get_cached_doc("Gym Settings")
	membership = frappe.new_doc("Gym Membership")
	membership.member = member
	# member_name has fetch_from="member.member_name" on the doctype, but
	# that's a Desk-form (client-side JS) convenience only - a server-side
	# insert() like this one never runs it, so without this line every
	# membership created from this dashboard would show a blank Member
	# column in Memberships.vue's list (list_memberships() reads member_name
	# directly rather than joining to Gym Member on every row).
	membership.member_name = frappe.db.get_value("Gym Member", member, "member_name")
	# Same story as member_name just above: customer also has fetch_from on
	# the doctype (member.customer) but that's Desk-JS only too. Needed so
	# frappe_paystack's PaystackPaymentLog.get_data() (used to render the
	# hosted checkout page - see send_payment_link() below) can resolve
	# order.customer without raising; blank is fine (Gym Settings > Link
	# Customer to Gym Member may be off, or this member predates it).
	membership.customer = frappe.db.get_value("Gym Member", member, "customer")
	membership.company = company or frappe.defaults.get_global_default("company")
	membership.date = date or nowdate()
	membership.membership_plan = membership_plan
	membership.membership_plan_type = membership_plan_type
	membership.trainer = trainer
	membership.time_slot = time_slot
	membership.mode_of_payment = mode_of_payment
	membership.start_date = start_date or nowdate()
	membership.is_admission_fee = cint(is_admission_fee)
	membership.valid_number_of_days = cint(valid_number_of_days) or cint(settings.default_valid_number_of_days)
	membership.number_of_service = cint(number_of_service) or 1
	membership.taxes_and_charges = taxes_and_charges or None
	membership.cost_center = cost_center or None
	membership.invoice_reference = (invoice_reference or "").strip() or None
	if gym_services:
		if isinstance(gym_services, str):
			gym_services = frappe.parse_json(gym_services)
		for service in gym_services:
			membership.append("gym_services", {"gym_service": service})
	membership.insert()
	return {"name": membership.name, "grand_total": membership.grand_total}


@frappe.whitelist()
def get_membership(name):
	_check_staff()
	membership = frappe.get_doc("Gym Membership", name)
	payments = frappe.get_all(
		"Gym Membership Payment",
		filters={"gym_membership": name},
		fields=["name", "amount", "mode_of_payment", "payment_date", "reference_no", "collected_by"],
		order_by="payment_date desc, creation desc",
	)
	return {
		"membership": membership.as_dict(),
		"payments": payments,
	}


@frappe.whitelist()
def collect_payment(gym_membership, amount, mode_of_payment, reference_no=None, remarks=None):
	_check_staff()
	payment = frappe.new_doc("Gym Membership Payment")
	payment.gym_membership = gym_membership
	payment.amount = flt(amount)
	payment.mode_of_payment = mode_of_payment
	payment.payment_date = nowdate()
	payment.reference_no = reference_no
	payment.remarks = remarks
	payment.insert()
	membership = frappe.get_doc("Gym Membership", gym_membership)
	return {
		"name": payment.name,
		"membership": {
			"name": membership.name,
			"paid_amount": membership.paid_amount,
			"outstanding_amount": membership.outstanding_amount,
			"payment_status": membership.payment_status,
			"status": membership.status,
		},
	}


@frappe.whitelist()
def send_payment_link(gym_membership):
	"""Generates a Paystack payment link for this membership's outstanding
	balance and, when the member has an email on file, emails it to them.
	The link is always returned too, so staff can copy/share it directly
	(e.g. over WhatsApp/SMS) - most members here won't have an email on
	file at all.

	Relies on frappe_paystack (https://github.com/... - a separately
	installed third-party app, not part of gym_management itself) for the
	actual link/checkout-page machinery: create_payment_link() logs a
	Pending Paystack Payment Log against this Gym Membership and returns
	its hosted /paystack-checkout URL. The other half of this integration -
	turning a *paid* log back into a real Gym Membership Payment record -
	lives in utils/paystack.py, wired up via hooks.py's doc_events on
	Paystack Payment Log's on_update (fires from the Paystack webhook or
	verify_transaction(), not from anything in this module).

	Two frappe_paystack behaviors this call depends on having been patched/
	added for a non-submittable custom doctype like Gym Membership - see
	that app's own paystack_payment_log.py and this doctype's
	conversion_rate/customer fields:
	  - PaystackPaymentLog.validate_record() used to reject every log for a
	    doctype whose docstatus never leaves 0 (i.e. never gets submitted) -
	    patched to skip that check for non-submittable doctypes.
	  - PaystackPaymentLog.get_data() (used by the checkout page) reads
	    <linked doc>.conversion_rate and .customer, neither of which
	    existed on Gym Membership before those fields were added above.
	"""
	_check_staff()
	if not cint(frappe.get_cached_doc("Gym Settings").enable_paystack_payments):
		frappe.throw(_("Paystack Payments is turned off in Gym Settings > Payments."))
	try:
		from frappe_paystack.api import create_payment_link
	except ImportError:
		frappe.throw(_("Paystack is not installed on this site."))

	membership = frappe.get_doc("Gym Membership", gym_membership)
	if flt(membership.outstanding_amount) <= 0:
		frappe.throw(_("This membership has no outstanding balance to collect."))

	link = create_payment_link("Gym Membership", gym_membership)

	member_email = frappe.db.get_value("Gym Member", membership.member, "email")
	emailed = False
	if member_email:
		frappe.sendmail(
			recipients=[member_email],
			subject=_("Payment link for your {0} membership").format(membership.membership_plan),
			message=_(
				"Hi {0},<br><br>Please use the link below to pay the outstanding balance "
				"of {1} on your {2} membership:<br><br><a href=\"{3}\">{3}</a>"
			).format(membership.member_name, membership.outstanding_amount, membership.membership_plan, link),
			now=True,
		)
		emailed = True
	return {"link": link, "emailed": emailed, "email": member_email or None}
