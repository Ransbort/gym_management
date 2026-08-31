# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_datetime
from frappe.model.document import Document


class GymAttendance(Document):
	def validate(self):
		if self.check_out_time:
			if get_datetime(self.check_out_time) < get_datetime(self.check_in_time):
				frappe.throw(_("Check-out time cannot be before check-in time."))
			delta = get_datetime(self.check_out_time) - get_datetime(self.check_in_time)
			self.duration_minutes = int(delta.total_seconds() // 60)
