# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document


class GymMembershipPayment(Document):
	def validate(self):
		if not self.member:
			self.member = frappe.db.get_value("Gym Membership", self.gym_membership, "member")
		if flt(self.amount) <= 0:
			frappe.throw(_("Payment amount must be greater than zero."))

	def after_insert(self):
		self.apply_to_membership()

	def apply_to_membership(self):
		"""Adds this payment onto the parent Gym Membership's paid_amount and
		lets that doc's own validate() (see generate.py's Gym Membership
		controller) recompute outstanding_amount/payment_status/status from it -
		same ignore_permissions=True side-effect pattern already used by Gym
		Member.sync_customer() and Trainer.sync_employee().
		"""
		membership = frappe.get_doc("Gym Membership", self.gym_membership)
		membership.paid_amount = flt(membership.paid_amount) + flt(self.amount)
		membership.flags.ignore_permissions = True
		membership.save(ignore_permissions=True)
