# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt
"""Shell page for the Vue Gym Portal SPA (gym_management/frontend - see
that directory's README.md). This page itself renders almost nothing -
just a <div id="app"> and a bit of boot context - Vue Router takes over
from there client-side. hooks.py's website_route_rules sends every
/gym-portal/<anything> request here too (not just the bare /gym-portal),
so a hard reload or a shared link to a nested route like
/gym-portal/trainer still renders this same shell instead of 404ing
before Vue Router gets a chance to pick up that path.

Deliberately no login gate here (unlike the old www/gym-portal/member.py
and trainer.py, which each raised frappe.Redirect for a Guest) - a Guest
still needs this shell to load so the SPA can render its own Login page
client-side. Individual dashboard data calls (portal.get_member_dashboard /
get_trainer_dashboard) still enforce their own require_member()/
require_trainer() checks - see portal.py.
"""

import frappe

from gym_management.portal import get_member, get_trainer


def get_context(context):
	context.title = "Gym Portal"
	context.no_cache = 1

	is_guest = frappe.session.user == "Guest"
	full_name = None
	if not is_guest:
		full_name = frappe.db.get_value("User", frappe.session.user, "full_name")

	member = None if is_guest else get_member()
	trainer = None if is_guest else get_trainer()

	context.portal_boot_json = frappe.as_json(
		{
			"is_guest": is_guest,
			"user": frappe.session.user,
			"full_name": full_name,
			"is_member": bool(member),
			"member_name": member.member_name if member else None,
			"is_trainer": bool(trainer),
			"trainer_name": trainer.trainer_name if trainer else None,
		}
	)
	return context
