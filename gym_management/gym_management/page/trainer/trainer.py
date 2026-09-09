# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt
"""Server side for the Desk "Trainer" page (gym_management.page.trainer).

Desk equivalent of the website Trainer dashboard (www/gym-portal/trainer.*):
a Gym Trainer logs into the Desk (not the website) and works from this page
instead of /gym-portal/trainer. Unlike the website portal - built for
website users with no DocType permissions, where every action does its own
ownership check before an ignore_permissions=True write - a Desk user
reaching this page already holds a real role (Gym Trainer / Gym Staff / Gym
Manager / System Manager, see trainer.json's "roles") with its own
DocType-level permissions (see generate.py's trainer_rw() / staff_rw() /
manager_full()), so the mutating calls below (check_in/check_out) insert
and save normally rather than forcing ignore_permissions.

A plain Gym Trainer only ever sees their own linked Trainer record - the
"trainer" argument is ignored for them and silently resolved to their own
profile. Gym Staff/Gym Manager/System Manager may pass any Trainer name to
look at (front-desk staff covering for a trainer, or a manager checking a
member in), which is what the page's own Trainer picker is for.
"""

import frappe
from frappe import _
from frappe.utils import get_datetime

ALLOWED_ROLES = {"System Manager", "Gym Manager", "Gym Staff", "Gym Trainer"}
STAFF_ROLES = {"System Manager", "Gym Manager", "Gym Staff"}


def _check_access():
	if not ALLOWED_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Not permitted to use the Trainer page."), frappe.PermissionError)


def _own_trainer():
	return frappe.db.get_value("Trainer", {"user": frappe.session.user}, "name")


def _resolve_trainer(trainer=None):
	"""A plain Gym Trainer is always pinned to their own record, even if a
	different `trainer` was passed in - only staff-level roles may look at
	someone else's."""
	roles = set(frappe.get_roles())
	own = _own_trainer()
	if roles & STAFF_ROLES:
		return trainer or own
	if not own:
		frappe.throw(_("No Trainer profile is linked to your account."), frappe.PermissionError)
	return own


@frappe.whitelist()
def get_trainers():
	"""Trainer picker options - staff-level roles only; a plain Gym Trainer
	never needs to pick, they only ever see their own record."""
	_check_access()
	if not set(frappe.get_roles()) & STAFF_ROLES:
		return []
	return frappe.get_all(
		"Trainer", fields=["name", "trainer_name"], order_by="trainer_name asc", ignore_permissions=True
	)


@frappe.whitelist()
def get_dashboard(trainer=None):
	_check_access()
	trainer_name = _resolve_trainer(trainer)
	if not trainer_name:
		return {"trainer": None, "can_pick": bool(set(frappe.get_roles()) & STAFF_ROLES)}

	trainer_doc = frappe.get_all(
		"Trainer",
		filters={"name": trainer_name},
		fields=["name", "trainer_name", "department", "status"],
		ignore_permissions=True,
	)
	if not trainer_doc:
		frappe.throw(_("Trainer {0} not found.").format(trainer_name))
	trainer_doc = trainer_doc[0]

	classes = frappe.get_all(
		"Class Schedule",
		filters={"trainer": trainer_name, "is_active": 1},
		fields=["name", "class_type", "day_of_week", "start_time", "end_time", "room", "capacity"],
		order_by="day_of_week asc, start_time asc",
		ignore_permissions=True,
	)

	pt_sessions = frappe.get_all(
		"PT Session",
		filters={"trainer": trainer_name, "status": "Scheduled"},
		fields=["name", "member", "session_date", "start_time", "duration_minutes", "pt_package_purchase"],
		order_by="session_date asc, start_time asc",
		limit_page_length=30,
		ignore_permissions=True,
	)

	member_names = set()
	for row in frappe.get_all(
		"Gym Membership",
		filters={"trainer": trainer_name, "status": "Active"},
		fields=["member"],
		ignore_permissions=True,
	):
		member_names.add(row.member)
	for row in frappe.get_all(
		"Assigned Workout Plan", filters={"assigned_by": trainer_name}, fields=["member"], ignore_permissions=True
	):
		member_names.add(row.member)
	for row in frappe.get_all(
		"Assigned Diet Plan", filters={"assigned_by": trainer_name}, fields=["member"], ignore_permissions=True
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
		"Gym Attendance",
		filters={"check_out_time": ["is", "not set"]},
		fields=["member"],
		ignore_permissions=True,
	)
	checked_in_members = {row.member for row in open_checkins}

	return {
		"trainer": trainer_doc,
		"can_pick": bool(set(frappe.get_roles()) & STAFF_ROLES),
		"classes": classes,
		"pt_sessions": pt_sessions,
		"members": members,
		"checked_in_members": list(checked_in_members),
	}


@frappe.whitelist()
def check_in(member):
	_check_access()
	if not frappe.db.exists("Gym Member", member):
		frappe.throw(_("Gym Member {0} not found.").format(member))
	att = frappe.new_doc("Gym Attendance")
	att.member = member
	att.check_in_time = get_datetime()
	att.checked_in_by = frappe.session.user
	att.insert()
	return {"name": att.name}


@frappe.whitelist()
def check_out(member):
	_check_access()
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
