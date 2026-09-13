<template>
  <!-- Same popup convention as NewMembershipModal.vue - Member/PT Package
       pickers each get a "can't find it, create one" escape hatch instead of
       forcing a trip to the full Desk form. -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4" @mousedown.self="cancel">
      <div class="flex max-h-[90vh] w-full max-w-md flex-col rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-semibold text-slate-900">New PT Purchase</h2>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600" @click="cancel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <form id="new-pt-purchase-form" class="flex flex-1 flex-col gap-4 overflow-y-auto pr-1" @submit.prevent="submit">
          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Member<span class="text-red-500">*</span></span>
            <select v-model="form.member" ref="firstField" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required>
              <option value="" disabled>Select a member...</option>
              <option v-for="m in options.members" :key="m.name" :value="m.name">{{ m.member_name }} - {{ m.phone || 'no phone' }}</option>
            </select>
            <button
              type="button"
              class="mt-1 text-xs font-semibold text-[var(--gym-accent)] hover:text-[var(--gym-accent-hover)]"
              @click="showCreateMember = true"
            >
              <i class="bi bi-person-plus"></i> Can't find them? Create a new member
            </button>
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">PT Package<span class="text-red-500">*</span></span>
            <select v-model="form.pt_package" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required @change="onPackageChosen">
              <option value="" disabled>Select a package...</option>
              <option v-for="p in options.pt_packages" :key="p.name" :value="p.name">{{ p.package_name }} ({{ p.no_of_sessions }} sessions, {{ p.price }})</option>
            </select>
            <button
              type="button"
              class="mt-1 text-xs font-semibold text-[var(--gym-accent)] hover:text-[var(--gym-accent-hover)]"
              @click="showCreatePackage = true"
            >
              <i class="bi bi-plus-lg"></i> Create new package
            </button>
          </label>

          <div class="grid grid-cols-2 gap-3">
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">Purchase Date</span>
              <input
                v-model="form.purchase_date" type="date"
                class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">Amount</span>
              <input
                v-model="form.amount" type="number" min="0" step="0.01" placeholder="From package"
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
                @input="amountFollowsPackage = false"
              />
            </label>
          </div>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Invoice Reference</span>
            <input
              v-model="form.invoice_reference" type="text" placeholder="Optional free-text reference"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            />
          </label>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
        </form>

        <div class="mt-4 flex shrink-0 items-center gap-2 border-t border-slate-100 pt-4">
          <button type="submit" form="new-pt-purchase-form" :disabled="creating || !form.member || !form.pt_package"
            class="rounded-lg bg-[var(--gym-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50">
            {{ creating ? 'Creating...' : 'Create Purchase' }}
          </button>
          <button type="button" :disabled="creating"
            class="rounded-lg px-4 py-2 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-200"
            @click="cancel">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <CreateMemberModal
      v-if="showCreateMember"
      @close="showCreateMember = false"
      @created="onMemberCreated"
    />
    <CreatePtPackageModal
      v-if="showCreatePackage"
      @close="showCreatePackage = false"
      @created="onPackageCreated"
    />
  </Teleport>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';
import CreateMemberModal from '@/components/CreateMemberModal.vue';
import CreatePtPackageModal from '@/components/CreatePtPackageModal.vue';

const emit = defineEmits(['close', 'created']);

const options = ref({ members: [], pt_packages: [], trainers: [] });
const creating = ref(false);
const error = ref('');
const firstField = ref(null);
const showCreateMember = ref(false);
const showCreatePackage = ref(false);
// Tracks whether Amount still matches the selected package's own price (so
// picking a package can pre-fill it) versus having been hand-edited by
// staff (in which case picking a different package shouldn't clobber it) -
// same "pre-fill, don't fight the user" idea Memberships.vue's own
// selectMembership() uses for its payment amount.
let amountFollowsPackage = true;

const form = reactive({
  member: '',
  pt_package: '',
  purchase_date: new Date().toISOString().slice(0, 10),
  amount: '',
  invoice_reference: '',
});

function cancel() {
  if (creating.value) return;
  emit('close');
}

function onPackageChosen() {
  if (!amountFollowsPackage) return;
  const pkg = options.value.pt_packages.find((p) => p.name === form.pt_package);
  if (pkg) form.amount = pkg.price;
}

function onMemberCreated(member) {
  showCreateMember.value = false;
  options.value.members = [...options.value.members, member];
  form.member = member.name;
}

function onPackageCreated(pkg) {
  showCreatePackage.value = false;
  options.value.pt_packages = [...options.value.pt_packages, pkg];
  form.pt_package = pkg.name;
  onPackageChosen();
}

async function loadOptions() {
  try {
    options.value = await call('gym_management.admin_api.get_pt_form_options');
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not load form options.';
  }
}

async function submit() {
  if (!form.member || !form.pt_package) return;
  creating.value = true;
  error.value = '';
  try {
    const purchase = await call('gym_management.admin_api.create_pt_purchase', {
      member: form.member,
      pt_package: form.pt_package,
      purchase_date: form.purchase_date,
      amount: form.amount,
      invoice_reference: form.invoice_reference,
    });
    emit('created', purchase);
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not create this purchase.';
  } finally {
    creating.value = false;
  }
}

onMounted(() => {
  nextTick(() => firstField.value?.focus());
  loadOptions();
});
</script>
