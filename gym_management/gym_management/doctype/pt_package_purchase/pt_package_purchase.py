# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, getdate, nowdate
from frappe.model.document import Document


class PTPackagePurchase(Document):
	def validate(self):
		package = frappe.get_cached_doc("PT Package", self.pt_package)
		if not self.amount:
			self.amount = package.price
		if not self.sessions_total:
			self.sessions_total = package.no_of_sessions
		if not self.expiry_date:
			self.expiry_date = add_days(self.purchase_date, package.validity_days)
		self.recalculate_status(save=False)

	def recalculate_status(self, save=True):
		used = frappe.db.count(
			"PT Session", filters={"pt_package_purchase": self.name, "status": "Completed"}
		)
		self.sessions_used = used
		self.sessions_remaining = max((self.sessions_total or 0) - used, 0)
		if self.sessions_remaining <= 0 and (self.sessions_total or 0) > 0:
			self.status = "Completed"
		elif self.expiry_date and getdate(self.expiry_date) < getdate(nowdate()):
			self.status = "Expired"
		else:
			self.status = "Active"
		if save:
			self.db_update()
