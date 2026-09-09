# Copyright (c) 2026, Ransford Borketey and contributors
# For license information, please see license.txt
"""Shell page for the Gym Admin Vue SPA (gym_management/admin_frontend - see
that directory's README.md). Fullscreen, PWA-installable staff dashboard
modelled on POSNext's /pos: front-desk check-in, an operational overview,
and membership & payments, all client-side via Vue Router once this shell
has loaded.

Same no-server-login-gate pattern as www/gym-portal/index.py: a Guest still
needs this shell to load so the SPA can render its own Login page
client-side, and every actual data call in admin_api.py enforces its own
_check_staff() role check (System Manager / Gym Manager / Gym Staff) before
touching anything.
"""

from urllib.parse import quote

import frappe
from frappe.utils import get_url


def get_context(context):
	context.no_cache = 1

	is_guest = frappe.session.user == "Guest"
	full_name = None
	user_image = None
	is_staff = False
	if not is_guest:
		full_name, user_image = frappe.db.get_value("User", frappe.session.user, ["full_name", "user_image"])
		if user_image:
			user_image = get_url(quote(user_image, safe="/"))
		is_staff = bool({"System Manager", "Gym Manager", "Gym Staff"} & set(frappe.get_roles()))

	# Gym Settings is world-readable-by-staff config, not user data, so this
	# is fetched (cached) for Guest and logged-in requests alike - the
	# header/login screen show the real gym branding even on the login page.
	settings = frappe.get_cached_doc("Gym Settings")
	gym_name = settings.gym_name or None
	# quote(): uploaded file names keep spaces/special characters as-is in
	# File.file_url (e.g. "/files/Pep Sports Limited Logo.png") - browsers
	# usually auto-encode an unescaped space in an <img src>, but this
	# avoids relying on that for less common characters too.
	gym_logo = get_url(quote(settings.logo, safe="/")) if settings.logo else None
	# Both also drive the browser tab itself (index.html's <title>/favicon),
	# not just the in-app header - set on context directly since a Jinja
	# template only sees what's assigned to context, not this function's
	# local variables.
	context.title = gym_name or "Gym Admin"
	context.gym_logo = gym_logo
	# getattr(), not settings.theme_color: this field only exists in the DB
	# once this app's `theme_color` DocField change has actually been
	# migrated in (`bench migrate` / `bench reload-doctype "Gym Settings"`)
	# - falling back here means a not-yet-migrated site still renders the
	# dashboard instead of a hard 500 on this one field.
	theme_color = getattr(settings, "theme_color", None) or "#4f46e5"
	# Same not-yet-migrated-site guard as theme_color above - these two
	# fields are new too (see generate.py's Gym Settings "Security" section).
	enable_session_lock = bool(getattr(settings, "enable_session_lock", 0))
	session_lock_timeout = getattr(settings, "session_lock_timeout", None) or 5

	context.admin_boot_json = frappe.as_json(
		{
			"is_guest": is_guest,
			"user": frappe.session.user,
			"full_name": full_name,
			"user_image": user_image,
			"is_staff": is_staff,
			"site_name": frappe.local.site,
			"gym_name": gym_name,
			"gym_logo": gym_logo,
			"theme_color": theme_color,
			"enable_session_lock": enable_session_lock,
			"session_lock_timeout": session_lock_timeout,
		}
	)
	return context
