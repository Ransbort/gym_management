# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class GymSettings(Document):
	def validate(self):
		self.validate_paystack_settings()

	def validate_paystack_settings(self):
		"""Enable Paystack Payments is the actual runtime switch (checked by
		admin_api.py's send_payment_link()); default_payment_gateway can't
		drive gateway selection the way it might elsewhere - frappe_paystack
		doesn't use Frappe's generic Payment Gateway framework at all, it
		matches its own Paystack Gateway Setting by Company - so there's
		nothing for this field to actually select between. What it CAN do is
		catch a misconfiguration upfront (switch on, no gateway recorded)
		rather than let it surface later as a confusing failure the first
		time staff try to send a payment link.
		"""
		if self.enable_paystack_payments and not self.default_payment_gateway:
			frappe.throw(
				_("Set Default Payment Gateway before enabling Paystack Payments."),
				title=_("Missing Payment Gateway"),
			)
