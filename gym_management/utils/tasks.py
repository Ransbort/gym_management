# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

"""Daily scheduled maintenance for Gym Management.

Wired up in hooks.py under scheduler_events -> daily. Neither function talks to
the client; they're plain background jobs that keep status fields honest even
when nobody opens the record on the day it actually expires.
"""

import frappe
from frappe.utils import nowdate


def expire_memberships():
	"""Flip any Gym Membership past its end_date from Active to Expired, and
	resync the owning Gym Member's membership_status.
	"""
	rows = frappe.get_all(
		"Gym Membership",
		filters={"status": "Active", "end_date": ["<", nowdate()]},
		fields=["name"],
	)
	for row in rows:
		doc = frappe.get_doc("Gym Membership", row.name)
		doc.status = "Expired"
		doc.flags.ignore_permissions = True
		doc.save()
	if rows:
		frappe.db.commit()


def expire_pt_packages():
	"""Flip any PT Package Purchase past its expiry_date from Active to
	Expired.
	"""
	rows = frappe.get_all(
		"PT Package Purchase",
		filters={"status": "Active", "expiry_date": ["<", nowdate()]},
		fields=["name"],
	)
	for row in rows:
		doc = frappe.get_doc("PT Package Purchase", row.name)
		doc.recalculate_status()
	if rows:
		frappe.db.commit()
