<template>
  <!-- Centered popup dialog, same treatment as CreateMemberModal.vue (title +
       X close top-right, red-asterisk required labels, Create/Cancel buttons
       bottom-left). Extracted out of Memberships.vue so both that page and
       Overview.vue (top-right quick actions) can open the same modal instead
       of duplicating this form. -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4" @mousedown.self="cancel">
      <div class="flex h-[80vh] w-full max-w-2xl flex-col rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-semibold text-slate-900">New Membership</h2>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600" @click="cancel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <form id="new-membership-form" class="grid flex-1 auto-rows-min content-start grid-cols-1 gap-3 overflow-y-auto pr-1 sm:grid-cols-2" @submit.prevent="submit">
          <Field label="Member" required>
            <select v-model="form.member" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required>
              <option value="" disabled>Select a member...</option>
              <option v-for="m in options.members" :key="m.name" :value="m.name">{{ m.member_name }} - {{ m.phone || 'no phone' }}</option>
            </select>
            <button
              type="button"
              class="mt-1 text-xs font-semibold text-[var(--gym-accent)] hover:text-[var(--gym-accent-hover)]"
              @click="openCreateMember()"
            >
              <i class="bi bi-person-plus"></i> Can't find them? Create a new member
            </button>
          </Field>

          <Field label="Membership Plan" required>
            <select v-model="form.membership_plan" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required>
              <option value="" disabled>Select a plan...</option>
              <option v-for="p in options.membership_plans" :key="p.name" :value="p.name">{{ p.plan_name }} ({{ p.duration_months }}mo, {{ p.price }})</option>
            </select>
          </Field>

          <Field label="Membership Plan Type" required>
            <select v-model="form.membership_plan_type" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required>
              <option value="" disabled>Select a type...</option>
              <option v-for="t in options.membership_plan_types" :key="t.name" :value="t.name">{{ t.plan_type_name }}</option>
            </select>
          </Field>

          <Field label="Trainer" required>
            <select v-model="form.trainer" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required>
              <option value="" disabled>Select a trainer...</option>
              <option v-for="t in options.trainers" :key="t.name" :value="t.name">{{ t.trainer_name }}</option>
            </select>
          </Field>

          <Field label="Time Slot" required>
            <input v-model="form.time_slot" type="text" placeholder="e.g. 6:00 AM - 7:00 AM" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required />
          </Field>

          <Field label="Mode of Payment" required>
            <select v-model="form.mode_of_payment" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required>
              <option value="" disabled>Select...</option>
              <option v-for="mop in options.mode_of_payments" :key="mop.name" :value="mop.name">{{ mop.name }}</option>
            </select>
          </Field>

          <Field label="Activation Date">
            <input v-model="form.start_date" type="date" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          </Field>

          <Field label="Document Date">
            <input v-model="form.date" type="date" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          </Field>

          <Field label="Valid Number of Days">
            <input v-model="form.valid_number_of_days" type="number" min="1" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          </Field>

          <Field label="Number of Service">
            <input v-model="form.number_of_service" type="number" min="1" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          </Field>

          <Field label="Company">
            <select v-model="form.company" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]">
              <option v-for="c in options.companies" :key="c.name" :value="c.name">{{ c.name }}</option>
            </select>
          </Field>

          <Field label="Taxes and Charges">
            <select v-model="form.taxes_and_charges" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]">
              <option value="">None</option>
              <option v-for="t in options.taxes_and_charges_templates" :key="t.name" :value="t.name">{{ t.name }}</option>
            </select>
          </Field>

          <Field label="Cost Center">
            <select v-model="form.cost_center" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]">
              <option value="">Default</option>
              <option v-for="c in options.cost_centers" :key="c.name" :value="c.name">{{ c.name }}</option>
            </select>
          </Field>

          <Field label="Invoice Reference" class="sm:col-span-2">
            <input v-model="form.invoice_reference" type="text" placeholder="Optional free-text reference to an external invoice/receipt" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          </Field>

          <Field label="Gym Services" class="sm:col-span-2">
            <div class="flex flex-wrap gap-3">
              <label v-for="s in options.gym_services" :key="s.name" class="flex items-center gap-1.5 text-sm text-slate-600">
                <input type="checkbox" :value="s.name" v-model="form.gym_services" />
                {{ s.service_name }}
              </label>
            </div>
          </Field>

          <label class="flex items-center gap-1.5 text-sm text-slate-600 sm:col-span-2">
            <input type="checkbox" v-model="form.is_admission_fee" />
            Include Admission Fee
          </label>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-2">{{ error }}</p>
        </form>

        <div class="mt-4 flex shrink-0 items-center gap-2 border-t border-slate-100 pt-4">
          <button type="submit" form="new-membership-form" :disabled="creating || !form.member"
            class="rounded-lg bg-[var(--gym-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50">
            {{ creating ? 'Creating...' : 'Create Membership' }}
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
  </Teleport>
</template>

<script setup>
import { h, onMounted, reactive, ref } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';
import CreateMemberModal from '@/components/CreateMemberModal.vue';

const emit = defineEmits(['close', 'created']);

const options = ref({
  members: [], membership_plans: [], membership_plan_types: [], gym_services: [], trainers: [], mode_of_payments: [],
  companies: [], taxes_and_charges_templates: [], cost_centers: [],
});
const creating = ref(false);
const error = ref('');
const showCreateMember = ref(false);

const form = reactive({
  member: '',
  membership_plan: '', membership_plan_type: '', trainer: '', time_slot: '', mode_of_payment: '',
  start_date: new Date().toISOString().slice(0, 10),
  date: new Date().toISOString().slice(0, 10),
  valid_number_of_days: '', number_of_service: 1,
  company: '', taxes_and_charges: '', cost_center: '', invoice_reference: '',
  gym_services: [], is_admission_fee: false,
});

function cancel() {
  if (creating.value) return;
  emit('close');
}

async function loadOptions() {
  try {
    options.value = await call('gym_management.admin_api.get_membership_form_options');
    form.valid_number_of_days = options.value.default_valid_number_of_days || '';
    form.company = options.value.default_company || '';
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not load form options.';
  }
}

function openCreateMember() {
  showCreateMember.value = true;
}
function onMemberCreated(member) {
  showCreateMember.value = false;
  // Newly created, so it isn't in the options.members list this modal
  // already fetched at mount - add it in place and select it, rather than
  // re-fetching the whole (up to 500-row) list just for one new row.
  options.value.members = [...options.value.members, member];
  form.member = member.name;
}

async function submit() {
  if (!form.member) return;
  creating.value = true;
  error.value = '';
  try {
    const membership = await call('gym_management.admin_api.create_membership', {
      member: form.member,
      membership_plan: form.membership_plan,
      membership_plan_type: form.membership_plan_type,
      trainer: form.trainer,
      time_slot: form.time_slot,
      mode_of_payment: form.mode_of_payment,
      start_date: form.start_date,
      is_admission_fee: form.is_admission_fee ? 1 : 0,
      gym_services: form.gym_services,
      company: form.company,
      date: form.date,
      valid_number_of_days: form.valid_number_of_days,
      number_of_service: form.number_of_service,
      taxes_and_charges: form.taxes_and_charges,
      cost_center: form.cost_center,
      invoice_reference: form.invoice_reference,
    });
    emit('created', membership);
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not create this membership.';
  } finally {
    creating.value = false;
  }
}

onMounted(loadOptions);

const Field = {
  props: { label: String, required: Boolean },
  render() {
    return h('label', { class: 'flex flex-col gap-1 text-sm font-semibold text-slate-700' }, [
      h('span', {}, [this.label, this.required ? h('span', { class: 'text-red-500' }, '*') : null]),
      ...(this.$slots.default ? this.$slots.default() : []),
    ]);
  },
};
</script>
