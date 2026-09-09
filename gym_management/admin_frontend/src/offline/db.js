// IndexedDB (via Dexie) offline cache for the front-desk Check-In screen.
//
// Scope, deliberately kept small: this is the extension point for
// offline support, not a full offline-first rewrite of the dashboard -
// only the two things front-desk staff actually need mid-outage are
// covered:
//   - memberCache: the last known member list/search results, so the
//     Check-In screen still shows something useful with no network.
//   - pendingActions: a queue of check-in/check-out taps made while
//     offline, flushed to the server by ./sync.js as soon as the
//     connection comes back.
//
// Add more tables here as more of the dashboard grows offline support
// (e.g. a queued-payments table for Memberships & Payments).
import Dexie from 'dexie';

export const db = new Dexie('gym_admin_offline');

db.version(1).stores({
  memberCache: 'name, member_name, phone, membership_status, checked_in, cached_at',
  pendingActions: '++id, type, member, created_at',
});

export async function cacheMembers(members) {
  const now = Date.now();
  await db.memberCache.bulkPut(members.map((m) => ({ ...m, cached_at: now })));
}

export async function getCachedMembers() {
  return db.memberCache.toArray();
}

export async function queueAction(type, member) {
  return db.pendingActions.add({ type, member, created_at: Date.now() });
}

export async function getPendingActions() {
  return db.pendingActions.toArray();
}

export async function removePendingAction(id) {
  return db.pendingActions.delete(id);
}
