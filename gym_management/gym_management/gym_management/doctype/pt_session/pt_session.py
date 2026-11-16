# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PTSession(Document):
	def on_update(self):
		frappe.get_doc("PT Package Purchase", self.pt_package_purchase).recalculate_status()

	def on_trash(self):
		frappe.get_doc("PT Package Purchase", self.pt_package_purchase).recalculate_status()
