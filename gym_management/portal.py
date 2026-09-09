# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt
"""Whitelisted server methods for the Gym Portal (www/gym-portal/*).

Design note: portal users (Gym Portal Member / Gym Portal Trainer) are
website users with no Desk access and are NOT granted DocType-level
permissions on Gym Membership, Class Booking, Gym Attendance, etc. - wiring
up Frappe's row-level permission engine (User Permissions per member) for a
handful of self-service actions would be a lot of moving parts for what is,
so far, a small and fixed set of actions. Instead, every function here does
its own explicit ownership check (does this session's Gym Member / Trainer
record actually own the thing being read or changed?) before touching data,
then uses ignore_permissions=True for the actual read/write. Keep that
pattern for any new portal action - never skip the ownership check.
"""

import frappe
from frappe import _
from frappe.utils import get_datetime, nowdate


def get_member(user=None):
	"""Returns the Gym Member doc linked to this login, or None."""
	user = user or frappe.session.user
	name = frappe.db.get_value("Gym Member", {"user": user}, "name")
	return frappe.get_doc("Gym Member", name) if name else None


def get_trainer(user=None):
	"""Returns the Trainer doc linked to this login, or None."""
	user = user or frappe.session.user
	name = frappe.db.get_value("Trainer", {"user": user}, "name")
	return frappe.get_doc("Trainer", name) if name else None


def require_member():
	member = get_member()
	if not member:
		frappe.throw(_("No Gym Member profile is linked to your account."), frappe.PermissionError)
	return member


def require_trainer():
	trainer = get_trainer()
	if not trainer:
		frappe.throw(_("No Trainer profile is linked to your account."), frappe.PermissionError)
	return trainer


@frappe.whitelist()
def get_member_dashboard():
	"""Data for the Vue Member dashboard (frontend/src/pages/Member.vue) -
	everything www/gym-portal/member.py used to hand the old Jinja template
	via get_context(), now returned as plain JSON for the SPA to render
	client-side instead.
	"""
	member = require_member()

	memberships = frappe.get_all(
		"Gym Membership",
		filters={"member": member.name},
		fields=["name", "membership_plan", "start_date", "end_date", "status", "grand_total"],
		order_by="start_date desc",
		ignore_permissions=True,
	)

	attendance = frappe.get_all(
		"Gym Attendance",
		filters={"member": member.name},
		fields=["name", "check_in_time", "check_out_time", "duration_minutes"],
		order_by="check_in_time desc",
		limit_page_length=20,
		ignore_permissions=True,
	)

	invoices = []
	if member.customer:
		invoices = frappe.get_all(
			"Sales Invoice",
			filters={"customer": member.customer, "docstatus": ["!=", 2]},
			fields=["name", "posting_date", "grand_total", "outstanding_amount", "status"],
			order_by="posting_date desc",
			limit_page_length=20,
			ignore_permissions=True,
		)

	workout_plans = frappe.get_all(
		"Assigned Workout Plan",
		filters={"member": member.name},
		fields=["name", "workout_plan", "start_date", "end_date", "status"],
		order_by="start_date desc",
		ignore_permissions=True,
	)
	diet_plans = frappe.get_all(
		"Assigned Diet Plan",
		filters={"member": member.name},
		fields=["name", "diet_plan", "start_date", "end_date", "status"],
		order_by="start_date desc",
		ignore_permissions=True,
	)

	upcoming_classes = frappe.get_all(
		"Class Schedule",
		filters={"is_active": 1},
		fields=["name", "class_type", "trainer", "day_of_week", "start_time", "end_time", "room", "capacity"],
		order_by="day_of_week asc, start_time asc",
		ignore_permissions=True,
	)
	my_bookings = frappe.get_all(
		"Class Booking",
		filters={"member": member.name, "status": ["in", ("Booked", "Waitlisted")]},
		fields=["name", "class_schedule", "class_date", "status"],
		order_by="class_date desc",
		ignore_permissions=True,
	)

	pt_packages = frappe.get_all(
		"PT Package",
		fields=["name", "package_name", "no_of_sessions", "validity_days", "price"],
		ignore_permissions=True,
	)
	my_pt_purchases = frappe.get_all(
		"PT Package Purchase",
		filters={"member": member.name},
		fields=[
			"name", "pt_package", "status", "sessions_total",
			"sessions_used", "sessions_remaining", "expiry_date",
		],
		order_by="purchase_date desc",
		ignore_permissions=True,
	)

	return {
		"member": {
			"name": member.name,
			"member_name": member.member_name,
			"membership_status": member.membership_status,
			"customer": member.customer,
		},
		"memberships": memberships,
		"attendance": attendance,
		"invoices": invoices,
		"workout_plans": workout_plans,
		"diet_plans": diet_plans,
		"upcoming_classes": upcoming_classes,
		"my_bookings": my_bookings,
		"pt_packages": pt_packages,
		"my_pt_purchases": my_pt_purchases,
	}


@frappe.whitelist()
def get_trainer_dashboard():
	"""Data for the Vue Trainer dashboard (frontend/src/pages/Trainer.vue) -
	same self-service scope as the old www/gym-portal/trainer.py: only ever
	the logged-in trainer's own schedule/members, never a staff picker (that
	broader staff-facing view lives on the Desk "Trainer" page instead, see
	gym_management/page/trainer/trainer.py).
	"""
	trainer = require_trainer()

	classes = frappe.get_all(
		"Class Schedule",
		filters={"trainer": trainer.name, "is_active": 1},
		fields=["name", "class_type", "day_of_week", "start_time", "end_time", "room", "capacity"],
		order_by="day_of_week asc, start_time asc",
		ignore_permissions=True,
	)

	pt_sessions = frappe.get_all(
		"PT Session",
		filters={"trainer": trainer.name, "status": "Scheduled"},
		fields=["name", "member", "session_date", "start_time", "duration_minutes", "pt_package_purchase"],
		order_by="session_date asc, start_time asc",
		limit_page_length=30,
		ignore_permissions=True,
	)

	member_names = set()
	for row in frappe.get_all(
		"Gym Membership", filters={"trainer": trainer.name, "status": "Active"}, fields=["member"], ignore_permissions=True
	):
		member_names.add(row.member)
	for row in frappe.get_all(
		"Assigned Workout Plan", filters={"assigned_by": trainer.name}, fields=["member"], ignore_permissions=True
	):
		member_names.add(row.member)
	for row in frappe.get_all(
		"Assigned Diet Plan", filters={"assigned_by": trainer.name}, fields=["member"], ignore_permissions=True
	):
		member_names.add(row.member)

	members = []
	if member_names:
		members = frappe.get_all(
			"Gym Member",
			filters={"name": ["in", list(member_names)]},
			fields=["name", "member_name", "membership_status", "phone"],
			order_by="member_name asc",
			ignore_permissions=True,
		)

	open_checkins = frappe.get_all(
		"Gym Attendance", filters={"check_out_time": ["is", "not set"]}, fields=["member"], ignore_permissions=True
	)
	checked_in_members = [row.member for row in open_checkins]

	return {
		"trainer": {"name": trainer.name, "trainer_name": trainer.trainer_name},
		"classes": classes,
		"pt_sessions": pt_sessions,
		"members": members,
		"checked_in_members": checked_in_members,
	}


@frappe.whitelist()
def book_class(class_schedule, class_date=None):
	"""Member self-service: book a seat in an upcoming class. Falls back to
	Waitlisted automatically (via Class Booking's own validate()) if the
	class is already full.
	"""
	member = require_member()
	booking = frappe.new_doc("Class Booking")
	booking.class_schedule = class_schedule
	booking.member = member.name
	booking.class_date = class_date or nowdate()
	booking.flags.ignore_permissions = True
	booking.insert(ignore_permissions=True)
	return {"name": booking.name, "status": booking.status}


@frappe.whitelist()
def cancel_class_booking(name):
	"""Member self-service: cancel one of their own (not yet attended) bookings."""
	member = require_member()
	booking = frappe.get_doc("Class Booking", name)
	if booking.member != member.name:
		frappe.throw(_("You can only cancel your own bookings."), frappe.PermissionError)
	if booking.status in ("Attended", "Cancelled"):
		frappe.throw(_("This booking can no longer be cancelled."))
	booking.status = "Cancelled"
	booking.flags.ignore_permissions = True
	booking.save(ignore_permissions=True)
	return {"name": booking.name, "status": booking.status}


@frappe.whitelist()
def request_pt_package(pt_package):
	"""Member self-service: request a PT Package. This creates a normal PT
	Package Purchase for gym staff to confirm and invoice - no payment is
	collected here.
	"""
	member = require_member()
	purchase = frappe.new_doc("PT Package Purchase")
	purchase.member = member.name
	purchase.pt_package = pt_package
	purchase.flags.ignore_permissions = True
	purchase.insert(ignore_permissions=True)
	return {"name": purchase.name, "status": purchase.status}


@frappe.whitelist()
def trainer_check_in(member):
	"""Trainer self-service: check a member in (opens a new Gym Attendance record)."""
	require_trainer()
	if not frappe.db.exists("Gym Member", member):
		frappe.throw(_("Gym Member {0} not found.").format(member))
	att = frappe.new_doc("Gym Attendance")
	att.member = member
	att.check_in_time = get_datetime()
	att.checked_in_by = frappe.session.user
	att.flags.ignore_permissions = True
	att.insert(ignore_permissions=True)
	return {"name": att.name}


@frappe.whitelist()
def trainer_check_out(member):
	"""Trainer self-service: close a member's most recent open check-in."""
	require_trainer()
	open_att = frappe.get_all(
		"Gym Attendance",
		filters={"member": member, "check_out_time": ["is", "not set"]},
		fields=["name"],
		order_by="check_in_time desc",
		limit_page_length=1,
		ignore_permissions=True,
	)
	if not open_att:
		frappe.throw(_("No open check-in found for this member."))
	att = frappe.get_doc("Gym Attendance", open_att[0].name)
	att.check_out_time = get_datetime()
	att.flags.ignore_permissions = True
	att.save(ignore_permissions=True)
	return {"name": att.name}
