// Thin wrapper around the global `frappe` object every page on this site
// already gets from templates/web.html - frappe.call() already handles
// CSRF tokens, session cookies, and the plumbing for whitelisted method
// calls, so the SPA needs no HTTP client or auth-token scheme of its own.
// Same shape as sports_complex/frontend/src/api/frappe.js.

export function call(method, args = {}) {
  // Promise.resolve() assimilates frappe.call()'s jQuery-style Deferred
  // into a real native Promise before anything chains off of it - jQuery's
  // Promise/Deferred implements .then()/.catch() but never .finally().
  return Promise.resolve(window.frappe.call(method, args)).then((r) => r && r.message);
}

export function hasServerMessage(err) {
  if (!err) return false;
  if (err._server_messages) return true;
  if (err.responseJSON && err.responseJSON._server_messages) return true;
  return false;
}

export function firstServerMessage(err) {
  try {
    const raw = (err && err._server_messages) || (err && err.responseJSON && err.responseJSON._server_messages);
    if (!raw) return '';
    const messages = JSON.parse(raw);
    const first = JSON.parse(messages[0]);
    return first.message || '';
  } catch (e) {
    return '';
  }
}
