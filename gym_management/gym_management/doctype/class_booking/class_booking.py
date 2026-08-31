# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ClassBooking(Document):
	def validate(self):
		duplicate = frappe.get_all(
			"Class Booking",
			filters={
				"class_schedule": self.class_schedule,
				"class_date": self.class_date,
				"member": self.member,
				"status": ["in", ("Booked", "Waitlisted", "Attended")],
				"name": ["!=", self.name],
			},
			limit_page_length=1,
		)
		if duplicate:
			frappe.throw(_("{0} already has a booking for this class on {1}.").format(self.member, self.class_date))

		if self.status == "Booked":
			capacity = frappe.db.get_value("Class Schedule", self.class_schedule, "capacity") or 0
			confirmed = frappe.db.count(
				"Class Booking",
				filters={
					"class_schedule": self.class_schedule,
					"class_date": self.class_date,
					"status": "Booked",
					"name": ["!=", self.name],
				},
			)
			if capacity and confirmed >= capacity:
				self.status = "Waitlisted"
