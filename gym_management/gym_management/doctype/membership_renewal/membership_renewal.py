# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_months, getdate, nowdate
from frappe.model.document import Document


class MembershipRenewal(Document):
	def validate(self):
		membership = frappe.get_doc("Gym Membership", self.membership)
		self.previous_end_date = membership.end_date
		if not self.new_end_date:
			plan = frappe.get_cached_doc("Membership Plan", membership.membership_plan)
			base = membership.end_date if getdate(membership.end_date) > getdate(nowdate()) else nowdate()
			self.new_end_date = add_months(base, plan.duration_months)

	def on_update(self):
		membership = frappe.get_doc("Gym Membership", self.membership)
		membership.end_date = self.new_end_date
		membership.status = "Active"
		membership.flags.ignore_permissions = True
		# Same reasoning as Gym Membership Payment's apply_to_membership():
		# a renewal shouldn't be blocked by an older membership row missing
		# fields (e.g. Time Slot Start/End) that postdate it.
		membership.flags.ignore_mandatory = True
		membership.save()
