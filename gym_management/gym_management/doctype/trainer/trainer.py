# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate
from frappe.model.document import Document


class Trainer(Document):
	def before_insert(self):
		self.sync_employee()

	def sync_employee(self):
		"""Auto-create a matching Employee when Gym Settings.link_gym_trainer_to_employee
		is on and this trainer doesn't already have one picked. Best-effort, same
		reasoning as Gym Member.sync_customer(): never block saving the Trainer.
		"""
		settings = frappe.get_cached_doc("Gym Settings")
		if not settings.link_gym_trainer_to_employee or self.employee:
			return
		try:
			employee = frappe.new_doc("Employee")
			employee.employee_name = self.trainer_name
			employee.first_name = (self.trainer_name or "").split(" ")[0] or self.trainer_name
			if self.department:
				employee.department = self.department
			employee.date_of_joining = self.date_of_joining or nowdate()
			company = frappe.defaults.get_global_default("company")
			if company:
				employee.company = company
			employee.flags.ignore_mandatory = True
			employee.insert(ignore_permissions=True)
			self.employee = employee.name
		except Exception:
			frappe.log_error(
				title="Trainer: Employee auto-create failed", message=frappe.get_traceback()
			)
