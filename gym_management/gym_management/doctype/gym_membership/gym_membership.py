# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, add_months, flt, get_time, getdate, nowdate
from frappe.model.document import Document


class GymMembership(Document):
	def validate(self):
		if self.time_slot_start and self.time_slot_end and get_time(self.time_slot_end) <= get_time(self.time_slot_start):
			frappe.throw(_("Time Slot End must be after Time Slot Start."))
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
		# Recompute end_date whenever Activation Date or Valid Number of
		# Days actually changes, not just the first time end_date is blank -
		# otherwise, once set, it's stuck forever and extending a
		# membership by editing either of those two fields silently does
		# nothing. Skipped when neither changed so Membership Renewal's own
		# on_update() (which sets end_date directly, to a plan-based date
		# that doesn't fit this start_date + valid_number_of_days formula)
		# isn't immediately overwritten by this same save().
		dates_changed = self.has_value_changed("start_date") or self.has_value_changed("valid_number_of_days")
		if not self.end_date or dates_changed:
			if self.valid_number_of_days:
				self.end_date = add_days(self.start_date, self.valid_number_of_days)
			else:
				self.end_date = add_months(self.start_date, plan.duration_months)
		self.calculate_totals()
		# Active and Expired both just mean "has the date range been
		# reached" - keep this bidirectional so extending an already-
		# Expired membership's end_date (directly, or via the recompute
		# above) brings it back to Active without a separate Membership
		# Renewal, while an Active one that lapses still flips the other
		# way as before. Other statuses (Draft, Suspended, Cancelled) are
		# untouched here.
		if self.status in ("Active", "Expired"):
			self.status = "Expired" if getdate(self.end_date) < getdate(nowdate()) else "Active"

	def apply_settings_defaults(self, settings):
		if not self.taxes_and_charges and settings.enable_tax:
			self.taxes_and_charges = settings.default_sales_taxes_and_charges_template
		if not self.cost_center:
			self.cost_center = settings.default_cost_center
		if not self.valid_number_of_days:
			self.valid_number_of_days = settings.default_valid_number_of_days

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
