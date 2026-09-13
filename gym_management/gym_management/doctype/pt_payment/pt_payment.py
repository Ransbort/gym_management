# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document


class PTPayment(Document):
	def validate(self):
		if not self.member:
			self.member = frappe.db.get_value("PT Package Purchase", self.pt_package_purchase, "member")
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero."))
		if self.payment_type == "Refund":
			already_paid = flt(frappe.db.get_value("PT Package Purchase", self.pt_package_purchase, "paid_amount"))
			if flt(self.amount) > already_paid:
				frappe.throw(_("Refund of {0} exceeds the {1} already paid on this purchase.").format(
					flt(self.amount), already_paid
				))

	def after_insert(self):
		self.apply_to_purchase()
		self.create_accounting_entry()

	def create_accounting_entry(self):
		"""Mirrors Gym Membership Payment.create_accounting_entry() - posts this
		payment (or its reversal, for a Refund) into the real Chart of Accounts
		as a submitted Journal Entry, silently skipped (never blocks the
		payment itself) when Gym Settings > Default Income Account isn't set or
		the Mode of Payment used has no default account configured for this
		purchase's Company - surfaced via the Error Log instead of stopping a
		front-desk staff member from recording a payment.
		"""
		settings = frappe.get_cached_doc("Gym Settings")
		income_account = getattr(settings, "default_income_account", None)
		if not income_account:
			return
		company = frappe.db.get_value("PT Package Purchase", self.pt_package_purchase, "company")
		if not company:
			return
		cash_account = frappe.db.get_value(
			"Mode of Payment Account", {"parent": self.mode_of_payment, "company": company}, "default_account"
		)
		if not cash_account:
			frappe.log_error(
				title="PT Payment: missing Mode of Payment account",
				message=(
					f"No default account configured for Mode of Payment {self.mode_of_payment} "
					f"in Company {company} - could not post {self.name} to the Chart of "
					"Accounts. Set one on that Mode of Payment's Accounts table to fix this "
					"going forward; re-run the dashboard's accounting backfill afterward to "
					"catch this payment up too."
				),
			)
			return
		# Same Party-Type guard as Gym Membership Payment.create_accounting_entry() -
		# a Receivable/Payable account needs a Party this plain cash-in/cash-out
		# posting doesn't set.
		for label, account in (("Mode of Payment", cash_account), ("Default Income Account", income_account)):
			account_type = frappe.db.get_value("Account", account, "account_type")
			if account_type in ("Receivable", "Payable"):
				frappe.log_error(
					title="PT Payment: account requires a Party",
					message=(
						f"{label} account '{account}' is a {account_type} account, which "
						f"requires a Party (Customer/Supplier) on every Journal Entry row - "
						f"this automatic posting doesn't set one, so {self.name} could not "
						f"be posted to the Chart of Accounts. Point {label} at a Cash/Bank "
						"account instead, then re-run the dashboard's accounting backfill."
					),
				)
				return
		try:
			is_refund = self.payment_type == "Refund"
			je = frappe.new_doc("Journal Entry")
			je.voucher_type = "Journal Entry"
			je.company = company
			je.posting_date = self.payment_date
			je.user_remark = _("{0} - {1} for {2} ({3})").format(
				self.name, self.payment_type, self.pt_package_purchase, self.member
			)
			je.append("accounts", {
				"account": cash_account,
				"debit_in_account_currency": 0 if is_refund else flt(self.amount),
				"credit_in_account_currency": flt(self.amount) if is_refund else 0,
			})
			je.append("accounts", {
				"account": income_account,
				"debit_in_account_currency": flt(self.amount) if is_refund else 0,
				"credit_in_account_currency": 0 if is_refund else flt(self.amount),
			})
			je.insert(ignore_permissions=True)
			je.submit()
			self.db_set("journal_entry", je.name, update_modified=False)
		except Exception:
			frappe.log_error(
				title=f"PT Payment {self.name}: failed to post Journal Entry",
				message=frappe.get_traceback(),
			)
			frappe.clear_messages()

	def apply_to_purchase(self):
		"""Adds this payment onto the parent PT Package Purchase's paid_amount
		and lets that doc's own validate() (see generate.py's PT Package
		Purchase controller) recompute outstanding_amount/payment_status from
		it - same ignore_permissions=True side-effect + retry-on-
		TimestampMismatch pattern as Gym Membership Payment.apply_to_membership().
		"""
		signed_amount = -flt(self.amount) if self.payment_type == "Refund" else flt(self.amount)
		for attempt in range(5):
			purchase = frappe.get_doc("PT Package Purchase", self.pt_package_purchase)
			purchase.paid_amount = flt(purchase.paid_amount) + signed_amount
			purchase.flags.ignore_permissions = True
			purchase.flags.ignore_mandatory = True
			try:
				purchase.save(ignore_permissions=True)
				return
			except frappe.TimestampMismatchError:
				if attempt == 4:
					raise
				frappe.db.rollback()
