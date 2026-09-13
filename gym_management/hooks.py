app_name = "gym_management"
app_title = "Gym Management"
app_publisher = "Ransford Borketey"
app_description = "Gym management on ERPNext: members, memberships, attendance, trainers, classes, PT packages, workout plans, lockers and equipment"
app_email = "ransbort@outlook.com"
app_license = "mit"
required_apps = ["erpnext"]
app_home = "/desk/gym-management"

add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/gym_management/images/gym_management.svg",
		"title": app_title,
		"route": app_home,
		"has_permission": "gym_management.install.check_app_permission",
	}
]

# Includes in <head>
# ------------------
# app_include_css = "/assets/gym_management/css/gym_management.css"
# app_include_js = "/assets/gym_management/js/gym_management.js"

# Website Route Rules
# --------------------
# /gym-admin is the fullscreen, PWA-installable staff dashboard
# (gym_management/admin_frontend, modelled on POSNext's /pos). Vue Router
# takes over client-side once the shell has loaded, but a hard reload or a
# shared link straight to a nested route like /gym-admin/memberships is
# still a fresh server-side request for that exact path - without this
# catch-all, Frappe would 404 it before Vue Router ever got a chance to
# take over. Every /gym-admin/* path maps to the same www/gym-admin/
# index.html shell; the bare /gym-admin itself needs no rule of its own
# (default www/gym-admin/index.html routing already handles it).
#
# The old member/trainer self-service website (/gym-portal, gym_management/
# frontend) has been retired now that the team has fully migrated onto this
# Vue admin dashboard - its route rule, website menu item, and dedicated
# API surface (portal.py) are gone along with it. Gym Member.user "Portal
# Access" and the Gym Portal Member/Trainer roles (see install.py) are
# unrelated Desk/permission plumbing and are left in place.
website_route_rules = [
	{"from_route": "/gym-admin/<path:app_path>", "to_route": "gym-admin"},
]

# Document Events
# ----------------
# Reconciles a *paid* frappe_paystack Paystack Payment Log (a separately
# installed third-party app - see admin_api.py's send_payment_link()/
# send_pt_payment_link() and utils/paystack.py) into a real Gym Membership
# Payment or PT Payment record, depending on which doctype the log is linked
# to (each function below is a no-op for the other one). Harmless if
# frappe_paystack isn't installed on a given site - this doctype then simply
# never exists there, so the event never fires.
doc_events = {
	"Paystack Payment Log": {
		"on_update": [
			"gym_management.utils.paystack.sync_gym_membership_payment",
			"gym_management.utils.paystack.sync_pt_purchase_payment",
		],
	},
}

# Installation
# ------------
after_install = "gym_management.install.after_install"
after_migrate = "gym_management.install.after_migrate"

# Scheduled Tasks
# ---------------
scheduler_events = {
	"daily": [
		"gym_management.utils.tasks.expire_memberships",
		"gym_management.utils.tasks.expire_pt_packages",
	],
}
