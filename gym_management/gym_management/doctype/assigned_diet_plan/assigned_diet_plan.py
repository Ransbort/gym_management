# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.model.document import Document


class AssignedDietPlan(Document):
	def validate(self):
		if self.end_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("End Date cannot be before Start Date."))
		if not self.meals and self.diet_plan:
			plan = frappe.get_doc("Diet Plan", self.diet_plan)
			for row in plan.meals:
				self.append("meals", {
					"meal_time": row.meal_time,
					"food_items": row.food_items,
					"quantity": row.quantity,
					"calories": row.calories,
					"notes": row.notes,
				})
