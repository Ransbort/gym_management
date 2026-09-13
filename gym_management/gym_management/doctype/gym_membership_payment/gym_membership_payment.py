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
			frappe.throw(_("Amount must be greater than zero."))
		if self.payment_type == "Refund":
			already_paid = flt(frappe.db.get_value("Gym Membership", self.gym_membership, "paid_amount"))
			if flt(self.amount) > already_paid:
				frappe.throw(_("Refund of {0} exceeds the {1} already paid on this membership.").format(
					flt(self.amount), already_paid
				))

	def after_insert(self):
		self.apply_to_membership()
		self.create_accounting_entry()

	def create_accounting_entry(self):
		"""Mirrors this payment (or, for a Refund, its reversal) into the
		real Chart of Accounts as a submitted Journal Entry, so Gym Settings
		> Default Income Account actually receives the cash Collect Payment
		records here instead of that money only ever showing up in this
		doctype's own paid_amount ledger. Silently skipped (never blocks the
		payment itself, same 'graceful when unconfigured' treatment Paystack
		gets elsewhere in this app) when Default Income Account isn't set, or
		when the Mode of Payment used has no default account configured for
		this membership's Company - both are accounts-setup gaps, not payment
		failures, and surface via the Error Log instead of stopping a
		front-desk staff member from recording a payment.
		"""
		settings = frappe.get_cached_doc("Gym Settings")
		income_account = getattr(settings, "default_income_account", None)
		if not income_account:
			return
		company = frappe.db.get_value("Gym Membership", self.gym_membership, "company")
		if not company:
			return
		cash_account = frappe.db.get_value(
			"Mode of Payment Account", {"parent": self.mode_of_payment, "company": company}, "default_account"
		)
		if not cash_account:
			frappe.log_error(
				title="Gym Membership Payment: missing Mode of Payment account",
				message=(
					f"No default account configured for Mode of Payment {self.mode_of_payment} "
					f"in Company {company} - could not post {self.name} to the Chart of "
					"Accounts. Set one on that Mode of Payment's Accounts table to fix this "
					"going forward; re-run the dashboard's accounting backfill afterward to "
					"catch this payment up too."
				),
			)
			return
		# A Receivable/Payable account (e.g. Debtors) requires a Party on
		# every Journal Entry row that touches it - this posting is a plain
		# cash-in/cash-out entry with no Customer/Supplier context, so an
		# account configured as one of those can never work here. Checked up
		# front rather than relying on the try/except below: frappe.throw()
		# queues its message onto frappe.local.message_log before raising,
		# and catching the exception doesn't undo that - so a front-desk
		# staff member would still see a spurious "Party Type and Party is
		# required" popup stacked on their real "Successful" payment screen,
		# the exact bug class frappe_paystack's own on_update() hit before its
		# Sales Invoice/Sales Order guard was added (see paystack_payment_log.py).
		for label, account in (("Mode of Payment", cash_account), ("Default Income Account", income_account)):
			account_type = frappe.db.get_value("Account", account, "account_type")
			if account_type in ("Receivable", "Payable"):
				frappe.log_error(
					title="Gym Membership Payment: account requires a Party",
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
				self.name, self.payment_type, self.gym_membership, self.member
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
				title=f"Gym Membership Payment {self.name}: failed to post Journal Entry",
				message=frappe.get_traceback(),
			)
			# Defense in depth for any other unexpected accounting-validation
			# failure (a closed fiscal year, a missing Cost Center, etc.) not
			# already ruled out above: frappe.throw() queues its message onto
			# frappe.local.message_log before raising, and catching the
			# exception here doesn't undo that on its own - without this, a
			# staff member would still see that error surface as a spurious
			# popup stacked on their real success screen, even though this
			# whole method never re-raises.
			frappe.clear_messages()

	def apply_to_membership(self):
		"""Adds this payment onto the parent Gym Membership's paid_amount and
		lets that doc's own validate() (see generate.py's Gym Membership
		controller) recompute outstanding_amount/payment_status/status from it -
		same ignore_permissions=True side-effect pattern already used by Gym
		Member.sync_customer() and Trainer.sync_employee().

		Retries on a Timestamp Mismatch: two payments landing for the same
		membership close together (e.g. Paystack's webhook and the checkout
		page's own verify_transaction() call both reconciling the same
		charge within moments of each other - see utils/paystack.py) can
		both load this same Gym Membership before either has saved, so
		whichever saves second would otherwise raise instead of silently
		losing that payment's contribution to paid_amount.
		"""
		signed_amount = -flt(self.amount) if self.payment_type == "Refund" else flt(self.amount)
		for attempt in range(5):
			membership = frappe.get_doc("Gym Membership", self.gym_membership)
			membership.paid_amount = flt(membership.paid_amount) + signed_amount
			membership.flags.ignore_permissions = True
			# This is a narrow, system-triggered side effect (a payment landed,
			# so bump paid_amount) - it has nothing to do with fields like
			# Time Slot Start/End, which may be blank on a membership created
			# before those became required. A payment on an older row like
			# that shouldn't be rejected over unrelated missing data.
			membership.flags.ignore_mandatory = True
			try:
				membership.save(ignore_permissions=True)
				return
			except frappe.TimestampMismatchError:
				if attempt == 4:
					raise
				frappe.db.rollback()
