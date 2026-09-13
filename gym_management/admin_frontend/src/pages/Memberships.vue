<template>
  <div class="flex h-full flex-col gap-4 overflow-hidden bg-slate-50 p-6 lg:flex-row">
    <!-- List + filters -->
    <section class="flex min-w-0 flex-1 flex-col">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-xl font-bold text-slate-900">Memberships & Payments</h1>
        <div class="flex items-center gap-2">
          <button
            v-if="auth.isManager"
            class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            @click="showCreatePlan = true"
          >
            <i class="bi bi-card-checklist"></i> New Plan
          </button>
          <button
            class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            @click="openCreateMember()"
          >
            <i class="bi bi-person-plus"></i> New Member
          </button>
          <button
            class="rounded-lg bg-[var(--gym-accent)] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[var(--gym-accent-hover)]"
            @click="showCreate = true"
          >
            <i class="bi bi-plus-lg"></i> New Membership
          </button>
        </div>
      </div>

      <NewMembershipModal
        v-if="showCreate"
        @close="showCreate = false"
        @created="onMembershipCreated"
      />

      <NewMembershipPlanModal
        v-if="showCreatePlan"
        @close="showCreatePlan = false"
        @created="onPlanCreated"
      />

      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div class="flex gap-2">
          <select v-model="listPlan" class="w-56 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" @change="loadList">
            <option value="">All plans</option>
            <option v-for="p in options.membership_plans" :key="p.name" :value="p.name">{{ p.plan_name }}</option>
          </select>
          <select v-model="listStatus" class="w-40 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" @change="loadList">
            <option value="">All statuses</option>
            <option v-for="s in ['Draft', 'Active', 'Expired', 'Suspended', 'Cancelled']" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="flex items-center gap-1 rounded-lg bg-slate-200 p-1 text-xs font-semibold">
          <button
            type="button"
            class="rounded-md px-2.5 py-1.5 transition-colors"
            :class="viewMode === 'list' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'"
            title="List view"
            @click="viewMode = 'list'"
          ><i class="bi bi-list-ul"></i></button>
          <button
            type="button"
            class="rounded-md px-2.5 py-1.5 transition-colors"
            :class="viewMode === 'grid' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'"
            title="Grid view"
            @click="viewMode = 'grid'"
          ><i class="bi bi-grid-3x3-gap-fill"></i></button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-white">
        <p v-if="listLoading" class="px-4 py-6 text-sm text-slate-500">Loading...</p>
        <p v-else-if="!memberships.length" class="px-4 py-6 text-sm text-slate-500">No memberships found.</p>
        <table v-else-if="viewMode === 'list'" class="w-full text-left text-sm">
          <thead class="sticky top-0 border-b border-slate-200 bg-white text-slate-500">
            <tr>
              <th class="px-4 py-2 font-semibold">Member</th>
              <th class="px-4 py-2 font-semibold">Plan</th>
              <th class="px-4 py-2 font-semibold">Status</th>
              <th class="px-4 py-2 font-semibold">Outstanding</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in memberships" :key="m.name"
              class="cursor-pointer border-b border-slate-100 border-l-4 border-l-transparent text-slate-700 hover:bg-slate-50"
              :class="{ '!border-l-[var(--gym-accent)] !bg-[var(--gym-accent-tint)]': selected && selected.membership.name === m.name }"
              @click="selectMembership(m.name)">
              <td class="px-4 py-2">{{ m.member_name }}</td>
              <td class="px-4 py-2">{{ m.membership_plan }}</td>
              <td class="px-4 py-2">{{ m.status }}</td>
              <td class="px-4 py-2" :class="m.outstanding_amount > 0 ? 'text-amber-600' : 'text-emerald-600'">
                {{ m.outstanding_amount }}
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 xl:grid-cols-3">
          <div v-for="m in memberships" :key="m.name"
            class="cursor-pointer rounded-xl border-2 border-slate-200 bg-white p-3 transition-colors hover:border-slate-300"
            :class="{ '!border-[var(--gym-accent)] !bg-[var(--gym-accent-tint)]': selected && selected.membership.name === m.name }"
            @click="selectMembership(m.name)">
            <div class="flex items-start justify-between gap-2">
              <p class="min-w-0 truncate text-sm font-semibold text-slate-900">{{ m.member_name }}</p>
              <span
                class="shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold"
                :class="m.status === 'Active' ? 'bg-emerald-50 text-emerald-600' : m.status === 'Expired' ? 'bg-red-50 text-red-600' : 'bg-slate-100 text-slate-500'"
              >{{ m.status }}</span>
            </div>
            <p class="mt-1 truncate text-xs text-slate-500">{{ m.membership_plan }}</p>
            <p class="mt-2 text-xs font-semibold" :class="m.outstanding_amount > 0 ? 'text-amber-600' : 'text-emerald-600'">
              Outstanding: {{ m.outstanding_amount }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Detail / collect payment -->
    <section class="flex w-full flex-col lg:w-96 lg:shrink-0">
      <div v-if="!selected" class="flex h-full items-center justify-center rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
        Select a membership to view details and collect payment.
      </div>
      <div v-else class="flex h-full flex-col overflow-y-auto rounded-xl border border-slate-200 bg-white p-4">
        <h2 class="text-sm font-semibold text-slate-900">{{ selected.membership.member_name }}</h2>
        <p class="text-xs text-slate-500">{{ selected.membership.name }} - {{ selected.membership.membership_plan }}</p>

        <dl class="mt-3 grid grid-cols-2 gap-2 text-xs">
          <dt class="text-slate-500">Grand Total</dt><dd class="text-right text-slate-700">{{ selected.membership.grand_total }}</dd>
          <dt class="text-slate-500">Paid</dt><dd class="text-right text-slate-700">{{ selected.membership.paid_amount }}</dd>
          <dt class="text-slate-500">Outstanding</dt>
          <dd class="text-right font-semibold" :class="selected.membership.outstanding_amount > 0 ? 'text-amber-600' : 'text-emerald-600'">
            {{ selected.membership.outstanding_amount }}<span v-if="selected.membership.outstanding_amount < 0" class="ml-1 font-normal text-slate-400">(credit)</span>
          </dd>
          <dt class="text-slate-500">Status</dt><dd class="text-right text-slate-700">{{ selected.membership.status }} / {{ selected.membership.payment_status }}</dd>
        </dl>

        <div v-if="selected.membership.outstanding_amount > 0 && options.enable_paystack_payments" class="mt-3 border-t border-slate-200 pt-3">
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

        <form v-if="selected.membership.outstanding_amount !== 0" class="mt-4 flex flex-col gap-2 border-t border-slate-200 pt-4" @submit.prevent="submitPayment">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-semibold text-slate-600">{{ paymentForm.payment_type === 'Refund' ? 'Pay Back Member' : 'Collect Payment' }}</h3>
            <!-- Only worth offering when there's actually a credit to pay
                 back - outstanding_amount < 0 means paid_amount exceeds
                 grand_total (e.g. an overpayment or a duplicated Paystack
                 confirmation - see Gym Membership Payment's own validate(),
                 which also hard-caps a refund at what's actually been paid). -->
            <button
              v-if="selected.membership.outstanding_amount < 0 || paymentForm.payment_type === 'Refund'"
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
      </div>
    </section>

    <CreateMemberModal
      v-if="showCreateMember"
      :prefill-name="createMemberPrefill"
      @close="showCreateMember = false"
      @created="onMemberCreated"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';
import CreateMemberModal from '@/components/CreateMemberModal.vue';
import NewMembershipModal from '@/components/NewMembershipModal.vue';
import NewMembershipPlanModal from '@/components/NewMembershipPlanModal.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';

const ui = useUiStore();
const auth = useAuthStore();

function flt(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

// mode_of_payments (Collect Payment panel) and membership_plans (the plan
// filter above, replacing the old free-text member search - picking a plan
// there filters this list down to just the members subscribed to it) -
// membership-creation-specific options otherwise live inside
// NewMembershipModal.vue, which fetches its own copy.
const options = ref({ mode_of_payments: [], membership_plans: [], enable_paystack_payments: false });
const memberships = ref([]);
const listPlan = ref('');
const listStatus = ref('');
const listLoading = ref(true);
const viewMode = ref('list');
const selected = ref(null);
const showCreate = ref(false);
const showCreatePlan = ref(false);
const collecting = ref(false);
const showCreateMember = ref(false);
const createMemberPrefill = ref('');
const sendingLink = ref(false);
const paymentLink = ref('');

const paymentForm = reactive({ amount: '', mode_of_payment: '', reference_no: '', payment_type: 'Payment' });

async function loadOptions() {
  try {
    options.value = await call('gym_management.admin_api.get_membership_form_options');
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load form options.', 'error');
  }
}

async function loadList() {
  listLoading.value = true;
  try {
    memberships.value = await call('gym_management.admin_api.list_memberships', { membership_plan: listPlan.value, status: listStatus.value });
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load memberships.', 'error');
  } finally {
    listLoading.value = false;
  }
}

function openCreateMember(prefill) {
  createMemberPrefill.value = prefill || '';
  showCreateMember.value = true;
}

function onMemberCreated(member) {
  showCreateMember.value = false;
  ui.showToast(`${member.member_name} created.`);
}

function onMembershipCreated(membership) {
  showCreate.value = false;
  ui.showToast('Membership created.');
  loadList();
}

function onPlanCreated(plan) {
  showCreatePlan.value = false;
  ui.showToast(`${plan.plan_name} plan created.`);
  // Newly created, so it isn't in the options.membership_plans list this
  // page already fetched at mount - add it in place (same shape as
  // NewMembershipModal.vue's own onPlanCreated()) so it shows up in the
  // plan filter above immediately, without a full loadOptions() round-trip.
  options.value.membership_plans = [...options.value.membership_plans, plan];
}

async function selectMembership(name) {
  try {
    selected.value = await call('gym_management.admin_api.get_membership', { name });
    // Pre-fill with what's actually owed (or, for a credit balance, what's
    // owed back) instead of leaving it blank - outstanding_amount is 0 or
    // positive for a normal balance (equal to Grand Total on a fresh, unpaid
    // membership - see get_membership()) and negative for a credit, so this
    // also self-adjusts correctly for a partially-paid membership rather
    // than always suggesting the full Grand Total regardless of what's
    // already been paid. Still just a starting point - staff can edit it
    // for a partial payment.
    const outstanding = flt(selected.value.membership.outstanding_amount);
    paymentForm.amount = outstanding !== 0 ? Math.abs(outstanding) : '';
    paymentForm.mode_of_payment = '';
    paymentForm.reference_no = '';
    // Default to Refund only when there's actually a credit to pay back -
    // otherwise a freshly-selected membership always starts on the normal
    // Collect Payment path.
    paymentForm.payment_type = outstanding < 0 ? 'Refund' : 'Payment';
    paymentLink.value = '';
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load this membership.', 'error');
  }
}

async function sendPaymentLink() {
  if (!selected.value) return;
  sendingLink.value = true;
  paymentLink.value = '';
  try {
    const result = await call('gym_management.admin_api.send_payment_link', {
      gym_membership: selected.value.membership.name,
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

async function submitPayment() {
  if (!selected.value) return;
  collecting.value = true;
  try {
    await call('gym_management.admin_api.collect_payment', {
      gym_membership: selected.value.membership.name,
      amount: paymentForm.amount,
      mode_of_payment: paymentForm.mode_of_payment,
      payment_type: paymentForm.payment_type,
      reference_no: paymentForm.reference_no,
    });
    ui.showToast(paymentForm.payment_type === 'Refund' ? 'Refund recorded.' : 'Payment recorded.');
    await selectMembership(selected.value.membership.name);
    loadList();
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not record this payment.', 'error');
  } finally {
    collecting.value = false;
  }
}

// One-off, self-healing repair for memberships created before
// create_membership() started setting member_name explicitly (see that
// function's own comment in admin_api.py) - safe to call every mount,
// it's a no-op once every row has already been fixed.
async function repairMemberNames() {
  try {
    const result = await call('gym_management.admin_api.backfill_membership_member_names');
    if (result?.fixed) loadList();
  } catch (err) {
    // Non-fatal: worst case a few older rows keep showing a blank Member
    // column until the next successful mount.
  }
}

// Same self-healing shape as repairMemberNames() above: a no-op once every
// payment either already has a Journal Entry or has been logged as
// unpostable (see Gym Membership Payment.create_accounting_entry()'s own
// missing-account log_error) - catches payments up to the Chart of
// Accounts once Gym Settings > Default Income Account gets configured,
// without staff having to trigger anything manually.
async function repairPaymentAccounting() {
  try {
    await call('gym_management.admin_api.backfill_membership_payment_accounting');
  } catch (err) {
    // Non-fatal: worst case some older payments stay un-posted until the
    // next successful mount.
  }
}

onMounted(() => {
  loadOptions();
  loadList();
  repairMemberNames();
  repairPaymentAccounting();
});
watch(() => ui.refreshKey, () => {
  loadOptions();
  loadList();
  if (selected.value) selectMembership(selected.value.membership.name);
});
</script>
