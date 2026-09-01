# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, add_months, flt, getdate, nowdate
from frappe.model.document import Document


class GymMembership(Document):
	def validate(self):
		plan = frappe.get_cached_doc("Membership Plan", self.membership_plan)
		settings = frappe.get_cached_doc("Gym Settings")
		self.apply_settings_defaults(settings)
		if not self.items:
			self.append("items", {
				"item_code": settings.default_gym_membership_item,
				"description": "Membership Plan: {0} ({1} month(s))".format(plan.plan_name, plan.duration_months),
				"qty": 1,
				"rate": plan.price,
			})
		self.apply_admission_fee(settings)
		if not self.end_date:
			if self.valid_number_of_days:
				self.end_date = add_days(self.start_date, self.valid_number_of_days)
			else:
				self.end_date = add_months(self.start_date, plan.duration_months)
		self.calculate_totals()
		if self.status == "Active" and getdate(self.end_date) < getdate(nowdate()):
			self.status = "Expired"

	def apply_settings_defaults(self, settings):
		if not self.taxes_and_charges and settings.enable_tax:
			self.taxes_and_charges = settings.default_sales_taxes_and_charges_template
		if not self.cost_center:
			self.cost_center = settings.default_cost_center
		if not self.payment_terms_template:
			self.payment_terms_template = settings.default_payment_terms_template
		if not self.valid_number_of_days:
			self.valid_number_of_days = settings.default_valid_number_of_days

	def apply_admission_fee(self, settings):
		"""Adds the Admission Fee Item (Gym Settings) as an Order Line, at the
		Registration Fee amount, when Is Admission Fee is checked and it isn't
		already on the order.
		"""
		if not self.is_admission_fee or not settings.admission_fee_item:
			return
		for item in self.items:
			if item.item_code == settings.admission_fee_item:
				return
		self.append("items", {
			"item_code": settings.admission_fee_item,
			"description": "Admission Fee",
			"qty": 1,
			"rate": settings.registration_fee,
		})

	def calculate_totals(self):
		net_total = 0.0
		for item in self.items:
			item.amount = flt(item.qty) * flt(item.rate)
			net_total += item.amount
		self.net_total = net_total
		tax_rate = 0
		if self.taxes_and_charges:
			tax_rows = frappe.get_all(
				"Sales Taxes and Charges",
				filters={"parent": self.taxes_and_charges, "parenttype": "Sales Taxes and Charges Template"},
				fields=["rate"],
			)
			# Approximation: sums percentage rows as if all are "On Net Total" -
			# covers the common single/flat-rate templates (e.g. GST) but not
			# cascading/compound tax charge types.
			tax_rate = sum(flt(row.rate) for row in tax_rows)
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
