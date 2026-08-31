app_name = "gym_management"
app_title = "Gym Management"
app_publisher = "Ransford Borketey"
app_description = "Standalone gym management: members, memberships, attendance, trainers, classes, PT packages, workout plans, lockers and equipment"
app_email = "ransbort@outlook.com"
app_license = "mit"
required_apps = []
app_home = "/app/gym-management"

add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/gym_management/images/gym_management.svg",
		"title": app_title,
		"route": app_home,
		"has_permission": "gym_management.gym_management.install.check_app_permission",
	}
]

# Includes in <head>
# ------------------
# app_include_css = "/assets/gym_management/css/gym_management.css"
# app_include_js = "/assets/gym_management/js/gym_management.js"

# Installation
# ------------
after_install = "gym_management.install.after_install"

# Scheduled Tasks
# ---------------
scheduler_events = {
	"daily": [
		"gym_management.gym_management.utils.tasks.expire_memberships",
		"gym_management.gym_management.utils.tasks.expire_pt_packages",
	],
}
