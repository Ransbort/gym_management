# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GymMember(Document):
	def before_insert(self):
		self.sync_customer()

	def sync_customer(self):
		"""Auto-create a matching Customer when Gym Settings.link_customer_to_gym_member
		is on and this member doesn't already have one picked. Best-effort: a
		failure here (e.g. missing Company defaults) must never block saving the
		Gym Member, so it's logged rather than raised.
		"""
		settings = frappe.get_cached_doc("Gym Settings")
		if not settings.link_customer_to_gym_member or self.customer:
			return
		try:
			customer = frappe.new_doc("Customer")
			customer.customer_name = self.member_name
			customer.customer_type = "Individual"
			if settings.default_customer_group:
				customer.customer_group = settings.default_customer_group
			if settings.default_price_list:
				customer.default_price_list = settings.default_price_list
			customer.flags.ignore_mandatory = True
			customer.insert(ignore_permissions=True)
			self.customer = customer.name
		except Exception:
			frappe.log_error(
				title="Gym Member: Customer auto-create failed", message=frappe.get_traceback()
			)
