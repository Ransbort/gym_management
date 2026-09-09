<template>
  <div class="h-full overflow-y-auto bg-slate-50 p-6">
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-xl font-bold text-slate-900">Overview</h1>
      <div class="flex items-center gap-2">
        <button
          class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          @click="showCreateMember = true"
        >
          <i class="bi bi-person-plus"></i> New Member
        </button>
        <button
          class="rounded-lg bg-[var(--gym-accent)] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[var(--gym-accent-hover)]"
          @click="showCreateMembership = true"
        >
          <i class="bi bi-plus-lg"></i> New Membership
        </button>
      </div>
    </div>

    <p v-if="flash" :class="['mb-4 rounded-lg px-3 py-2 text-sm', flashError ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700']">
      {{ flash }}
    </p>

    <p v-if="loading && !data" class="text-slate-500">Loading...</p>

    <template v-else-if="data">
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Active Members" :value="data.stats.active_members" icon="bi-people" />
        <StatCard label="Total Members" :value="data.stats.total_members" icon="bi-person-lines-fill" />
        <StatCard label="Checked In Now" :value="data.stats.checked_in_now" icon="bi-door-open" accent />
        <StatCard label="Today's Check-Ins" :value="data.stats.todays_checkins" icon="bi-clock-history" />
        <StatCard label="Expiring (7 days)" :value="data.stats.expiring_soon" icon="bi-exclamation-triangle" warn />
        <StatCard label="Today's Revenue" :value="formatCurrency(data.stats.todays_revenue)" icon="bi-cash-coin" />
      </div>

      <div class="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section class="rounded-xl border border-slate-200 bg-white">
          <h2 class="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">Currently Checked In</h2>
          <p v-if="!data.checked_in.length" class="px-4 py-6 text-sm text-slate-500">Nobody is checked in right now.</p>
          <ul v-else class="divide-y divide-slate-100">
            <li v-for="row in data.checked_in" :key="row.name" class="flex items-center justify-between px-4 py-2.5 text-sm">
              <span class="text-slate-700">{{ row.member_name }}</span>
              <span class="text-slate-400">{{ formatTime(row.check_in_time) }}</span>
            </li>
          </ul>
        </section>

        <section class="rounded-xl border border-slate-200 bg-white">
          <h2 class="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">Expiring in the Next 7 Days</h2>
          <p v-if="!data.expiring_memberships.length" class="px-4 py-6 text-sm text-slate-500">Nothing expiring soon.</p>
          <ul v-else class="divide-y divide-slate-100">
            <li v-for="row in data.expiring_memberships" :key="row.name" class="flex items-center justify-between px-4 py-2.5 text-sm">
              <span class="text-slate-700">{{ row.member_name }}</span>
              <span class="text-amber-600">{{ row.end_date }}</span>
            </li>
          </ul>
        </section>
      </div>
    </template>

    <CreateMemberModal
      v-if="showCreateMember"
      @close="showCreateMember = false"
      @created="onMemberCreated"
    />
    <NewMembershipModal
      v-if="showCreateMembership"
      @close="showCreateMembership = false"
      @created="onMembershipCreated"
    />
  </div>
</template>

<script setup>
import { h, onMounted, ref, watch } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';
import { useUiStore } from '@/stores/ui';
import CreateMemberModal from '@/components/CreateMemberModal.vue';
import NewMembershipModal from '@/components/NewMembershipModal.vue';

const ui = useUiStore();
const data = ref(null);
const loading = ref(true);
const showCreateMember = ref(false);
const showCreateMembership = ref(false);
const flash = ref('');
const flashError = ref(false);

function showFlash(message, isError) {
  flash.value = message;
  flashError.value = !!isError;
  setTimeout(() => { if (flash.value === message) flash.value = ''; }, 4000);
}

function onMemberCreated(member) {
  showCreateMember.value = false;
  showFlash(`${member.member_name} created.`, false);
  load();
}

function onMembershipCreated(membership) {
  showCreateMembership.value = false;
  showFlash('Membership created.', false);
  load();
}

async function load() {
  loading.value = true;
  try {
    data.value = await call('gym_management.admin_api.get_overview');
  } catch (err) {
    console.error(firstServerMessage(err) || err);
  } finally {
    loading.value = false;
  }
}

function formatTime(value) {
  if (!value) return '-';
  const d = new Date(value.replace(' ', 'T'));
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatCurrency(value) {
  const n = Number(value) || 0;
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

onMounted(load);
watch(() => ui.refreshKey, load);

const StatCard = {
  props: { label: String, value: [String, Number], icon: String, accent: Boolean, warn: Boolean },
  render() {
    return h('div', { class: 'rounded-xl border border-slate-200 bg-white p-4' }, [
      h('div', {
        class: [
          'mb-2 flex h-8 w-8 items-center justify-center rounded-lg text-sm',
          this.warn ? 'bg-amber-50 text-amber-600' : this.accent ? 'bg-[var(--gym-accent-tint)] text-[var(--gym-accent)]' : 'bg-slate-100 text-slate-500',
        ],
      }, [h('i', { class: ['bi', this.icon] })]),
      h('div', { class: 'text-2xl font-bold text-slate-900' }, String(this.value)),
      h('div', { class: 'text-xs text-slate-500' }, this.label),
    ]);
  },
};
</script>
