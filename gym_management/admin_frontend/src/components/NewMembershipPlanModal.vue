<template>
  <!-- Same centered-dialog treatment as NewMembershipModal.vue/
       CreateMemberModal.vue - opened either standalone from Memberships.vue's
       "New Plan" button, or inline from NewMembershipModal.vue's "Can't find
       it? Create a new plan" link (see that file's own Membership Plan
       field). -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[110] flex items-center justify-center bg-black/40 p-4" @mousedown.self="cancel">
      <div class="flex max-h-[85vh] w-full max-w-lg flex-col rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-semibold text-slate-900">New Membership Plan</h2>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600" @click="cancel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <form id="new-membership-plan-form" class="grid flex-1 auto-rows-min content-start grid-cols-1 gap-3 overflow-y-auto pr-1 sm:grid-cols-2" @submit.prevent="submit">
          <Field label="Plan Name" required class="sm:col-span-2">
            <input v-model="form.plan_name" type="text" placeholder="e.g. Gold Monthly" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required />
          </Field>

          <Field label="Duration (Months)" required>
            <input v-model="form.duration_months" type="number" min="1" step="1" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required />
          </Field>

          <Field label="Price" required>
            <input v-model="form.price" type="number" min="0" step="0.01" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" required />
          </Field>

          <Field label="Class Credits / month">
            <input v-model="form.class_credits_per_month" type="number" min="0" step="1" placeholder="Leave 0 for unlimited" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          </Field>

          <Field label="Included PT Sessions / month">
            <input v-model="form.includes_pt_sessions" type="number" min="0" step="1" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
          </Field>

          <Field label="Access Hours" class="sm:col-span-2">
            <select v-model="form.access_hours" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]">
              <option value="Full Access">Full Access</option>
              <option value="Off-Peak Only">Off-Peak Only</option>
            </select>
          </Field>

          <Field label="Description" class="sm:col-span-2">
            <textarea v-model="form.description" rows="2" placeholder="Optional" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"></textarea>
          </Field>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-2">{{ error }}</p>
        </form>

        <div class="mt-4 flex shrink-0 items-center gap-2 border-t border-slate-100 pt-4">
          <button type="submit" form="new-membership-plan-form" :disabled="creating || !form.plan_name || !form.duration_months || form.price === ''"
            class="rounded-lg bg-[var(--gym-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50">
            {{ creating ? 'Creating...' : 'Create Plan' }}
          </button>
          <button type="button" :disabled="creating"
            class="rounded-lg px-4 py-2 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-200"
            @click="cancel">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { h, reactive, ref } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';

const emit = defineEmits(['close', 'created']);

const creating = ref(false);
const error = ref('');

const form = reactive({
  plan_name: '',
  duration_months: '',
  price: '',
  class_credits_per_month: '',
  includes_pt_sessions: '',
  access_hours: 'Full Access',
  description: '',
});

function cancel() {
  if (creating.value) return;
  emit('close');
}

async function submit() {
  if (!form.plan_name || !form.duration_months || form.price === '') return;
  creating.value = true;
  error.value = '';
  try {
    const plan = await call('gym_management.admin_api.create_membership_plan', {
      plan_name: form.plan_name,
      duration_months: form.duration_months,
      price: form.price,
      class_credits_per_month: form.class_credits_per_month,
      includes_pt_sessions: form.includes_pt_sessions,
      access_hours: form.access_hours,
      description: form.description,
    });
    emit('created', plan);
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not create this membership plan.';
  } finally {
    creating.value = false;
  }
}

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
