# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt
"""Whitelisted server methods for the Gym Admin dashboard
(gym_management/admin_frontend - a fullscreen staff-facing Vue SPA served at
/gym-admin, modelled on POSNext's /pos app: frappe-ui components, Dexie
offline cache, a PWA-installable shell, Socket.IO realtime).

Every caller here is a Desk-capable staff member (System Manager / Gym Manager /
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
		"default_income_account": getattr(settings, "default_income_account", None),
		# Populates the popup's own gateway dropdown, so turning Paystack on
		# doesn't require a trip to Desk just to pick one - see
		# Gym Settings.validate_paystack_settings(), which now requires this
		# to be set before the checkbox above can be saved checked.
		"payment_gateways": frappe.get_all("Payment Gateway", fields=["name"], order_by="name asc", ignore_permissions=True),
		# Same idea for Default Income Account: real ledger (leaf) accounts
		# only, Income root type only - a staff member configuring this
		# shouldn't be able to pick a group node or, say, an Expense account
		# by mistake. Not filtered by Company here (Account is company-scoped
		# but this dashboard otherwise assumes a single default company - see
		# get_membership_form_options()'s own default_company) - a
		# multi-company gym would need to pick the account for whichever
		# Company its memberships actually use.
		"income_accounts": frappe.get_all(
			"Account",
			filters={"root_type": "Income", "is_group": 0},
			fields=["name", "company"],
			order_by="name asc",
			limit_page_length=200,
			ignore_permissions=True,
		),
	}


@frappe.whitelist()
def update_gym_settings(
	theme_color=None, enable_paystack_payments=None, default_payment_gateway=None, default_income_account=None
):
	_check_manager()
	settings = frappe.get_single("Gym Settings")
	if theme_color:
		settings.theme_color = theme_color
	if enable_paystack_payments is not None:
		settings.enable_paystack_payments = cint(enable_paystack_payments)
	if default_payment_gateway is not None:
		settings.default_payment_gateway = default_payment_gateway or None
	if default_income_account is not None:
		settings.default_income_account = default_income_account or None
	settings.save()
	# get_gym_settings()/www/gym-admin/index.py's own settings read both go
	# through get_cached_doc() - without this, the next full page load would
	# keep serving the old color until the site's own cache naturally expired.
	frappe.clear_cache(doctype="Gym Settings")
	return {
		"theme_color": settings.theme_color,
		"enable_paystack_payments": cint(settings.enable_paystack_payments),
		"default_payment_gateway": settings.default_payment_gateway,
		"default_income_account": settings.default_income_account,
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
	photo=None,
):
	"""Quick "Create New Member" popup (see admin_frontend's CreateMemberModal.vue,
	styled after POSNext's own Create New Customer dialog) - used both from the
	check-in search (no match found) and the New Membership member picker, so a
	front-desk staff member never has to leave the dashboard to sign someone up.

	Covers every Gym Member field except: naming_series (auto), membership_status
	(read-only, kept in sync automatically once this member has memberships -
	see Gym Membership's own sync_member_status()), and user/Portal Access
	(see get_member_form_options()'s docstring - stays a deliberate Desk-only
	step, not part of quick-create).

	photo is a file_url already uploaded via the standard /api/method/upload_file
	endpoint (see admin_frontend's api/frappe.js uploadFile()) before this call -
	an admin or instructor picks the image from the modal's own file input, the
	same "upload first, then reference the URL" two-step every Frappe Attach
	field uses. The doctype's photo field is hidden=1 on the Desk form itself
	(set from the sidebar avatar there instead), but that only affects Desk's
	own rendering - nothing stops a whitelisted method from setting a real
	field directly, so it works the same from this dashboard.
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
	member.photo = (photo or "").strip() or None
	member.insert()
	if member.photo:
		# The upload happened before this doc existed (see docstring above),
		# so the File record it created has no attached_to_doctype/name yet -
		# same re-parenting Desk's own Attach control does once the form it
		# was uploaded from gets saved. Purely bookkeeping (which doc "owns"
		# this file for the Attachments list / cascade-delete), not a
		# permission check, so a plain db.set_value is enough here.
		frappe.db.set_value(
			"File",
			{"file_url": member.photo},
			{"attached_to_doctype": "Gym Member", "attached_to_name": member.name, "attached_to_field": "photo"},
		)
	return {"name": member.name, "member_name": member.member_name, "phone": member.phone, "photo": _resolve_file_url(member.photo)}


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
	membership history and, since the "Fitness & Nutrition" section was
	added, their Body Measurement / Assigned Workout Plan / Assigned Diet
	Plan history too (same three groups Gym Member's own Desk form shows
	under "Linked Forms" / "Fitness & Nutrition" - see generate.py's
	dashboard_links), all mirroring get_membership()'s "doc + related rows"
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
	body_measurements = frappe.get_all(
		"Member Body Measurement",
		filters={"member": name},
		fields=["name", "measurement_date", "height_cm", "weight_kg", "bmi", "weight_status"],
		order_by="measurement_date desc",
	)
	assigned_workout_plans = frappe.get_all(
		"Assigned Workout Plan",
		filters={"member": name},
		fields=["name", "workout_plan", "assigned_by", "start_date", "end_date", "duration_weeks", "status"],
		order_by="start_date desc",
	)
	assigned_diet_plans = frappe.get_all(
		"Assigned Diet Plan",
		filters={"member": name},
		fields=["name", "diet_plan", "assigned_by", "start_date", "end_date", "status"],
		order_by="start_date desc",
	)
	member_dict = member.as_dict()
	_attach_member_images([member_dict])
	return {
		"member": member_dict,
		"memberships": memberships,
		"body_measurements": body_measurements,
		"assigned_workout_plans": assigned_workout_plans,
		"assigned_diet_plans": assigned_diet_plans,
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
# Fitness & Nutrition (Members.vue detail panel - Body Measurements, Assigned
# Workout Plans, Assigned Diet Plans). These mirror the same "Linked Forms" /
# "Fitness & Nutrition" dashboard groups Gym Member's own Desk form shows
# (see generate.py's dashboard_links), but let staff add/view them from the
# dashboard instead of sending them out to the full Desk form.
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_fitness_form_options():
	"""Dropdown data for the "Add Body Measurement" / "Assign Workout Plan" /
	"Assign Diet Plan" popups on Members.vue's detail panel. Workout Plan and
	Diet Plan are reusable templates (staff_ro() for Gym Staff - readable,
	not writable, from here), Trainer mirrors get_membership_form_options()'s
	own trainers list.
	"""
	_check_staff()
	return {
		"workout_plans": frappe.get_all("Workout Plan", fields=["name", "plan_name"], order_by="plan_name asc"),
		"diet_plans": frappe.get_all("Diet Plan", fields=["name", "plan_name"], order_by="plan_name asc"),
		"trainers": frappe.get_all(
			"Trainer", filters={"employment_status": "Active"}, fields=["name", "trainer_name"], order_by="trainer_name asc"
		),
		# For CreateWorkoutPlanModal's exercise-row picker.
		"exercises": frappe.get_all("Exercise", fields=["name", "exercise_name"], order_by="exercise_name asc"),
	}


@frappe.whitelist()
def create_body_measurement(
	member,
	measurement_date=None,
	height_cm=None,
	weight_kg=None,
	chest_cm=None,
	waist_cm=None,
	hip_cm=None,
	arms_cm=None,
	thighs_cm=None,
	body_fat_percent=None,
	notes=None,
):
	"""Add Body Measurement popup (Members.vue). bmi/weight_status are always
	server-computed by Member Body Measurement's own validate()/calculate_bmi()
	- never accepted here, same "computed fields stay computed" rule
	create_membership() follows for Gym Membership's own totals.
	"""
	_check_staff()
	if not (flt(height_cm) and flt(weight_kg)):
		frappe.throw(_("Height and Weight are required."))
	doc = frappe.new_doc("Member Body Measurement")
	doc.member = member
	doc.measurement_date = measurement_date or nowdate()
	doc.height_cm = flt(height_cm)
	doc.weight_kg = flt(weight_kg)
	doc.chest_cm = flt(chest_cm) or None
	doc.waist_cm = flt(waist_cm) or None
	doc.hip_cm = flt(hip_cm) or None
	doc.arms_cm = flt(arms_cm) or None
	doc.thighs_cm = flt(thighs_cm) or None
	doc.body_fat_percent = flt(body_fat_percent) or None
	doc.notes = (notes or "").strip() or None
	doc.insert()
	return doc.as_dict()


@frappe.whitelist()
def create_assigned_workout_plan(
	member, workout_plan=None, assigned_by=None, start_date=None, duration_weeks=None, status="Active"
):
	"""Assign Workout Plan popup (Members.vue). Workout Configuration itself
	is left for the doctype's own validate() to copy over from the chosen
	Workout Plan template when one is picked (or left for a trainer to fill
	in later from the full Desk form for a "Custom" assignment) - not
	collected in this quick-assign form, the same "quick create, refine
	later in Desk if needed" shape create_membership() takes for Order Line.
	"""
	_check_staff()
	doc = frappe.new_doc("Assigned Workout Plan")
	doc.member = member
	doc.workout_plan = workout_plan or None
	doc.assigned_by = assigned_by or None
	doc.start_date = start_date or nowdate()
	doc.duration_weeks = cint(duration_weeks) or 4
	doc.status = status or "Active"
	doc.insert()
	return doc.as_dict()


@frappe.whitelist()
def create_workout_plan(plan_name, goal=None, description=None, exercises=None):
	"""The "Create new template" link on the Assign Workout Plan popup
	(AssignWorkoutPlanModal.vue) - lets a Gym Manager (or Gym Trainer, which
	also has trainer_rw() on this doctype in generate.py) define a reusable
	Workout Plan without leaving the dashboard for the full Desk form. A
	plain insert() (no ignore_permissions) so Gym Staff, who only has
	staff_ro() here, is correctly turned away with Frappe's own
	PermissionError rather than this endpoint quietly granting more access
	than the doctype itself allows.

	exercises is a list of {exercise, sets, reps, rest_seconds, notes} rows,
	the same shape as the Workout Plan Exercise child table; rows missing an
	Exercise are dropped rather than rejected, so a half-filled blank row
	left over from the UI doesn't block saving the template.
	"""
	_check_staff()
	plan = frappe.new_doc("Workout Plan")
	plan.plan_name = plan_name
	plan.goal = goal or None
	plan.description = (description or "").strip() or None
	if exercises:
		if isinstance(exercises, str):
			exercises = frappe.parse_json(exercises)
		for row in exercises:
			if not row.get("exercise"):
				continue
			plan.append("exercises", {
				"exercise": row.get("exercise"),
				"sets": cint(row.get("sets")) or 3,
				"reps": (row.get("reps") or "").strip() or "8-12",
				"rest_seconds": cint(row.get("rest_seconds")) or 60,
				"notes": (row.get("notes") or "").strip() or None,
			})
	plan.insert()
	return plan.as_dict()


@frappe.whitelist()
def create_assigned_diet_plan(member, diet_plan=None, assigned_by=None, start_date=None, end_date=None, status="Active"):
	"""Assign Diet Plan popup (Members.vue). Meals are left for the doctype's
	own validate() to copy over from the chosen Diet Plan template, same
	shape as create_assigned_workout_plan() above.
	"""
	_check_staff()
	doc = frappe.new_doc("Assigned Diet Plan")
	doc.member = member
	doc.diet_plan = diet_plan or None
	doc.assigned_by = assigned_by or None
	doc.start_date = start_date or nowdate()
	doc.end_date = end_date or None
	doc.status = status or "Active"
	doc.insert()
	return doc.as_dict()


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
	fixing) and a no-op once every row has already been fixed. Covers four
	unrelated gaps that all share the same root cause and the same fix
	shape, so they're repaired together rather than in four endpoints:

	- member_name / customer / currency: all three have fetch_from on the
	  doctype (see create_membership()'s own comments), but fetch_from is a
	  Desk-form (browser JS) convenience only and never ran for memberships
	  created through this dashboard's API before create_membership() was
	  fixed to set them explicitly - older rows were saved with these blank
	  even though member/company themselves were set correctly.
	- conversion_rate: added later than the doctype itself, with a
	  DocType-level default of 1 - but `bench migrate` only adds the new
	  column, it doesn't backfill that default onto rows that already
	  existed, so those rows are left with conversion_rate NULL.
	- Both conversion_rate and currency are fatal (not just cosmetic) for
	  frappe_paystack's checkout page, whose PaystackPaymentLog.get_data()
	  does `self.amount * order.conversion_rate` and reads `order.currency`
	  directly - a plain `float * None` TypeError / AttributeError for any
	  pre-existing membership missing either one.
	"""
	_check_staff()
	rows = frappe.get_all(
		"Gym Membership",
		or_filters={
			"member_name": ["in", ["", None]],
			"customer": ["in", ["", None]],
			"conversion_rate": ["in", [0, None]],
			"currency": ["in", ["", None]],
		},
		fields=["name", "member", "company", "member_name", "customer", "conversion_rate", "currency"],
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
		if not row.currency and row.company:
			currency = frappe.db.get_value("Company", row.company, "default_currency")
			if currency:
				updates["currency"] = currency
		if updates:
			frappe.db.set_value("Gym Membership", row.name, updates, update_modified=False)
			fixed += 1

	# Separately: paid_amount can drift from the truth when a Gym
	# Membership Payment's own after_insert() -> apply_to_membership()
	# save() doesn't land (e.g. Paystack's webhook and the checkout page's
	# own verify_transaction() both reconciling the same charge within
	# moments of each other used to be able to lose one side's update to a
	# Timestamp Mismatch - see that doctype's apply_to_membership(), which
	# now retries instead). Recomputing from the actual payment rows (the
	# source of truth) rather than trusting the stored total catches any
	# membership already left stuck on Draft/Unpaid despite real, recorded
	# payments.
	totals = {}
	for row in frappe.get_all(
		"Gym Membership Payment", fields=["gym_membership", "amount", "payment_type"], ignore_permissions=True
	):
		signed = -flt(row.amount) if row.payment_type == "Refund" else flt(row.amount)
		totals[row.gym_membership] = flt(totals.get(row.gym_membership)) + signed
	for name, total_paid in totals.items():
		current_paid = frappe.db.get_value("Gym Membership", name, "paid_amount")
		if current_paid is None or abs(flt(current_paid) - flt(total_paid)) > 0.005:
			membership = frappe.get_doc("Gym Membership", name)
			membership.paid_amount = total_paid
			membership.flags.ignore_permissions = True
			# This repair only touches paid_amount - an older membership row
			# missing a field that postdates it (e.g. Time Slot Start/End,
			# added later in this app's life) shouldn't block correcting an
			# unrelated total.
			membership.flags.ignore_mandatory = True
			membership.save(ignore_permissions=True)
			fixed += 1

	if fixed:
		frappe.db.commit()
	return {"fixed": fixed}


@frappe.whitelist()
def backfill_membership_payment_accounting():
	"""One-off, self-healing catch-up for Gym Membership Payment rows that
	predate Gym Settings > Default Income Account (or were recorded before
	it was configured / before a Mode of Payment had a default account set
	for its Company) - posts the same Journal Entry each one would have
	gotten from create_accounting_entry() at insert time, had accounting
	been configured yet. Cheap (a filtered get_all plus one get_doc + method
	call per row still missing a journal_entry) and a no-op once every row
	either has one or has already been logged as unpostable (see that
	method's own missing-account log_error) - same shape as
	backfill_membership_member_names() above, just for accounting instead of
	derived fields. Safe to call on every Memberships.vue mount.
	"""
	_check_staff()
	rows = frappe.get_all(
		"Gym Membership Payment", filters={"journal_entry": ["in", ["", None]]}, fields=["name"]
	)
	fixed = 0
	for row in rows:
		payment = frappe.get_doc("Gym Membership Payment", row.name)
		payment.create_accounting_entry()
		if payment.journal_entry:
			fixed += 1
	if fixed:
		frappe.db.commit()
	return {"checked": len(rows), "fixed": fixed}


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
	time_slot_start,
	time_slot_end,
	start_date=None,
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
	# Same story again: currency has fetch_from="company.default_currency" on
	# the doctype, Desk-JS only. Needed for the same reason as customer above
	# - PaystackPaymentLog.get_data() reads order.currency directly.
	membership.currency = frappe.db.get_value("Company", membership.company, "default_currency")
	membership.date = date or nowdate()
	membership.membership_plan = membership_plan
	membership.membership_plan_type = membership_plan_type
	membership.trainer = trainer
	membership.time_slot_start = time_slot_start
	membership.time_slot_end = time_slot_end
	membership.start_date = start_date or nowdate()
	membership.valid_number_of_days = cint(valid_number_of_days) or cint(settings.default_valid_number_of_days)
	membership.number_of_service = cint(number_of_service) or 1
	membership.taxes_and_charges = taxes_and_charges or None
	membership.cost_center = cost_center or None
	membership.invoice_reference = (invoice_reference or "").strip() or None
	membership.insert()
	return {"name": membership.name, "grand_total": membership.grand_total}


@frappe.whitelist()
def get_membership(name):
	_check_staff()
	membership = frappe.get_doc("Gym Membership", name)
	payments = frappe.get_all(
		"Gym Membership Payment",
		filters={"gym_membership": name},
		fields=["name", "payment_type", "amount", "mode_of_payment", "payment_date", "reference_no", "collected_by", "journal_entry"],
		order_by="payment_date desc, creation desc",
	)
	return {
		"membership": membership.as_dict(),
		"payments": payments,
	}


@frappe.whitelist()
def collect_payment(gym_membership, amount, mode_of_payment, payment_type="Payment", reference_no=None, remarks=None):
	"""payment_type="Refund" pays back a member with a credit balance (e.g.
	after an overpayment leaves outstanding_amount negative) - subtracts
	from paid_amount instead of adding to it. Gym Membership Payment's own
	validate() rejects a refund larger than what's actually been paid.
	"""
	_check_staff()
	payment = frappe.new_doc("Gym Membership Payment")
	payment.gym_membership = gym_membership
	payment.payment_type = payment_type
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


# ---------------------------------------------------------------------------
# Personal Training (PT Package / PT Package Purchase / PT Session / PT
# Payment) - own sidebar page (PersonalTraining.vue), same "list + detail"
# shape as Memberships.vue above, now with the same Paystack-link + payment-
# ledger + accounting flow too (PT Payment mirrors Gym Membership Payment;
# see that doctype's own controller in generate.py). PT Package Purchase's
# own validate()/recalculate_status()/calculate_payment_status() (see
# generate.py) already derive amount/sessions_total/expiry_date from the
# chosen PT Package, keep sessions_used/sessions_remaining/status in sync
# with its PT Sessions, and keep outstanding_amount/payment_status in sync
# with its PT Payments - this section is mostly a thin pass-through onto that
# existing controller logic, not a reimplementation of it.
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_pt_form_options():
	"""Dropdown data for PersonalTraining.vue's New Purchase / Collect Payment /
	Log Session forms and its own package filter.
	"""
	_check_staff()
	settings = frappe.get_cached_doc("Gym Settings")
	return {
		"members": frappe.get_all(
			"Gym Member", fields=["name", "member_name", "phone"], order_by="member_name asc", limit_page_length=500
		),
		"pt_packages": frappe.get_all(
			"PT Package",
			fields=["name", "package_name", "no_of_sessions", "validity_days", "price"],
			order_by="package_name asc",
		),
		"trainers": frappe.get_all(
			"Trainer", filters={"employment_status": "Active"}, fields=["name", "trainer_name"], order_by="trainer_name asc"
		),
		"mode_of_payments": frappe.get_all("Mode of Payment", fields=["name"], order_by="name asc", ignore_permissions=True),
		# Lets PersonalTraining.vue hide "Send Paystack Payment Link" entirely
		# when the switch is off, same as get_membership_form_options() does
		# for Memberships.vue.
		"enable_paystack_payments": cint(getattr(settings, "enable_paystack_payments", 0)),
	}


@frappe.whitelist()
def create_pt_package(package_name, no_of_sessions, validity_days=90, price=0, description=None):
	"""The "Create new package" link on the New Purchase popup - lets a Gym
	Manager define a reusable PT Package without leaving the dashboard, same
	pattern create_workout_plan() uses for Workout Plan. Plain insert() (no
	ignore_permissions): PT Package is staff_ro() for Gym Staff in
	generate.py, so only a Gym Manager (or System Manager) can actually
	create one here, matching the doctype's own permissions.
	"""
	_check_staff()
	package = frappe.new_doc("PT Package")
	package.package_name = package_name
	package.no_of_sessions = cint(no_of_sessions)
	package.validity_days = cint(validity_days) or 90
	package.price = flt(price)
	package.description = (description or "").strip() or None
	package.insert()
	return package.as_dict()


def _attach_member_names(rows, key="member"):
	"""Bulk-resolve `key` (a Gym Member name) to member_name for a list of
	row dicts, mutating them in place - unlike Gym Membership, PT Package
	Purchase has no member_name field of its own to read directly, so
	list_pt_purchases() and get_pt_purchase() both need this to show a name
	instead of a bare GM-MEM-... id.
	"""
	names = {r.get(key) for r in rows if r.get(key)}
	if not names:
		return
	member_names = {
		m.name: m.member_name
		for m in frappe.get_all("Gym Member", filters={"name": ["in", list(names)]}, fields=["name", "member_name"])
	}
	for row in rows:
		row["member_name"] = member_names.get(row.get(key))


@frappe.whitelist()
def list_pt_purchases(pt_package="", status="", limit=50):
	"""List + filter for PersonalTraining.vue's own table."""
	_check_staff()
	filters = {}
	if status:
		filters["status"] = status
	if pt_package:
		filters["pt_package"] = pt_package
	rows = frappe.get_all(
		"PT Package Purchase",
		filters=filters,
		fields=[
			"name", "member", "pt_package", "purchase_date", "expiry_date", "status",
			"sessions_total", "sessions_used", "sessions_remaining",
			"amount", "paid_amount", "outstanding_amount", "payment_status",
		],
		order_by="modified desc",
		limit_page_length=cint(limit) or 50,
	)
	_attach_member_names(rows)
	return rows


@frappe.whitelist()
def create_pt_purchase(member, pt_package, purchase_date=None, amount=None, company=None, invoice_reference=None):
	"""New Purchase popup - covers every settable PT Package Purchase field.
	expiry_date/sessions_total/sessions_remaining/status/paid_amount/
	outstanding_amount/payment_status all stay computed by the doctype's own
	validate()/recalculate_status()/calculate_payment_status() (see
	generate.py) - amount defaults there too when left blank, same "quick
	create, let the controller fill in the rest" shape create_membership()
	uses for Gym Membership. A purchase always starts Unpaid (paid_amount 0) -
	collect_pt_payment() below is the only thing that ever moves it, exactly
	like Gym Membership's own collect_payment().
	"""
	_check_staff()
	purchase = frappe.new_doc("PT Package Purchase")
	purchase.member = member
	purchase.pt_package = pt_package
	purchase.purchase_date = purchase_date or nowdate()
	if amount:
		purchase.amount = flt(amount)
	purchase.company = company or frappe.defaults.get_global_default("company")
	# customer/currency: fetch_from is Desk-JS only, same story as
	# create_membership()'s own comment on Gym Membership.member_name/customer -
	# needed for frappe_paystack's PaystackPaymentLog.get_data(), used by
	# send_pt_payment_link() below.
	purchase.customer = frappe.db.get_value("Gym Member", member, "customer")
	purchase.currency = frappe.db.get_value("Company", purchase.company, "default_currency")
	purchase.invoice_reference = (invoice_reference or "").strip() or None
	purchase.insert()
	return purchase.as_dict()


@frappe.whitelist()
def get_pt_purchase(name):
	_check_staff()
	purchase = frappe.get_doc("PT Package Purchase", name)
	sessions = frappe.get_all(
		"PT Session",
		filters={"pt_package_purchase": name},
		fields=["name", "trainer", "session_date", "start_time", "duration_minutes", "status", "notes"],
		order_by="session_date desc, creation desc",
	)
	payments = frappe.get_all(
		"PT Payment",
		filters={"pt_package_purchase": name},
		fields=["name", "payment_type", "amount", "mode_of_payment", "payment_date", "reference_no", "collected_by", "journal_entry"],
		order_by="payment_date desc, creation desc",
	)
	purchase_dict = purchase.as_dict()
	_attach_member_names([purchase_dict])
	return {"purchase": purchase_dict, "sessions": sessions, "payments": payments}


@frappe.whitelist()
def create_pt_session(
	pt_package_purchase, trainer, session_date=None, start_time=None, duration_minutes=None, status="Scheduled", notes=None
):
	"""Log Session form on a selected purchase's detail panel. PT Session's
	own on_update() (see generate.py) recalculates the parent purchase's
	sessions_used/sessions_remaining/status immediately after insert, so the
	caller doesn't need a separate refresh step for those - just re-fetching
	get_pt_purchase() afterward picks up the new totals.
	"""
	_check_staff()
	session = frappe.new_doc("PT Session")
	session.pt_package_purchase = pt_package_purchase
	session.trainer = trainer
	session.session_date = session_date or nowdate()
	session.start_time = start_time or None
	session.duration_minutes = cint(duration_minutes) or 60
	session.status = status or "Scheduled"
	session.notes = (notes or "").strip() or None
	session.insert()
	return session.as_dict()


@frappe.whitelist()
def update_pt_session_status(name, status):
	"""Quick status change (Scheduled -> Completed/Cancelled/No-Show) from the
	session history list - a plain save() rather than db_set() so PT
	Session's own on_update() fires and keeps the parent purchase's session
	counts and status in sync.
	"""
	_check_staff()
	session = frappe.get_doc("PT Session", name)
	session.status = status
	session.save()
	return {"name": session.name, "status": session.status}


@frappe.whitelist()
def update_pt_purchase_invoice_reference(name, invoice_reference=None):
	"""Edits just the free-text Invoice Reference from the purchase detail
	panel. Replaces the old update_pt_purchase_payment() now that
	payment_status is computed (see PT Package Purchase.calculate_payment_status()
	in generate.py) rather than being a plain staff-set field - actually
	moving money now goes through collect_pt_payment()/send_pt_payment_link()
	below instead.
	"""
	_check_staff()
	purchase = frappe.get_doc("PT Package Purchase", name)
	purchase.invoice_reference = (invoice_reference or "").strip() or None
	purchase.save()
	return {"name": purchase.name, "invoice_reference": purchase.invoice_reference}


@frappe.whitelist()
def collect_pt_payment(pt_package_purchase, amount, mode_of_payment, payment_type="Payment", reference_no=None, remarks=None):
	"""Collect Payment / Pay Back Member form on a purchase's detail panel -
	mirrors Gym Membership's own collect_payment(). payment_type="Refund"
	pays back a member with a credit balance; PT Payment's own validate()
	(see generate.py) rejects a refund larger than what's actually been paid.
	"""
	_check_staff()
	payment = frappe.new_doc("PT Payment")
	payment.pt_package_purchase = pt_package_purchase
	payment.payment_type = payment_type
	payment.amount = flt(amount)
	payment.mode_of_payment = mode_of_payment
	payment.payment_date = nowdate()
	payment.reference_no = reference_no
	payment.remarks = remarks
	payment.insert()
	purchase = frappe.get_doc("PT Package Purchase", pt_package_purchase)
	return {
		"name": payment.name,
		"purchase": {
			"name": purchase.name,
			"paid_amount": purchase.paid_amount,
			"outstanding_amount": purchase.outstanding_amount,
			"payment_status": purchase.payment_status,
		},
	}


@frappe.whitelist()
def send_pt_payment_link(pt_package_purchase):
	"""Generates a Paystack payment link for this PT purchase's outstanding
	balance and, when the member has an email on file, emails it to them -
	mirrors Gym Membership's own send_payment_link(); see that function's own
	docstring for the frappe_paystack dependency and behaviors this relies on
	(create_payment_link() works against any doctype/docname pair, and PT
	Package Purchase's customer/currency/conversion_rate fields exist for the
	exact same reason Gym Membership's do - PaystackPaymentLog.get_data()
	reads them directly).
	"""
	_check_staff()
	if not cint(frappe.get_cached_doc("Gym Settings").enable_paystack_payments):
		frappe.throw(_("Paystack Payments is turned off in Gym Settings > Payments."))
	try:
		from frappe_paystack.api import create_payment_link
	except ImportError:
		frappe.throw(_("Paystack is not installed on this site."))

	purchase = frappe.get_doc("PT Package Purchase", pt_package_purchase)
	if flt(purchase.outstanding_amount) <= 0:
		frappe.throw(_("This PT purchase has no outstanding balance to collect."))

	link = create_payment_link("PT Package Purchase", pt_package_purchase)

	member_name, member_email = frappe.db.get_value("Gym Member", purchase.member, ["member_name", "email"])
	emailed = False
	if member_email:
		frappe.sendmail(
			recipients=[member_email],
			subject=_("Payment link for your {0} personal training package").format(purchase.pt_package),
			message=_(
				"Hi {0},<br><br>Please use the link below to pay the outstanding balance "
				"of {1} on your {2} personal training package:<br><br><a href=\"{3}\">{3}</a>"
			).format(member_name, purchase.outstanding_amount, purchase.pt_package, link),
			now=True,
		)
		emailed = True
	return {"link": link, "emailed": emailed, "email": member_email or None}


@frappe.whitelist()
def backfill_pt_purchase_derived_fields():
	"""Same shape as backfill_membership_member_names() - repairs PT Package
	Purchase rows left with a blank company/customer/currency/conversion_rate
	(all added after PT Package Purchase itself first shipped). company is
	needed for PT Payment's own accounting postings; customer/currency/
	conversion_rate are needed by frappe_paystack's PaystackPaymentLog.get_data(),
	same as Gym Membership's own fields - fatal (not just cosmetic) for the
	checkout page without them. Safe to call on every PersonalTraining.vue
	mount - a no-op once every row has already been fixed.

	Note: this does NOT synthesize a PT Payment for a purchase that was
	previously marked "Paid" by hand (before this ledger existed) - inventing
	a payment record with a guessed amount/mode of payment would be a false
	accounting entry. Any such purchase will correctly show Unpaid again
	(computed from its real paid_amount of 0) until an actual payment is
	recorded against it.
	"""
	_check_staff()
	default_company = frappe.defaults.get_global_default("company")
	rows = frappe.get_all(
		"PT Package Purchase",
		or_filters={
			"company": ["in", ["", None]],
			"customer": ["in", ["", None]],
			"conversion_rate": ["in", [0, None]],
			"currency": ["in", ["", None]],
		},
		fields=["name", "member", "company", "customer", "conversion_rate", "currency"],
	)
	fixed = 0
	for row in rows:
		updates = {}
		company = row.company
		if not company and default_company:
			updates["company"] = company = default_company
		if not row.customer and row.member:
			customer = frappe.db.get_value("Gym Member", row.member, "customer")
			if customer:
				updates["customer"] = customer
		if not row.conversion_rate:
			updates["conversion_rate"] = 1
		if not row.currency and company:
			currency = frappe.db.get_value("Company", company, "default_currency")
			if currency:
				updates["currency"] = currency
		if updates:
			frappe.db.set_value("PT Package Purchase", row.name, updates, update_modified=False)
			fixed += 1
	if fixed:
		frappe.db.commit()
	return {"fixed": fixed}


@frappe.whitelist()
def backfill_pt_purchase_accounting():
	"""One-off, self-healing catch-up for PT Payment rows that predate Gym
	Settings > Default Income Account (or were recorded before a Mode of
	Payment had a default account set for its Company) - same shape as
	backfill_membership_payment_accounting(). Safe to call on every
	PersonalTraining.vue mount.
	"""
	_check_staff()
	rows = frappe.get_all("PT Payment", filters={"journal_entry": ["in", ["", None]]}, fields=["name"])
	fixed = 0
	for row in rows:
		payment = frappe.get_doc("PT Payment", row.name)
		payment.create_accounting_entry()
		if payment.journal_entry:
			fixed += 1
	if fixed:
		frappe.db.commit()
	return {"checked": len(rows), "fixed": fixed}
