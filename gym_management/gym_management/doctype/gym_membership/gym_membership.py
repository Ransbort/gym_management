# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_months, flt, getdate, nowdate
from frappe.model.document import Document


class GymMembership(Document):
	def validate(self):
		plan = frappe.get_cached_doc("Membership Plan", self.membership_plan)
		self.apply_settings_defaults()
		if not self.items:
			self.append("items", {
				"item_name": plan.plan_name,
				"description": "Membership Plan ({0} month(s))".format(plan.duration_months),
				"qty": 1,
				"rate": plan.price,
			})
		if not self.end_date:
			self.end_date = add_months(self.start_date, plan.duration_months)
		self.calculate_totals()
		if self.status == "Active" and getdate(self.end_date) < getdate(nowdate()):
			self.status = "Expired"

	def apply_settings_defaults(self):
		if self.tax_template or self.payment_terms_template or self.cost_center:
			return
		settings = frappe.get_cached_doc("Gym Settings")
		self.tax_template = self.tax_template or settings.default_tax_template
		self.payment_terms_template = self.payment_terms_template or settings.default_payment_terms_template
		self.cost_center = self.cost_center or settings.default_cost_center

	def calculate_totals(self):
		net_total = 0.0
		for item in self.items:
			item.amount = flt(item.qty) * flt(item.rate)
			net_total += item.amount
		self.net_total = net_total
		tax_rate = frappe.db.get_value("Gym Tax Template", self.tax_template, "tax_rate") if self.tax_template else 0
		self.tax_amount = flt(net_total) * flt(tax_rate) / 100
		self.grand_total = flt(self.net_total) + flt(self.tax_amount)
		self.outstanding_amount = flt(self.grand_total) - flt(self.paid_amount)
		if flt(self.paid_amount) <= 0:
			self.payment_status = "Unpaid"
		elif self.outstanding_amount > 0:
			self.payment_status = "Partially Paid"
		else:
			self.payment_status = "Paid"
		if self.status == "Draft" and flt(self.paid_amount) > 0:
			self.status = "Active"

	def on_update(self):
		self.sync_member_status()

	def on_trash(self):
		self.sync_member_status()

	def sync_member_status(self):
		"""Recompute the parent Gym Member's membership_status from all of their Gym Memberships."""
		status = "No Membership"
		active = frappe.get_all(
			"Gym Membership",
			filters={"member": self.member, "status": "Active", "end_date": [">=", nowdate()]},
			limit_page_length=1,
		)
		if active:
			status = "Active"
		elif frappe.get_all("Gym Membership", filters={"member": self.member, "status": "Suspended"}, limit_page_length=1):
			status = "Suspended"
		elif frappe.get_all("Gym Membership", filters={"member": self.member}, limit_page_length=1):
			status = "Expired"
		frappe.db.set_value("Gym Member", self.member, "membership_status", status)
