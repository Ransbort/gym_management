# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EquipmentMaintenanceLog(Document):
	def on_update(self):
		if self.equipment_status_after:
			frappe.db.set_value("Gym Equipment", self.gym_equipment, "status", self.equipment_status_after)
