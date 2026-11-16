<template>
  <div class="flex h-full flex-col overflow-hidden bg-slate-50 p-6">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
      <div>
        <h1 class="text-xl font-bold text-slate-900">Doctor Requests</h1>
        <p class="text-xs text-slate-500">Memberships and PT packages prescribed from a Patient Encounter. Accepting one bills the patient at the hospital Cashier.</p>
      </div>
      <div class="flex items-center gap-2">
        <input
          v-model="query" type="search" placeholder="Search patient..."
          class="w-56 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
          @keyup.enter="load"
        />
        <button class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50" @click="load">
          <i class="bi bi-arrow-clockwise"></i> Refresh
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-white">
      <p v-if="loading" class="px-4 py-6 text-sm text-slate-500">Loading...</p>
      <div v-else-if="!requests.length" class="flex flex-col items-center gap-2 px-4 py-16 text-slate-500">
        <i class="bi bi-clipboard2-check text-3xl"></i>
        <p class="text-sm">No pending requests from doctors.</p>
      </div>
      <table v-else class="w-full text-left text-sm">
        <thead class="sticky top-0 border-b border-slate-200 bg-white text-slate-500">
          <tr>
            <th class="px-4 py-2 font-semibold">Patient</th>
            <th class="px-4 py-2 font-semibold">Request</th>
            <th class="px-4 py-2 font-semibold">Priority</th>
            <th class="px-4 py-2 font-semibold">Doctor</th>
            <th class="px-4 py-2 font-semibold">Notes</th>
            <th class="px-4 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in requests" :key="r.request_id" class="border-b border-slate-100 align-top text-slate-700 hover:bg-slate-50">
            <td class="px-4 py-3">
              <div class="font-semibold text-slate-900">{{ r.patient_name }}</div>
              <div class="text-xs text-slate-500">{{ r.patient }}</div>
              <span v-if="r.gym_member" class="mt-1 inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">Existing member</span>
            </td>
            <td class="px-4 py-3">
              <template v-if="r.request_type === 'Membership'">
                <div class="font-semibold">{{ r.plan_name || r.membership_plan }}</div>
                <div class="text-xs text-slate-500">Membership · {{ r.duration_months }} mo · {{ money(r.price) }}</div>
              </template>
              <template v-else>
                <div class="font-semibold">{{ r.package_name || r.pt_package }}</div>
                <div class="text-xs text-slate-500">PT Package · {{ r.no_of_sessions }} sessions · {{ money(r.price) }}</div>
              </template>
            </td>
            <td class="px-4 py-3">
              <span v-if="r.priority" class="rounded-full px-2 py-0.5 text-xs font-semibold" :class="priorityClass(r.priority)">{{ r.priority }}</span>
            </td>
            <td class="px-4 py-3">
              <div>{{ r.practitioner_name }}</div>
              <div class="text-xs text-slate-500">{{ r.encounter }} · {{ r.encounter_date_label }}</div>
            </td>
            <td class="max-w-xs px-4 py-3 text-xs text-slate-600">{{ r.notes }}</td>
            <td class="px-4 py-3 text-right">
              <button class="rounded-lg bg-[var(--gym-accent)] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[var(--gym-accent-hover)]" @click="openAccept(r)">
                <i class="bi bi-check-lg"></i> Accept
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Accept dialog -->
    <Teleport to="body">
      <div v-if="active" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4" @mousedown.self="closeAccept">
        <div class="flex max-h-[85vh] w-full max-w-lg flex-col rounded-2xl bg-white p-6 shadow-xl">
          <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
            <h2 class="text-base font-semibold text-slate-900">Accept request - {{ active.patient_name }}</h2>
            <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 hover:bg-slate-200 hover:text-slate-600" @click="closeAccept">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>

          <form id="accept-request-form" class="grid flex-1 auto-rows-min grid-cols-1 gap-3 overflow-y-auto pr-1 sm:grid-cols-2" @submit.prevent="submit">
            <div class="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700 sm:col-span-2">
              <strong>{{ active.request_type === 'Membership' ? (active.plan_name || active.membership_plan) : (active.package_name || active.pt_package) }}</strong>
              · {{ money(active.price) }}
              <div class="mt-1 text-xs text-slate-500">
                {{ active.gym_member ? 'Will be added to their existing gym member record.' : 'A new gym member will be created from the patient record.' }}
                An invoice will be sent to the hospital Cashier; the {{ active.request_type === 'Membership' ? 'membership activates' : 'purchase is marked paid' }} once it's paid there.
              </div>
            </div>

            <label v-if="!active.gym_member" class="flex flex-col gap-1 text-sm font-semibold text-slate-700 sm:col-span-2">
              <span>Phone<span class="text-red-500">*</span></span>
              <input v-model="form.phone" type="tel" required :class="inputClass" />
            </label>

            <template v-if="active.request_type === 'Membership'">
              <label class="flex flex-col gap-1 text-sm font-semibold text-slate-700">
                <span>Membership Plan Type<span class="text-red-500">*</span></span>
                <select v-model="form.membership_plan_type" required :class="inputClass">
                  <option value="" disabled>Select a type...</option>
                  <option v-for="t in options.membership_plan_types" :key="t.name" :value="t.name">{{ t.plan_type_name }}</option>
                </select>
              </label>
              <label class="flex flex-col gap-1 text-sm font-semibold text-slate-700">
                <span>Trainer<span class="text-red-500">*</span></span>
                <select v-model="form.trainer" required :class="inputClass">
                  <option value="" disabled>Select a trainer...</option>
                  <option v-for="t in options.trainers" :key="t.name" :value="t.name">{{ t.trainer_name }}</option>
                </select>
              </label>
              <label class="flex flex-col gap-1 text-sm font-semibold text-slate-700 sm:col-span-2">
                <span>Time Slot<span class="text-red-500">*</span></span>
                <div class="flex items-center gap-2">
                  <input v-model="form.time_slot_start" type="time" required :class="inputClass" />
                  <span class="shrink-0 text-xs text-slate-400">to</span>
                  <input v-model="form.time_slot_end" type="time" required :class="inputClass" />
                </div>
              </label>
              <label class="flex flex-col gap-1 text-sm font-semibold text-slate-700">
                <span>Activation Date</span>
                <input v-model="form.start_date" type="date" :class="inputClass" />
              </label>
              <label class="flex flex-col gap-1 text-sm font-semibold text-slate-700">
                <span>Valid Number of Days</span>
                <input v-model="form.valid_number_of_days" type="number" min="1" :class="inputClass" />
              </label>
            </template>

            <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-2">{{ error }}</p>
          </form>

          <div class="mt-4 flex shrink-0 items-center gap-2 border-t border-slate-100 pt-4">
            <button type="submit" form="accept-request-form" :disabled="saving"
              class="rounded-lg bg-[var(--gym-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50">
              {{ saving ? 'Accepting...' : 'Accept & Send to Cashier' }}
            </button>
            <button type="button" :disabled="saving" class="rounded-lg px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-200" @click="closeAccept">Cancel</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';
import { useUiStore } from '@/stores/ui';
import { initSocket } from '@/socket';

const ui = useUiStore();
const inputClass = 'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]';

const requests = ref([]);
const loading = ref(false);
const query = ref('');
const options = ref({ membership_plan_types: [], trainers: [], default_valid_number_of_days: '' });
const active = ref(null);
const saving = ref(false);
const error = ref('');
const today = () => new Date().toISOString().slice(0, 10);
const form = reactive({});

function money(v) {
  return Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function priorityClass(p) {
  return { High: 'bg-red-50 text-red-700', Medium: 'bg-amber-50 text-amber-700', Low: 'bg-sky-50 text-sky-700' }[p] || '';
}

async function load() {
  loading.value = true;
  try {
    requests.value = (await call('gym_management.healthcare_requests.get_gym_requests', { query: query.value })) || [];
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load requests.', 'error');
  } finally {
    loading.value = false;
  }
}

async function loadOptions() {
  try {
    options.value = await call('gym_management.admin_api.get_membership_form_options');
  } catch (err) {
    // Only needed for membership requests; the dialog shows its own error on submit.
  }
}

function openAccept(r) {
  active.value = r;
  error.value = '';
  Object.assign(form, {
    phone: r.phone || '',
    membership_plan_type: '', trainer: '', time_slot_start: '', time_slot_end: '',
    start_date: today(),
    valid_number_of_days: options.value.default_valid_number_of_days || '',
  });
}
function closeAccept() {
  if (!saving.value) active.value = null;
}

async function submit() {
  saving.value = true;
  error.value = '';
  try {
    const res = await call('gym_management.healthcare_requests.accept_gym_request', {
      request_id: active.value.request_id,
      ...form,
    });
    ui.showToast(`Accepted for ${res.member_name}. Invoice ${res.invoice} sent to the Cashier.`);
    active.value = null;
    load();
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not accept this request.';
  } finally {
    saving.value = false;
  }
}

function onRealtime(data) {
  if (data && data.message) ui.showToast(data.message, 'warning');
  load();
}

watch(() => ui.refreshKey, load);

onMounted(() => {
  load();
  loadOptions();
  initSocket().on('gym_request_update', onRealtime);
});
onUnmounted(() => {
  initSocket().off('gym_request_update', onRealtime);
});
</script>
