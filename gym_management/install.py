# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe

ROLES = ["Gym Manager", "Gym Staff", "Gym Trainer"]


def after_install():
	create_roles()


def create_roles():
	for role_name in ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.new_doc("Role")
		role.role_name = role_name
		role.desk_access = 1
		role.flags.ignore_permissions = True
		role.insert(ignore_permissions=True)


def check_app_permission():
	"""Used by add_to_apps_screen; anyone with desk access to one of the
	gym roles (or System Manager) sees the app tile.
	"""
	if frappe.session.user == "Administrator":
		return True
	roles = set(frappe.get_roles())
	return bool(roles.intersection({"System Manager", *ROLES}))
