# Gym Admin (admin_frontend)

Fullscreen, PWA-installable staff dashboard for gym_management, served at
`/gym-admin`. Modelled on POSNext's `/pos` app (`apps/POSNext/POS`):
Vue 3 + Vite + Vue Router + Pinia, `frappe-ui` components, an IndexedDB
(Dexie) offline queue, a Socket.IO realtime connection, and a
`vite-plugin-pwa` service worker + install manifest.

This is a **separate** SPA from `../frontend` (the member/trainer Gym
Portal at `/gym-portal`) - different audience (Desk-capable staff vs.
website members/trainers), different route, different build output
(`public/admin` vs `public/portal`).

## Architecture

- `vite.config.js` builds straight into `../public/admin`
  (`/assets/gym_management/admin/...`) with fixed, non-hashed asset
  filenames (`assets/main.js` / `assets/main.css`), same reasoning as
  `../frontend/vite.config.js`.
- `../www/gym-admin/index.py` + `index.html` is the served shell: a
  hand-authored Jinja template (not Vite's own built `index.html`) that
  extends `templates/web.html`, suppresses the site's own navbar/footer,
  and injects `window.adminBoot` (current user + staff-role flag) computed
  server-side on every request. `hooks.py`'s `website_route_rules` sends
  every `/gym-admin/<path>` request to this same shell so a hard reload on
  a nested route (e.g. `/gym-admin/memberships`) doesn't 404 before Vue
  Router mounts.
- `src/router/index.js` - `createWebHistory('/gym-admin')`, matching that
  catch-all. Routes: `/` (Overview), `/checkin` (Front-Desk Check-In),
  `/memberships` (Memberships & Payments), `/login`.
- `src/api/frappe.js` - same `window.frappe.call()` wrapper as the Gym
  Portal SPA. No separate HTTP client or token scheme; CSRF/session
  cookies are handled by the global `frappe` object every page already
  gets from `templates/web.html`.
- `src/stores/auth.js` - reads `window.adminBoot`; `login()`/`logout()` do
  a full page navigation (not in-place state patching) so the next
  server render recomputes boot data and CSRF token for the new session.
- `src/offline/db.js` + `sync.js` - a small Dexie-backed offline queue for
  the Check-In screen: cached member list + queued check-in/out actions,
  flushed automatically on reconnect. Extend this (more tables, more
  queued action types) as more of the dashboard grows offline support.
- `src/socket.js` - opens a Socket.IO connection to Frappe's own
  `/socket.io` endpoint and exposes it as `window.frappe.realtime`. No
  events are subscribed yet - wire up `.on(...)` calls in pages that need
  live updates as those features get built.
- `vite-plugin-pwa` (see `vite.config.js`) generates the service worker
  and `manifest.webmanifest` into the build output; `src/main.js`
  registers it manually via `import('virtual:pwa-register')` (rather than
  the plugin's own HTML injection) for the same reason the shell HTML is
  hand-authored: `injectRegister: false`.

## Theming

The accent color throughout this app (buttons, active nav item, links,
focus rings) is configurable per-site via `Gym Settings.theme_color` (a
`Color` field, "Gym Details" section) rather than hardcoded - staff-facing
branding, alongside `gym_name`/`logo`, already sourced the same way (see
`../www/gym-admin/index.py`'s `get_context()`).

Because that color is runtime data (fetched from the database) rather
than something known at build time, it can't live in `tailwind.config.js`
the way a static palette would. Instead `src/theme.js`'s `applyTheme()`
derives a small set of CSS custom properties (`--gym-accent`,
`--gym-accent-hover`, `--gym-accent-tint`, `--gym-accent-ring`) from the
one stored hex value and sets them on `<html>` - called once in
`src/main.js`, straight off `window.adminBoot.theme_color`, before the
app even mounts, so there's no flash of the default color. Components
then reference these via Tailwind arbitrary-value classes, e.g.
`bg-[var(--gym-accent)]` / `hover:bg-[var(--gym-accent-hover)]`, instead
of a fixed `indigo-600`/`indigo-700`.

Not covered: the PWA install manifest's own `theme_color` (browser/OS
chrome tinting for an installed PWA) is still fixed at build time in
`vite.config.js`, since `manifest.webmanifest` is a static generated
file - making that dynamic too would mean serving it from a whitelisted
backend route instead.

## Backend

`../admin_api.py` - whitelisted methods behind `_check_staff()` (System
Manager / Gym Manager / Gym Staff). Unlike `../portal.py` (website users
with no DocType permissions, every action does its own ownership check),
every caller here already holds real DocType-level permissions from
`generate.py`'s `manager_full()`/`staff_rw()`, so most reads/writes go
through normally.

Payments are tracked as discrete `Gym Membership Payment` records (not a
single mutable field) - each one applies itself onto its parent `Gym
Membership.paid_amount` via `after_insert()`, giving a real, queryable
payment history per membership and an honest "today's revenue" figure on
the Overview page.

## Building

```sh
cd admin_frontend
npm install
npm run build
```

No compatible pre-built `node_modules` exists elsewhere in this repo for
this dependency set (unlike `../frontend`, which could borrow
`sports_complex/frontend/node_modules`) - `frappe-ui`, `dexie`,
`vite-plugin-pwa`, `workbox-*` and `socket.io-client` are new to this app,
so `npm install` needs real registry access.

If you're building this over a mounted/network filesystem (e.g. a
Windows folder bridged into a Linux VM), don't run `npm install`
straight in that mounted `admin_frontend/` - `node_modules` is tens of
thousands of small files, and on a slow mount that makes `npm install`,
`rm -rf node_modules`, and even a plain `ls`/`du` take minutes each or
hang outright. Instead: `rsync -a --exclude node_modules` (or `cp -r`)
this directory to a fast local disk, `npm install && npm run build`
there, then copy just the small build output
(`../public/admin/`, well under 1 MB) back onto the mounted filesystem.
`frappe-ui` alone pulls in ~250 packages (it bundles a rich-text editor,
a charting library, etc., mostly unused here and tree-shaken out) and
the full dependency set is ~600 packages - trivial for local disk,
painful over a slow mount.

## Extending

The user's own framing for this dashboard was "we will be building more
features" - the pieces above are meant as the extension points:

- New pages: add a route in `src/router/index.js`, a nav entry in
  `src/components/Sidebar.vue`, and whitelisted methods in
  `../admin_api.py`.
- New offline-capable actions: add a Dexie table in `src/offline/db.js`
  and a case in `src/offline/sync.js`'s `flushPendingActions()`.
- New realtime events: `frappe.publish_realtime(...)` on the server,
  `window.frappe.realtime.on(...)` (see `src/socket.js`) on the client.
