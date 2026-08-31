# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_time
from frappe.model.document import Document


class ClassSchedule(Document):
	def validate(self):
		if self.start_time and self.end_time and get_time(self.end_time) <= get_time(self.start_time):
			frappe.throw(_("End Time must be after Start Time."))
		if not self.capacity:
			self.capacity = frappe.db.get_value("Class Type", self.class_type, "default_capacity") or 20
