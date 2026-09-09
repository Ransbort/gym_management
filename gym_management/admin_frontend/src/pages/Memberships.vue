<template>
  <div class="flex h-full flex-col gap-4 overflow-hidden bg-slate-50 p-6 lg:flex-row">
    <!-- List + filters -->
    <section class="flex min-w-0 flex-1 flex-col">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-xl font-bold text-slate-900">Memberships & Payments</h1>
        <div class="flex items-center gap-2">
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

      <p v-if="flash" :class="['mb-3 rounded-lg px-3 py-2 text-sm', flashError ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700']">
        {{ flash }}
      </p>

      <NewMembershipModal
        v-if="showCreate"
        @close="showCreate = false"
        @created="onMembershipCreated"
      />

      <div class="mb-3 flex gap-2">
        <select v-model="listPlan" class="w-56 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" @change="loadList">
          <option value="">All plans</option>
          <option v-for="p in options.membership_plans" :key="p.name" :value="p.name">{{ p.plan_name }}</option>
        </select>
        <select v-model="listStatus" class="w-40 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" @change="loadList">
          <option value="">All statuses</option>
          <option v-for="s in ['Draft', 'Active', 'Expired', 'Suspended', 'Cancelled']" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div class="flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-white">
        <p v-if="listLoading" class="px-4 py-6 text-sm text-slate-500">Loading...</p>
        <p v-else-if="!memberships.length" class="px-4 py-6 text-sm text-slate-500">No memberships found.</p>
        <table v-else class="w-full text-left text-sm">
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
              class="cursor-pointer border-b border-slate-100 text-slate-700 hover:bg-slate-50"
              :class="{ 'bg-slate-100': selected && selected.membership.name === m.name }"
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
          <dt class="text-slate-500">Outstanding</dt><dd class="text-right font-semibold text-amber-600">{{ selected.membership.outstanding_amount }}</dd>
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

        <form class="mt-4 flex flex-col gap-2 border-t border-slate-200 pt-4" @submit.prevent="submitPayment">
          <h3 class="text-xs font-semibold text-slate-600">Collect Payment</h3>
          <input v-model="paymentForm.amount" type="number" step="0.01" min="0.01" placeholder="Amount" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required />
          <select v-model="paymentForm.mode_of_payment" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required>
            <option value="" disabled>Mode of payment...</option>
            <option v-for="mop in options.mode_of_payments" :key="mop.name" :value="mop.name">{{ mop.name }}</option>
          </select>
          <input v-model="paymentForm.reference_no" type="text" placeholder="Reference / receipt no. (optional)" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          <button type="submit" :disabled="collecting"
            class="rounded-lg bg-[var(--gym-accent)] px-3 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:opacity-60">
            {{ collecting ? 'Recording...' : 'Record Payment' }}
          </button>
        </form>

        <div class="mt-4 border-t border-slate-200 pt-3">
          <h3 class="mb-2 text-xs font-semibold text-slate-600">Payment History</h3>
          <p v-if="!selected.payments.length" class="text-xs text-slate-500">No payments recorded yet.</p>
          <ul v-else class="space-y-1.5 text-xs">
            <li v-for="p in selected.payments" :key="p.name" class="flex justify-between text-slate-600">
              <span>{{ p.payment_date }} - {{ p.mode_of_payment }}</span>
              <span class="font-semibold text-emerald-600">{{ p.amount }}</span>
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
import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

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
const selected = ref(null);
const showCreate = ref(false);
const collecting = ref(false);
const flash = ref('');
const flashError = ref(false);
const showCreateMember = ref(false);
const createMemberPrefill = ref('');
const sendingLink = ref(false);
const paymentLink = ref('');

const paymentForm = reactive({ amount: '', mode_of_payment: '', reference_no: '' });

function showFlash(message, isError) {
  flash.value = message;
  flashError.value = !!isError;
  setTimeout(() => { if (flash.value === message) flash.value = ''; }, 4000);
}

async function loadOptions() {
  try {
    options.value = await call('gym_management.admin_api.get_membership_form_options');
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not load form options.', true);
  }
}

async function loadList() {
  listLoading.value = true;
  try {
    memberships.value = await call('gym_management.admin_api.list_memberships', { membership_plan: listPlan.value, status: listStatus.value });
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not load memberships.', true);
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
  showFlash(`${member.member_name} created.`, false);
}

function onMembershipCreated(membership) {
  showCreate.value = false;
  showFlash('Membership created.', false);
  loadList();
}

async function selectMembership(name) {
  try {
    selected.value = await call('gym_management.admin_api.get_membership', { name });
    paymentForm.amount = '';
    paymentForm.mode_of_payment = '';
    paymentForm.reference_no = '';
    paymentLink.value = '';
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not load this membership.', true);
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
    showFlash(
      result.emailed
        ? `Payment link emailed to ${result.email}.`
        : 'Payment link generated - copy it below to share with the member.',
      false
    );
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not generate a payment link.', true);
  } finally {
    sendingLink.value = false;
  }
}

async function copyPaymentLink() {
  if (!paymentLink.value) return;
  try {
    await navigator.clipboard.writeText(paymentLink.value);
    showFlash('Link copied.', false);
  } catch (err) {
    showFlash('Could not copy - select and copy the link manually.', true);
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
      reference_no: paymentForm.reference_no,
    });
    showFlash('Payment recorded.', false);
    await selectMembership(selected.value.membership.name);
    loadList();
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not record this payment.', true);
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

onMounted(() => {
  loadOptions();
  loadList();
  repairMemberNames();
});
watch(() => ui.refreshKey, () => {
  loadOptions();
  loadList();
  if (selected.value) selectMembership(selected.value.membership.name);
});
</script>
