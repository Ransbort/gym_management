<template>
  <div class="flex h-full flex-col bg-slate-50 p-6">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
      <h1 class="text-xl font-bold text-slate-900">{{ tab === 'log' ? 'Attendance Log' : 'Front-Desk Check-In' }}</h1>
      <div class="flex items-center gap-1 rounded-lg bg-slate-200 p-1 text-xs font-semibold">
        <button
          type="button"
          class="rounded-md px-3 py-1.5 transition-colors"
          :class="tab === 'checkin' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'"
          @click="tab = 'checkin'"
        ><i class="bi bi-door-open"></i> Check In/Out</button>
        <button
          type="button"
          class="rounded-md px-3 py-1.5 transition-colors"
          :class="tab === 'log' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'"
          @click="switchToLog"
        ><i class="bi bi-clock-history"></i> Attendance Log</button>
      </div>
    </div>

    <template v-if="tab === 'checkin'">
      <div class="relative mb-4 max-w-sm">
        <i class="bi bi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"></i>
        <input
          v-model="query" type="text" placeholder="Search by name or mobile number..."
          class="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
          @input="onSearchInput"
        />
      </div>

      <p v-if="!ui.isOnline" class="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-700">
        <i class="bi bi-wifi-off"></i> Offline - check-in/out actions are queued and will sync automatically.
      </p>

      <div class="flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-white">
        <p v-if="loading" class="px-4 py-6 text-sm text-slate-500">Loading...</p>
        <div v-else-if="!members.length" class="px-4 py-6 text-center text-sm text-slate-500">
          <p>No members found.</p>
          <button
            type="button"
            class="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-[var(--gym-accent)] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[var(--gym-accent-hover)]"
            @click="openCreateMember()"
          >
            <i class="bi bi-person-plus"></i> Create New Member
          </button>
        </div>
        <ul v-else class="divide-y divide-slate-100">
          <li v-for="m in members" :key="m.name" class="flex items-center justify-between px-4 py-3">
            <div>
              <div class="text-sm font-medium text-slate-900">{{ m.member_name }}</div>
              <div class="text-xs text-slate-500">{{ m.phone || '-' }} - {{ m.membership_status }}</div>
            </div>
            <button
              v-if="m.checked_in"
              class="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
              :disabled="busy.has(m.name)" @click="checkOut(m)"
            >Check Out</button>
            <button
              v-else
              class="rounded-lg bg-[var(--gym-accent)] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[var(--gym-accent-hover)]"
              :disabled="busy.has(m.name)" @click="checkIn(m)"
            >Check In</button>
          </li>
        </ul>
      </div>
    </template>

    <template v-else>
      <div class="mb-3 flex flex-wrap items-end gap-2">
        <label class="block">
          <span class="mb-1 block text-xs font-semibold text-slate-600">From</span>
          <input
            v-model="logFrom" type="date"
            class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            @change="loadLog"
          />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-semibold text-slate-600">To</span>
          <input
            v-model="logTo" type="date"
            class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            @change="loadLog"
          />
        </label>
        <div class="relative min-w-[12rem] max-w-xs flex-1">
          <i class="bi bi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"></i>
          <input
            v-model="logQuery" type="text" placeholder="Search member..."
            class="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            @input="onLogSearchInput"
          />
        </div>
      </div>

      <div class="flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-white">
        <p v-if="logLoading" class="px-4 py-6 text-sm text-slate-500">Loading...</p>
        <p v-else-if="!logRows.length" class="px-4 py-6 text-sm text-slate-500">No check-ins found for this range.</p>
        <table v-else class="w-full text-left text-sm">
          <thead class="sticky top-0 border-b border-slate-200 bg-white text-slate-500">
            <tr>
              <th class="px-4 py-2 font-semibold">Member</th>
              <th class="px-4 py-2 font-semibold">Check-In</th>
              <th class="px-4 py-2 font-semibold">Check-Out</th>
              <th class="px-4 py-2 font-semibold">Duration</th>
              <th class="px-4 py-2 font-semibold">Checked In By</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in logRows" :key="r.name" class="border-b border-slate-100 text-slate-700">
              <td class="px-4 py-2">{{ r.member_name || r.member }}</td>
              <td class="px-4 py-2">{{ formatDateTime(r.check_in_time) }}</td>
              <td class="px-4 py-2">
                <span v-if="r.check_out_time">{{ formatDateTime(r.check_out_time) }}</span>
                <span v-else class="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-600">Still checked in</span>
              </td>
              <td class="px-4 py-2">{{ formatDuration(r.duration_minutes) }}</td>
              <td class="px-4 py-2 text-slate-500">{{ r.checked_in_by || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <CreateMemberModal
      v-if="showCreateMember"
      :prefill-name="isLikelyName(query) ? query : ''"
      @close="showCreateMember = false"
      @created="onMemberCreated"
    />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';
import { useUiStore } from '@/stores/ui';
import { cacheMembers, getCachedMembers, queueAction } from '@/offline/db';
import { flushPendingActions } from '@/offline/sync';
import CreateMemberModal from '@/components/CreateMemberModal.vue';

const ui = useUiStore();
const query = ref('');
const members = ref([]);
const loading = ref(true);
const busy = reactive(new Set());
const showCreateMember = ref(false);
let searchTimer = null;

// Attendance Log tab - a historical view alongside the live check-in/out
// screen above, so admin can see who came in and out (and for how long)
// rather than only who's on the floor right now (that's what Overview's own
// "checked in" list already covers).
const tab = ref('checkin');
const todayStr = new Date().toISOString().slice(0, 10);
const logFrom = ref(todayStr);
const logTo = ref(todayStr);
const logQuery = ref('');
const logRows = ref([]);
const logLoading = ref(false);
let logSearchTimer = null;

function formatDateTime(value) {
  if (!value) return '-';
  const d = new Date(String(value).replace(' ', 'T'));
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatDuration(minutes) {
  if (minutes === null || minutes === undefined || minutes === '') return '-';
  const total = Number(minutes);
  if (!Number.isFinite(total)) return '-';
  const h = Math.floor(total / 60);
  const m = total % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

async function loadLog() {
  logLoading.value = true;
  try {
    logRows.value = await call('gym_management.admin_api.list_attendance', {
      query: logQuery.value,
      date_from: logFrom.value,
      date_to: logTo.value,
    });
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load the attendance log.', 'error');
  } finally {
    logLoading.value = false;
  }
}

function onLogSearchInput() {
  clearTimeout(logSearchTimer);
  logSearchTimer = setTimeout(loadLog, 250);
}

function switchToLog() {
  tab.value = 'log';
  loadLog();
}

// Only offer to prefill the "name" field from the search box when it looks
// like a name rather than a partial phone number, since this same search
// box matches on either.
function isLikelyName(value) {
  return /[a-zA-Z]/.test(value || '');
}

async function load() {
  loading.value = true;
  if (!navigator.onLine) {
    members.value = await getCachedMembers();
    loading.value = false;
    return;
  }
  try {
    const result = await call('gym_management.admin_api.search_members', { query: query.value });
    members.value = result;
    cacheMembers(result);
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load members - showing last known list.', 'error');
    members.value = await getCachedMembers();
  } finally {
    loading.value = false;
  }
}

function onSearchInput() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(load, 250);
}

function openCreateMember() {
  showCreateMember.value = true;
}

function onMemberCreated(member) {
  showCreateMember.value = false;
  ui.showToast(`${member.member_name} created.`);
  query.value = member.member_name;
  load();
}

async function checkIn(member) {
  busy.add(member.name);
  member.checked_in = true;
  try {
    if (navigator.onLine) {
      await call('gym_management.admin_api.check_in', { member: member.name });
      ui.showToast(`${member.member_name} checked in.`);
    } else {
      await queueAction('check_in', member.name);
      ui.showToast(`${member.member_name} checked in (queued offline - will sync automatically).`);
    }
  } catch (err) {
    member.checked_in = false;
    ui.showToast(firstServerMessage(err) || 'Could not check this member in.', 'error');
  } finally {
    busy.delete(member.name);
  }
}

async function checkOut(member) {
  busy.add(member.name);
  member.checked_in = false;
  try {
    if (navigator.onLine) {
      await call('gym_management.admin_api.check_out', { member: member.name });
      ui.showToast(`${member.member_name} checked out.`);
    } else {
      await queueAction('check_out', member.name);
      ui.showToast(`${member.member_name} checked out (queued offline - will sync automatically).`);
    }
  } catch (err) {
    member.checked_in = true;
    ui.showToast(firstServerMessage(err) || 'Could not check this member out.', 'error');
  } finally {
    busy.delete(member.name);
  }
}

function handleOnline() {
  ui.setOnline(true);
  flushPendingActions().then((result) => {
    if (result.flushed) {
      ui.showToast(`Synced ${result.flushed} queued check-in/out action(s).`);
      load();
    }
  });
}
function handleOffline() {
  ui.setOnline(false);
}

onMounted(() => {
  load();
  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);
  if (navigator.onLine) flushPendingActions();
});
onUnmounted(() => {
  window.removeEventListener('online', handleOnline);
  window.removeEventListener('offline', handleOffline);
});
watch(() => ui.refreshKey, () => {
  load();
  if (tab.value === 'log') loadLog();
});
</script>
