// Socket.IO realtime connection to Frappe's own socketio server - same
// origin, same `/socket.io` path Frappe's Desk app itself connects
// through (nginx/the bench dev proxy routes that path to the socketio
// process), so no separate host/port config is needed here.
//
// This only opens the connection and exposes it as `window.frappe.realtime`
// (the same global name Desk code uses, so any future gym_management
// realtime publish() call on the server - e.g. `frappe.publish_realtime`
// on a new check-in - can be picked up here without another wiring
// change). No events are subscribed yet; wire up `.on(...)` calls in the
// pages that need them as those features get built.
import { io } from 'socket.io-client';

let socket = null;

export function initSocket() {
  if (socket) return socket;
  socket = io(window.location.origin, {
    withCredentials: true,
    path: '/socket.io',
    reconnectionAttempts: Infinity,
  });
  if (!window.frappe) window.frappe = {};
  window.frappe.realtime = socket;
  return socket;
}

export function getSocket() {
  return socket;
}
