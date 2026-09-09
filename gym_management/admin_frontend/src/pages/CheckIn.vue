<template>
  <div class="flex h-full flex-col bg-slate-50 p-6">
    <h1 class="mb-4 text-xl font-bold text-slate-900">Front-Desk Check-In</h1>

    <div class="relative mb-4">
      <i class="bi bi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"></i>
      <input
        v-model="query" type="text" placeholder="Search by name or mobile number..."
        class="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
        @input="onSearchInput"
      />
    </div>

    <p v-if="flash" :class="['mb-3 rounded-lg px-3 py-2 text-sm', flashError ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700']">
      {{ flash }}
    </p>
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
const flash = ref('');
const flashError = ref(false);
const busy = reactive(new Set());
const showCreateMember = ref(false);
let searchTimer = null;

// Only offer to prefill the "name" field from the search box when it looks
// like a name rather than a partial phone number, since this same search
// box matches on either.
function isLikelyName(value) {
  return /[a-zA-Z]/.test(value || '');
}

function showFlash(message, isError) {
  flash.value = message;
  flashError.value = !!isError;
  setTimeout(() => {
    if (flash.value === message) flash.value = '';
  }, 4000);
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
    showFlash(firstServerMessage(err) || 'Could not load members - showing last known list.', true);
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
  showFlash(`${member.member_name} created.`, false);
  query.value = member.member_name;
  load();
}

async function checkIn(member) {
  busy.add(member.name);
  member.checked_in = true;
  try {
    if (navigator.onLine) {
      await call('gym_management.admin_api.check_in', { member: member.name });
      showFlash(`${member.member_name} checked in.`, false);
    } else {
      await queueAction('check_in', member.name);
      showFlash(`${member.member_name} checked in (queued offline - will sync automatically).`, false);
    }
  } catch (err) {
    member.checked_in = false;
    showFlash(firstServerMessage(err) || 'Could not check this member in.', true);
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
      showFlash(`${member.member_name} checked out.`, false);
    } else {
      await queueAction('check_out', member.name);
      showFlash(`${member.member_name} checked out (queued offline - will sync automatically).`, false);
    }
  } catch (err) {
    member.checked_in = true;
    showFlash(firstServerMessage(err) || 'Could not check this member out.', true);
  } finally {
    busy.delete(member.name);
  }
}

function handleOnline() {
  ui.setOnline(true);
  flushPendingActions().then((result) => {
    if (result.flushed) {
      showFlash(`Synced ${result.flushed} queued check-in/out action(s).`, false);
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
watch(() => ui.refreshKey, load);
</script>
