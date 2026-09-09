# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

"""Reconciliation half of the Gym Membership <-> Paystack integration (the
"generate a payment link" half lives in admin_api.py's send_payment_link()).

frappe_paystack (a separately installed third-party app, not part of
gym_management) confirms a payment by saving its own Paystack Payment Log
with status Processed/Completed - from the Paystack webhook, or the
checkout page's synchronous verify_transaction() fallback. Its own
on_update() then tries to auto-reconcile by creating an ERPNext Payment
Entry, reading things like <linked doc>.customer/.debit_to/.conversion_rate
the way a Sales Invoice/Sales Order would have them - none of which describe
a Gym Membership the same way, so that attempt raises and is silently
swallowed by its own broad `except Exception` (logged via frappe.log_error,
otherwise a no-op: harmless, but useless to us).

This module does the real reconciliation for Gym Membership instead: wired
up in hooks.py's doc_events under "Paystack Payment Log": {"on_update": ...},
it turns a paid log into a real Gym Membership Payment record through the
exact same insert() (and therefore the same apply_to_membership() paid_amount/
status recompute) admin_api.py's own collect_payment() uses for a manual
front-desk payment - so a Paystack payment and a cash payment end up
indistinguishable in Gym Membership's own payment history.
"""

import frappe
from frappe.utils import flt, nowdate


def sync_gym_membership_payment(doc, method=None):
	"""doc is a Paystack Payment Log (on_update). Only acts on logs linked to
	a Gym Membership whose payment has actually gone through.
	"""
	try:
		_sync(doc)
	except Exception:
		# Mirrors frappe_paystack's own on_update() - never let a
		# reconciliation bug take down the webhook response or the
		# checkout page's verify_transaction() call.
		frappe.log_error(
			f"Failed to reconcile Paystack Payment Log {doc.name} to a Gym Membership Payment",
			"Gym Management Paystack sync",
		)


def _sync(doc):
	if doc.linked_doctype != "Gym Membership" or not doc.linked_docname:
		return
	if doc.status not in ("Processed", "Completed"):
		return
	if not flt(doc.amount_paid):
		return
	if not frappe.db.exists("Gym Membership", doc.linked_docname):
		return
	# Idempotency: on_update() fires again on every subsequent save of this
	# same log (e.g. frappe_paystack's own _mark_related_payment_requests_paid()
	# branch, or a second webhook delivery for the same event) - a Gym
	# Membership Payment already recorded for this log must never be
	# double-counted onto the membership's paid_amount.
	if frappe.db.exists("Gym Membership Payment", {"reference_no": doc.name}):
		return

	mode_of_payment = frappe.db.get_value(
		"Paystack Gateway Setting", {"enabled": 1, "company": doc.company}, "mode_of_payment"
	) or "Paystack"

	# Same set_user('administrator') pattern frappe_paystack's own on_update()
	# uses before its Payment Entry creation - this can run from a guest
	# webhook request (paystack_webhook is allow_guest=True), and
	# collected_by's default="__user" should read as a real user, not Guest.
	frappe.set_user("Administrator")
	try:
		payment = frappe.new_doc("Gym Membership Payment")
		payment.gym_membership = doc.linked_docname
		payment.amount = flt(doc.amount_paid)
		payment.mode_of_payment = mode_of_payment
		payment.payment_date = doc.payment_date or nowdate()
		payment.reference_no = doc.name
		payment.remarks = f"Paystack payment - {doc.payment_reference or doc.transaction_id or doc.name}"
		payment.flags.ignore_permissions = True
		payment.insert(ignore_permissions=True)
		frappe.db.commit()
	finally:
		frappe.set_user("Guest")
