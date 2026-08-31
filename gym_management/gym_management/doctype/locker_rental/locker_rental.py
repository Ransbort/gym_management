# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LockerRental(Document):
	def validate(self):
		if self.status == "Active":
			current = frappe.db.get_value("Locker", self.locker, "status")
			clashing = frappe.get_all(
				"Locker Rental",
				filters={"locker": self.locker, "status": "Active", "name": ["!=", self.name]},
				limit_page_length=1,
			)
			if clashing or current == "Out of Service":
				frappe.throw(_("Locker {0} is not available.").format(self.locker))

	def on_update(self):
		frappe.db.set_value(
			"Locker", self.locker, "status", "Occupied" if self.status == "Active" else "Available"
		)

	def on_trash(self):
		frappe.db.set_value("Locker", self.locker, "status", "Available")
