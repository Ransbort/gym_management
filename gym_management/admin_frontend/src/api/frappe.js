// Thin wrapper around the global `frappe` object every page on this site
// already gets from templates/web.html - frappe.call() already handles
// CSRF tokens, session cookies, and the plumbing for whitelisted method
// calls, so the SPA needs no HTTP client or auth-token scheme of its own.
// Same shape as ../../frontend/src/api/frappe.js (the Gym Portal SPA).

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

// frappe.call() only ever does JSON RPC - Frappe's own file upload endpoint
// (/api/method/upload_file) takes multipart/form-data instead, so this is a
// plain fetch() rather than a call() wrapper. Used by CreateMemberModal.vue's
// Photo field: upload first to get a file_url, then pass that URL along with
// the rest of the form to create_member() - the same two-step every Frappe
// Attach control does under the hood.
export function uploadFile(file, { isPrivate = false } = {}) {
  const formData = new FormData();
  formData.append('file', file, file.name);
  formData.append('is_private', isPrivate ? 1 : 0);
  return fetch('/api/method/upload_file', {
    method: 'POST',
    headers: { 'X-Frappe-CSRF-Token': window.frappe.csrf_token },
    body: formData,
  }).then(async (res) => {
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw data;
    return data.message;
  });
}
