// Flushes the pendingActions queue (see ./db.js) back to the server once
// the connection is back - called from App.vue on mount and on the
// browser's `online` event.
import { call } from '@/api/frappe';
import { getPendingActions, removePendingAction } from './db';

let flushing = false;

export async function flushPendingActions(onProgress) {
  if (flushing || !navigator.onLine) return { flushed: 0, failed: 0 };
  flushing = true;
  let flushed = 0;
  let failed = 0;
  try {
    const pending = await getPendingActions();
    for (const action of pending) {
      try {
        if (action.type === 'check_in') {
          await call('gym_management.admin_api.check_in', { member: action.member });
        } else if (action.type === 'check_out') {
          await call('gym_management.admin_api.check_out', { member: action.member });
        }
        await removePendingAction(action.id);
        flushed += 1;
        if (onProgress) onProgress({ flushed, total: pending.length });
      } catch (err) {
        // Leave it queued - most likely still offline, or the action is
        // now stale (e.g. already checked out by someone else). Either
        // way, don't block the rest of the queue on one failure.
        failed += 1;
      }
    }
  } finally {
    flushing = false;
  }
  return { flushed, failed };
}
