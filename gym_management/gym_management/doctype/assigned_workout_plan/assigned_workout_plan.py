# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, getdate
from frappe.model.document import Document


class AssignedWorkoutPlan(Document):
	def validate(self):
		if self.duration_weeks:
			self.end_date = add_days(self.start_date, self.duration_weeks * 7)
		elif self.end_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("End Date cannot be before Start Date."))
		if not self.workout_configuration and self.workout_plan:
			plan = frappe.get_doc("Workout Plan", self.workout_plan)
			for row in plan.exercises:
				self.append("workout_configuration", {
					"exercise": row.exercise,
					"sets": row.sets,
					"reps": row.reps,
					"rest_seconds": row.rest_seconds,
					"notes": row.notes,
				})
