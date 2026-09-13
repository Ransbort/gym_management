<template>
  <div class="flex h-full flex-col gap-4 overflow-hidden bg-slate-50 p-6 lg:flex-row">
    <!-- List + filters -->
    <section class="flex min-w-0 flex-1 flex-col">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-xl font-bold text-slate-900">Personal Training</h1>
        <button
          class="rounded-lg bg-[var(--gym-accent)] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[var(--gym-accent-hover)]"
          @click="showCreate = true"
        >
          <i class="bi bi-plus-lg"></i> New Purchase
        </button>
      </div>

      <NewPtPurchaseModal
        v-if="showCreate"
        @close="showCreate = false"
        @created="onPurchaseCreated"
      />

      <div class="mb-3 flex gap-2">
        <select v-model="listPackage" class="w-56 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" @change="loadList">
          <option value="">All packages</option>
          <option v-for="p in options.pt_packages" :key="p.name" :value="p.name">{{ p.package_name }}</option>
        </select>
        <select v-model="listStatus" class="w-40 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" @change="loadList">
          <option value="">All statuses</option>
          <option v-for="s in ['Active', 'Expired', 'Completed']" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div class="flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-white">
        <p v-if="listLoading" class="px-4 py-6 text-sm text-slate-500">Loading...</p>
        <p v-else-if="!purchases.length" class="px-4 py-6 text-sm text-slate-500">No PT purchases found.</p>
        <table v-else class="w-full text-left text-sm">
          <thead class="sticky top-0 border-b border-slate-200 bg-white text-slate-500">
            <tr>
              <th class="px-4 py-2 font-semibold">Member</th>
              <th class="px-4 py-2 font-semibold">Package</th>
              <th class="px-4 py-2 font-semibold">Sessions</th>
              <th class="px-4 py-2 font-semibold">Status</th>
              <th class="px-4 py-2 font-semibold">Payment</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in purchases" :key="p.name"
              class="cursor-pointer border-b border-slate-100 border-l-4 border-l-transparent text-slate-700 hover:bg-slate-50"
              :class="{ '!border-l-[var(--gym-accent)] !bg-[var(--gym-accent-tint)]': selected && selected.purchase.name === p.name }"
              @click="selectPurchase(p.name)">
              <td class="px-4 py-2">{{ p.member_name || p.member }}</td>
              <td class="px-4 py-2">{{ p.pt_package }}</td>
              <td class="px-4 py-2">{{ p.sessions_used }}/{{ p.sessions_total }} used</td>
              <td class="px-4 py-2">
                <span
                  class="rounded-full px-2 py-0.5 text-xs font-semibold"
                  :class="p.status === 'Active' ? 'bg-emerald-50 text-emerald-600' : p.status === 'Expired' ? 'bg-red-50 text-red-600' : 'bg-slate-100 text-slate-500'"
                >{{ p.status }}</span>
              </td>
              <td class="px-4 py-2" :class="p.payment_status === 'Paid' ? 'text-emerald-600' : 'text-amber-600'">{{ p.payment_status }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Detail / log session -->
    <section class="flex w-full flex-col lg:w-96 lg:shrink-0">
      <div v-if="!selected" class="flex h-full items-center justify-center rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
        Select a purchase to view details and log sessions.
      </div>
      <div v-else class="flex h-full flex-col overflow-y-auto rounded-xl border border-slate-200 bg-white p-4">
        <h2 class="text-sm font-semibold text-slate-900">{{ selected.purchase.member_name || selected.purchase.member }}</h2>
        <p class="text-xs text-slate-500">{{ selected.purchase.name }} - {{ selected.purchase.pt_package }}</p>

        <dl class="mt-3 grid grid-cols-2 gap-2 text-xs">
          <dt class="text-slate-500">Purchased</dt><dd class="text-right text-slate-700">{{ selected.purchase.purchase_date }}</dd>
          <dt class="text-slate-500">Expires</dt><dd class="text-right text-slate-700">{{ selected.purchase.expiry_date }}</dd>
          <dt class="text-slate-500">Sessions</dt>
          <dd class="text-right text-slate-700">{{ selected.purchase.sessions_used }}/{{ selected.purchase.sessions_total }} used ({{ selected.purchase.sessions_remaining }} left)</dd>
          <dt class="text-slate-500">Status</dt><dd class="text-right text-slate-700">{{ selected.purchase.status }}</dd>
          <dt class="text-slate-500">Amount</dt><dd class="text-right text-slate-700">{{ selected.purchase.amount }}</dd>
          <dt class="text-slate-500">Paid</dt><dd class="text-right text-slate-700">{{ selected.purchase.paid_amount }}</dd>
          <dt class="text-slate-500">Outstanding</dt>
          <dd class="text-right font-semibold" :class="selected.purchase.outstanding_amount > 0 ? 'text-amber-600' : 'text-emerald-600'">
            {{ selected.purchase.outstanding_amount }}<span v-if="selected.purchase.outstanding_amount < 0" class="ml-1 font-normal text-slate-400">(credit)</span>
          </dd>
          <dt class="text-slate-500">Payment</dt><dd class="text-right text-slate-700">{{ selected.purchase.payment_status }}</dd>
        </dl>

        <div v-if="selected.purchase.outstanding_amount > 0 && options.enable_paystack_payments" class="mt-3 border-t border-slate-200 pt-3">
          <button
            type="button"
            :disabled="sendingLink"
            class="w-full rounded-lg border border-[var(--gym-accent)] px-3 py-2 text-xs font-semibold text-[var(--gym-accent)] hover:bg-[var(--gym-accent-tint)] disabled:opacity-60"
            @click="sendPaymentLink"
          >
            <i class="bi bi-link-45deg"></i> {{ sendingLink ? 'Generating link...' : 'Send Paystack Payment Link' }}
          </button>
          <div v-if="paymentLink" class="mt-2 flex items-center gap-1.5 rounded-lg bg-slate-50 px-2 py-1.5 text-xs">
            <span class="flex-1 truncate text-slate-600">{{ paymentLink }}</span>
            <button
              type="button"
              class="shrink-0 rounded px-1.5 py-1 font-semibold text-[var(--gym-accent)] hover:bg-slate-200"
              title="Copy link"
              @click="copyPaymentLink"
            >
              <i class="bi bi-clipboard"></i>
            </button>
          </div>
        </div>

        <form v-if="selected.purchase.outstanding_amount !== 0" class="mt-4 flex flex-col gap-2 border-t border-slate-200 pt-4" @submit.prevent="submitPayment">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-semibold text-slate-600">{{ paymentForm.payment_type === 'Refund' ? 'Pay Back Member' : 'Collect Payment' }}</h3>
            <button
              v-if="selected.purchase.outstanding_amount < 0 || paymentForm.payment_type === 'Refund'"
              type="button"
              class="text-xs font-semibold text-[var(--gym-accent)] hover:underline"
              @click="paymentForm.payment_type = paymentForm.payment_type === 'Refund' ? 'Payment' : 'Refund'"
            >
              {{ paymentForm.payment_type === 'Refund' ? 'Collect payment instead' : 'Pay back credit instead' }}
            </button>
          </div>
          <input v-model="paymentForm.amount" type="number" step="0.01" min="0.01" placeholder="Amount" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required />
          <select v-model="paymentForm.mode_of_payment" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required>
            <option value="" disabled>Mode of payment...</option>
            <option v-for="mop in options.mode_of_payments" :key="mop.name" :value="mop.name">{{ mop.name }}</option>
          </select>
          <input v-model="paymentForm.reference_no" type="text" placeholder="Reference / receipt no. (optional)" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          <button type="submit" :disabled="collecting"
            class="rounded-lg px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
            :class="paymentForm.payment_type === 'Refund' ? 'bg-amber-500 hover:bg-amber-600' : 'bg-[var(--gym-accent)] hover:bg-[var(--gym-accent-hover)]'">
            {{ collecting ? 'Recording...' : (paymentForm.payment_type === 'Refund' ? 'Record Refund' : 'Record Payment') }}
          </button>
        </form>
        <p v-else class="mt-4 border-t border-slate-200 pt-4 text-xs text-slate-500">Paid in full - nothing to collect.</p>

        <div class="mt-4 border-t border-slate-200 pt-3">
          <h3 class="mb-2 text-xs font-semibold text-slate-600">Payment History</h3>
          <p v-if="!selected.payments.length" class="text-xs text-slate-500">No payments recorded yet.</p>
          <ul v-else class="space-y-1.5 text-xs">
            <li v-for="p in selected.payments" :key="p.name" class="flex items-center justify-between text-slate-600">
              <span class="flex items-center gap-1">
                {{ p.payment_date }} - {{ p.mode_of_payment }}{{ p.payment_type === 'Refund' ? ' (Refund)' : '' }}
                <i
                  v-if="p.journal_entry"
                  class="bi bi-check-circle-fill text-emerald-500"
                  :title="`Posted to Chart of Accounts (${p.journal_entry})`"
                ></i>
                <i
                  v-else
                  class="bi bi-dash-circle text-slate-300"
                  title="Not yet posted to Chart of Accounts - set Gym Settings > Default Income Account"
                ></i>
              </span>
              <span class="font-semibold" :class="p.payment_type === 'Refund' ? 'text-amber-600' : 'text-emerald-600'">
                {{ p.payment_type === 'Refund' ? '-' : '' }}{{ p.amount }}
              </span>
            </li>
          </ul>
        </div>

        <form class="mt-4 flex flex-col gap-2 border-t border-slate-200 pt-4" @submit.prevent="submitSession">
          <h3 class="text-xs font-semibold text-slate-600">Log Session</h3>
          <select v-model="sessionForm.trainer" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required>
            <option value="" disabled>Trainer...</option>
            <option v-for="t in options.trainers" :key="t.name" :value="t.name">{{ t.trainer_name }}</option>
          </select>
          <div class="grid grid-cols-3 gap-2">
            <input v-model="sessionForm.session_date" type="date" class="w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
            <input v-model="sessionForm.start_time" type="time" class="w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
            <input v-model="sessionForm.duration_minutes" type="number" min="1" step="1" placeholder="Mins" class="w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          </div>
          <input v-model="sessionForm.notes" type="text" placeholder="Notes (optional)" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          <button type="submit" :disabled="loggingSession"
            class="rounded-lg bg-[var(--gym-accent)] px-3 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:opacity-60">
            {{ loggingSession ? 'Logging...' : 'Log Session' }}
          </button>
        </form>

        <div class="mt-4 border-t border-slate-200 pt-3">
          <h3 class="mb-2 text-xs font-semibold text-slate-600">Session History</h3>
          <p v-if="!selected.sessions.length" class="text-xs text-slate-500">No sessions logged yet.</p>
          <ul v-else class="space-y-1.5 text-xs">
            <li v-for="s in selected.sessions" :key="s.name" class="flex items-center justify-between gap-2 text-slate-600">
              <span class="min-w-0 flex-1 truncate">
                {{ s.session_date }}{{ s.start_time ? ' ' + s.start_time.slice(0, 5) : '' }} - {{ s.trainer }}
                <span v-if="s.notes" class="text-slate-400"> ({{ s.notes }})</span>
              </span>
              <select
                :value="s.status"
                class="shrink-0 rounded-full border border-slate-300 bg-white px-2 py-0.5 text-[11px] font-semibold"
                :class="s.status === 'Completed' ? 'text-emerald-600' : s.status === 'Cancelled' || s.status === 'No-Show' ? 'text-red-600' : 'text-slate-500'"
                @change="onSessionStatusChange(s, $event.target.value)"
              >
                <option value="Scheduled">Scheduled</option>
                <option value="Completed">Completed</option>
                <option value="Cancelled">Cancelled</option>
                <option value="No-Show">No-Show</option>
              </select>
            </li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';
import NewPtPurchaseModal from '@/components/NewPtPurchaseModal.vue';
import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

function flt(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

const options = ref({ members: [], pt_packages: [], trainers: [], mode_of_payments: [], enable_paystack_payments: false });
const purchases = ref([]);
const listPackage = ref('');
const listStatus = ref('');
const listLoading = ref(true);
const selected = ref(null);
const showCreate = ref(false);
const collecting = ref(false);
const loggingSession = ref(false);
const sendingLink = ref(false);
const paymentLink = ref('');

const paymentForm = reactive({ amount: '', mode_of_payment: '', reference_no: '', payment_type: 'Payment' });
const sessionForm = reactive({
  trainer: '',
  session_date: new Date().toISOString().slice(0, 10),
  start_time: '',
  duration_minutes: 60,
  notes: '',
});

async function loadOptions() {
  try {
    options.value = await call('gym_management.admin_api.get_pt_form_options');
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load form options.', 'error');
  }
}

async function loadList() {
  listLoading.value = true;
  try {
    purchases.value = await call('gym_management.admin_api.list_pt_purchases', {
      pt_package: listPackage.value,
      status: listStatus.value,
    });
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load PT purchases.', 'error');
  } finally {
    listLoading.value = false;
  }
}

function onPurchaseCreated(purchase) {
  showCreate.value = false;
  ui.showToast('PT purchase created.');
  loadList();
  selectPurchase(purchase.name);
}

async function selectPurchase(name) {
  try {
    selected.value = await call('gym_management.admin_api.get_pt_purchase', { name });
    // Pre-fill with what's actually owed, same "starting point, not a
    // straitjacket" idea Memberships.vue's own selectMembership() uses.
    const outstanding = flt(selected.value.purchase.outstanding_amount);
    paymentForm.amount = outstanding !== 0 ? Math.abs(outstanding) : '';
    paymentForm.mode_of_payment = '';
    paymentForm.reference_no = '';
    paymentForm.payment_type = outstanding < 0 ? 'Refund' : 'Payment';
    paymentLink.value = '';
    sessionForm.trainer = '';
    sessionForm.session_date = new Date().toISOString().slice(0, 10);
    sessionForm.start_time = '';
    sessionForm.duration_minutes = 60;
    sessionForm.notes = '';
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load this purchase.', 'error');
  }
}

async function submitPayment() {
  if (!selected.value) return;
  collecting.value = true;
  try {
    await call('gym_management.admin_api.collect_pt_payment', {
      pt_package_purchase: selected.value.purchase.name,
      amount: paymentForm.amount,
      mode_of_payment: paymentForm.mode_of_payment,
      payment_type: paymentForm.payment_type,
      reference_no: paymentForm.reference_no,
    });
    ui.showToast(paymentForm.payment_type === 'Refund' ? 'Refund recorded.' : 'Payment recorded.');
    await selectPurchase(selected.value.purchase.name);
    loadList();
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not record this payment.', 'error');
  } finally {
    collecting.value = false;
  }
}

async function sendPaymentLink() {
  if (!selected.value) return;
  sendingLink.value = true;
  paymentLink.value = '';
  try {
    const result = await call('gym_management.admin_api.send_pt_payment_link', {
      pt_package_purchase: selected.value.purchase.name,
    });
    paymentLink.value = result.link;
    ui.showToast(
      result.emailed
        ? `Payment link emailed to ${result.email}.`
        : 'Payment link generated - copy it below to share with the member.'
    );
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not generate a payment link.', 'error');
  } finally {
    sendingLink.value = false;
  }
}

async function copyPaymentLink() {
  if (!paymentLink.value) return;
  try {
    await navigator.clipboard.writeText(paymentLink.value);
    ui.showToast('Link copied.');
  } catch (err) {
    ui.showToast('Could not copy - select and copy the link manually.', 'error');
  }
}

async function submitSession() {
  if (!selected.value || !sessionForm.trainer) return;
  loggingSession.value = true;
  try {
    await call('gym_management.admin_api.create_pt_session', {
      pt_package_purchase: selected.value.purchase.name,
      trainer: sessionForm.trainer,
      session_date: sessionForm.session_date,
      start_time: sessionForm.start_time,
      duration_minutes: sessionForm.duration_minutes,
      notes: sessionForm.notes,
    });
    ui.showToast('Session logged.');
    await selectPurchase(selected.value.purchase.name);
    loadList();
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not log this session.', 'error');
  } finally {
    loggingSession.value = false;
  }
}

async function onSessionStatusChange(session, newStatus) {
  if (newStatus === session.status) return;
  try {
    await call('gym_management.admin_api.update_pt_session_status', { name: session.name, status: newStatus });
    ui.showToast('Session status updated.');
    if (selected.value) await selectPurchase(selected.value.purchase.name);
    loadList();
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not update this session.', 'error');
  }
}

// Same self-healing shape as Memberships.vue's own repairMemberNames() -
// a no-op once every row already has company/customer/currency/
// conversion_rate set (see backfill_pt_purchase_derived_fields()'s own
// docstring for why those matter).
async function repairPtDerivedFields() {
  try {
    const result = await call('gym_management.admin_api.backfill_pt_purchase_derived_fields');
    if (result?.fixed) loadList();
  } catch (err) {
    // Non-fatal.
  }
}

// Same shape as Memberships.vue's own repairPaymentAccounting().
async function repairPtPaymentAccounting() {
  try {
    await call('gym_management.admin_api.backfill_pt_purchase_accounting');
  } catch (err) {
    // Non-fatal.
  }
}

onMounted(() => {
  loadOptions();
  loadList();
  repairPtDerivedFields();
  repairPtPaymentAccounting();
});
watch(() => ui.refreshKey, () => {
  loadOptions();
  loadList();
  if (selected.value) selectPurchase(selected.value.purchase.name);
});
</script>
