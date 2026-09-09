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

# Website / Portal
# -----------------
# Adds "Gym Portal" under the website's My Account menu (/me) for logged-in
# members and trainers.
standard_portal_menu_items = [
	{"title": "Gym Portal", "route": "/gym-portal", "reference_doctype": "", "role": ""},
]

# Website Route Rules
# --------------------
# /gym-portal is now the Vue Portal SPA (gym_management/frontend - built
# straight into public/portal, no separate deploy step). Vue Router takes
# over client-side once the page has loaded, but a hard reload or a shared
# link straight to a nested route like /gym-portal/trainer is still a
# fresh server-side request for that exact path - without this catch-all,
# Frappe would 404 it before Vue Router ever got a chance to take over.
# Every /gym-portal/* path maps to the same www/gym-portal/index.html
# shell; the bare /gym-portal itself needs no rule of its own (default
# www/gym-portal/index.html routing already handles it).
#
# /gym-admin is the fullscreen, PWA-installable staff dashboard
# (gym_management/admin_frontend, modelled on POSNext's /pos) - same
# catch-all reasoning as /gym-portal above.
website_route_rules = [
	{"from_route": "/gym-portal/<path:app_path>", "to_route": "gym-portal"},
	{"from_route": "/gym-admin/<path:app_path>", "to_route": "gym-admin"},
]

# Document Events
# ----------------
# Reconciles a *paid* frappe_paystack Paystack Payment Log (a separately
# installed third-party app - see admin_api.py's send_payment_link() and
# utils/paystack.py) into a real Gym Membership Payment record. Harmless if
# frappe_paystack isn't installed on a given site - this doctype then simply
# never exists there, so the event never fires.
doc_events = {
	"Paystack Payment Log": {
		"on_update": "gym_management.utils.paystack.sync_gym_membership_payment",
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
