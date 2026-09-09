# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import json
import os

import frappe

ROLES = ["Gym Manager", "Gym Staff", "Gym Trainer"]

# Portal (website-side, no Desk access) roles for Gym Portal self-service.
PORTAL_ROLES = ["Gym Portal Member", "Gym Portal Trainer"]


def after_install():
	create_roles()
	sync_workspace_sidebars()
	ensure_dashboard_widgets()


def after_migrate():
	create_roles()
	sync_workspace_sidebars()
	remove_retired_erpnext_stand_in_doctypes()
	ensure_dashboard_widgets()


def create_roles():
	for role_name in ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.new_doc("Role")
		role.role_name = role_name
		role.desk_access = 1
		role.flags.ignore_permissions = True
		role.insert(ignore_permissions=True)
	for role_name in PORTAL_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.new_doc("Role")
		role.role_name = role_name
		role.desk_access = 0
		role.flags.ignore_permissions = True
		role.insert(ignore_permissions=True)


def sync_workspace_sidebars():
	"""
	Load Workspace Sidebar fixture JSON files and create/update the
	corresponding DB records.

	Workspace Sidebar is not a standard module-doctype citizen - its JSON
	lives at <app>/workspace_sidebar/*.json, outside the folder structure
	frappe.model.sync scans during bench migrate, so it is never picked up
	automatically the way regular DocType fixtures are. This function does
	that sync explicitly: for each JSON file found, it creates the
	Workspace Sidebar record if missing, or updates an existing one and
	fully replaces its items child table with what's in the file, so a
	stale DB record can never drift from the JSON on disk.
	"""
	app_path = frappe.get_app_path("gym_management")
	sidebar_dir = os.path.join(app_path, "workspace_sidebar")

	if not os.path.isdir(sidebar_dir):
		return

	item_skip_fields = {"doctype", "parent", "parentfield", "parenttype"}

	for filename in sorted(os.listdir(sidebar_dir)):
		if not filename.endswith(".json"):
			continue

		filepath = os.path.join(sidebar_dir, filename)

		try:
			with open(filepath) as f:
				data = json.load(f)
		except (OSError, json.JSONDecodeError):
			continue

		name = data.get("name") or data.get("title")
		if not name:
			continue

		doc_fields = {
			"header_icon": data.get("header_icon"),
			"title": data.get("title"),
			"module": data.get("module"),
			"app": data.get("app"),
			"for_user": data.get("for_user"),
			"module_onboarding": data.get("module_onboarding"),
		}

		if frappe.db.exists("Workspace Sidebar", name):
			doc = frappe.get_doc("Workspace Sidebar", name)
			doc.update(doc_fields)
			doc.items = []
		else:
			doc = frappe.new_doc("Workspace Sidebar")
			doc.name = name
			doc.update(doc_fields)

		for item in data.get("items", []):
			doc.append("items", {k: v for k, v in item.items() if k not in item_skip_fields})

		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)


RETIRED_ERPNEXT_STAND_IN_DOCTYPES = [
	"Gym Tax Template",
	"Gym Payment Term",
	"Gym Payment Terms Template",
	"Gym Cost Center",
	"Gym Department",
]


def remove_retired_erpnext_stand_in_doctypes():
	"""One-time cleanup: Gym Tax Template / Gym Payment Term / Gym Payment
	Terms Template / Gym Cost Center / Gym Department were lightweight local
	stand-ins, built before this bench was confirmed to have ERPNext
	installed. Gym Membership and Trainer now link straight to the real
	Sales Taxes and Charges Template / Payment Terms Template / Cost Center
	/ Department doctypes instead, so these five are dead weight - drop them
	(and their tables) if an earlier install/migrate already created them.
	Safe to run on every migrate: a no-op once they're gone.
	"""
	for doctype in RETIRED_ERPNEXT_STAND_IN_DOCTYPES:
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True)
			print(f"[INFO] Removed retired doctype {doctype}")


def ensure_dashboard_widgets():
	"""Creates two Number Cards (live counts of Gym Member / Membership Plan)
	and one Dashboard Chart (Gym Member registrations by month), then wires
	all three into the Gym Management Workspace's content so they render
	above the shortcuts.

	Each step is wrapped separately and never raises: Number Card/Dashboard
	Chart field names can vary a little across Frappe versions, and a
	mismatch here must never be able to fail bench migrate for the whole
	site over what is, worst case, a missing chart.
	"""
	try:
		_ensure_number_card("Total Gym Members", "Gym Member")
		_ensure_number_card("Total Membership Plans", "Membership Plan")
	except Exception:
		frappe.log_error(title="Gym Management: Number Card setup failed", message=frappe.get_traceback())

	try:
		_ensure_registrations_chart()
	except Exception:
		frappe.log_error(title="Gym Management: Dashboard Chart setup failed", message=frappe.get_traceback())

	try:
		_wire_workspace_widgets()
	except Exception:
		frappe.log_error(title="Gym Management: Workspace widget wiring failed", message=frappe.get_traceback())


def _ensure_number_card(label, document_type):
	if frappe.db.exists("Number Card", label):
		return
	card = frappe.new_doc("Number Card")
	card.label = label
	card.document_type = document_type
	card.type = "Document Type"
	card.function = "Count"
	card.is_public = 1
	card.filters_json = "[]"
	card.module = "Gym Management"
	card.flags.ignore_permissions = True
	card.insert(ignore_permissions=True)


def _ensure_registrations_chart():
	name = "Gym Member Registrations"
	if frappe.db.exists("Dashboard Chart", name):
		return
	chart = frappe.new_doc("Dashboard Chart")
	chart.chart_name = name
	chart.chart_type = "Count"
	chart.document_type = "Gym Member"
	chart.based_on = "creation"
	chart.time_interval = "Monthly"
	chart.timespan = "Last Year"
	chart.type = "Bar"
	chart.timeseries = 1
	chart.is_public = 1
	chart.filters_json = "[]"
	chart.module = "Gym Management"
	chart.flags.ignore_permissions = True
	chart.insert(ignore_permissions=True)


def _wire_workspace_widgets():
	if not frappe.db.exists("Workspace", "Gym Management"):
		return
	ws = frappe.get_doc("Workspace", "Gym Management")

	existing_cards = {row.number_card_name for row in ws.number_cards}
	for label in ("Total Gym Members", "Total Membership Plans"):
		if frappe.db.exists("Number Card", label) and label not in existing_cards:
			ws.append("number_cards", {"number_card_name": label})

	existing_charts = {row.chart_name for row in ws.charts}
	chart_name = "Gym Member Registrations"
	if frappe.db.exists("Dashboard Chart", chart_name) and chart_name not in existing_charts:
		ws.append("charts", {"chart_name": chart_name, "label": chart_name})

	content = json.loads(ws.content or "[]")
	existing_ids = {block.get("id") for block in content}
	new_blocks = []
	if "number_card_total_gym_members" not in existing_ids and frappe.db.exists("Number Card", "Total Gym Members"):
		new_blocks.append({
			"id": "number_card_total_gym_members",
			"type": "number_card",
			"data": {"number_card_name": "Total Gym Members", "col": 4},
		})
	if "number_card_total_membership_plans" not in existing_ids and frappe.db.exists(
		"Number Card", "Total Membership Plans"
	):
		new_blocks.append({
			"id": "number_card_total_membership_plans",
			"type": "number_card",
			"data": {"number_card_name": "Total Membership Plans", "col": 4},
		})
	if "chart_gym_member_registrations" not in existing_ids and frappe.db.exists("Dashboard Chart", chart_name):
		new_blocks.append({
			"id": "chart_gym_member_registrations",
			"type": "chart",
			"data": {"chart_name": chart_name, "col": 12},
		})

	if new_blocks:
		# Insert right after the header block (index 0) so the widgets render
		# above the shortcut cards rather than at the bottom of the page.
		insert_at = 1 if content else 0
		content[insert_at:insert_at] = new_blocks
		ws.content = json.dumps(content)
		ws.flags.ignore_permissions = True
		ws.save(ignore_permissions=True)


def check_app_permission():
	"""Used by add_to_apps_screen; anyone with desk access to one of the
	gym roles (or System Manager) sees the app tile.
	"""
	if frappe.session.user == "Administrator":
		return True
	roles = set(frappe.get_roles())
	return bool(roles.intersection({"System Manager", *ROLES}))
