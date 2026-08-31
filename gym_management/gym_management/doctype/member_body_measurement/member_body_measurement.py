# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document


class MemberBodyMeasurement(Document):
	def validate(self):
		self.calculate_bmi()

	def calculate_bmi(self):
		if not (self.height_cm and self.weight_kg):
			return
		height_m = flt(self.height_cm) / 100
		if height_m <= 0:
			return
		self.bmi = flt(flt(self.weight_kg) / (height_m * height_m), 2)
		settings = frappe.get_cached_doc("Gym Settings")
		underweight_max = settings.bmi_underweight_max or 18.5
		normal_max = settings.bmi_normal_max or 24.9
		overweight_max = settings.bmi_overweight_max or 29.9
		if self.bmi < underweight_max:
			self.weight_status = "Underweight"
		elif self.bmi <= normal_max:
			self.weight_status = "Normal"
		elif self.bmi <= overweight_max:
			self.weight_status = "Overweight"
		else:
			self.weight_status = "Obese"
