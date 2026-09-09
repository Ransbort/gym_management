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
