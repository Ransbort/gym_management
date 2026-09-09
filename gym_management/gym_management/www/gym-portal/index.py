# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def get_context(context):
	context.no_cache = 1

	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/gym-portal"
		raise frappe.Redirect

	context.title = _("Gym Portal")
	context.member = frappe.db.get_value(
		"Gym Member", {"user": frappe.session.user}, ["name", "member_name"], as_dict=True
	)
	context.trainer = frappe.db.get_value(
		"Trainer", {"user": frappe.session.user}, ["name", "trainer_name"], as_dict=True
	)
