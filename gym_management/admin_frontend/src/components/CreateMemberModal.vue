<template>
  <!-- Centered popup dialog, styled after POSNext's own "Create New Customer"
       modal (title + X close top-right, bold labels with a red asterisk for
       required fields, pill-shaped dropdowns, primary+secondary buttons
       bottom-left) - fields themselves are Gym Member's, not Customer's,
       since that's the doctype this actually creates. Teleported to <body>
       so it always sits above the header/sidebar chrome regardless of which
       page opened it. -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4" @mousedown.self="cancel">
      <div class="flex h-[80vh] w-full max-w-md flex-col rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-semibold text-slate-900">Create New Member</h2>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600" @click="cancel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <form id="create-member-form" class="flex flex-1 flex-col gap-4 overflow-y-auto pr-1" @submit.prevent="submit">
          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Member Name<span class="text-red-500">*</span></span>
            <input
              v-model="form.member_name" ref="firstField" type="text" required placeholder="e.g. Jane Doe"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            />
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Mobile Number<span class="text-red-500">*</span></span>
            <input
              v-model="form.phone" type="text" required placeholder="e.g. 024 123 4567"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            />
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Email</span>
            <input
              v-model="form.email" type="email" placeholder="name@example.com"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            />
          </label>

          <div class="grid grid-cols-2 gap-3">
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">Gender</span>
              <select
                v-model="form.gender"
                class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              >
                <option value="">Select...</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </label>

            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">Date of Birth</span>
              <input
                v-model="form.date_of_birth" type="date"
                class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </label>
          </div>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Address</span>
            <textarea
              v-model="form.address" rows="2" placeholder="Street, city..."
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            ></textarea>
          </label>

          <div>
            <div class="mb-2 border-t border-slate-100 pt-3 text-xs font-semibold uppercase tracking-wide text-slate-400">Emergency Contact</div>
            <div class="grid grid-cols-2 gap-3">
              <label class="block">
                <span class="mb-1 block text-sm font-semibold text-slate-700">Name</span>
                <input
                  v-model="form.emergency_contact_name" type="text" placeholder="e.g. John Doe"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
                />
              </label>
              <label class="block">
                <span class="mb-1 block text-sm font-semibold text-slate-700">Phone</span>
                <input
                  v-model="form.emergency_contact_phone" type="text" placeholder="e.g. 024 987 6543"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
                />
              </label>
            </div>
          </div>

          <div>
            <div class="mb-2 border-t border-slate-100 pt-3 text-xs font-semibold uppercase tracking-wide text-slate-400">Membership</div>
            <div class="grid grid-cols-2 gap-3">
              <label class="block">
                <span class="mb-1 block text-sm font-semibold text-slate-700">Date Joined</span>
                <input
                  v-model="form.date_joined" type="date"
                  class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
                />
              </label>
              <label class="block">
                <span class="mb-1 block text-sm font-semibold text-slate-700">Linked Customer</span>
                <select
                  v-model="form.customer"
                  class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
                >
                  <option value="">Auto-create</option>
                  <option v-for="c in options.customers" :key="c.name" :value="c.name">{{ c.customer_name }}</option>
                </select>
              </label>
            </div>
          </div>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Health Notes</span>
            <textarea
              v-model="form.health_notes" rows="2" placeholder="Injuries, conditions or restrictions (optional, self-reported)"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            ></textarea>
          </label>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
        </form>

        <div class="mt-4 flex shrink-0 items-center gap-2 border-t border-slate-100 pt-4">
          <button
            type="submit" form="create-member-form" :disabled="!isValid || creating"
            class="rounded-lg bg-[var(--gym-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ creating ? 'Creating...' : 'Create Member' }}
          </button>
          <button
            type="button" :disabled="creating"
            class="rounded-lg px-4 py-2 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-200"
            @click="cancel"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';

// Optional: pre-fill the name/mobile fields from whatever the caller had
// already typed into a search box (CheckIn's search, or the New Membership
// member picker) so the front-desk staff member doesn't retype it.
const props = defineProps({ prefillName: { type: String, default: '' } });
const emit = defineEmits(['close', 'created']);

const form = reactive({
  member_name: props.prefillName || '',
  phone: '',
  email: '',
  gender: '',
  date_of_birth: '',
  address: '',
  emergency_contact_name: '',
  emergency_contact_phone: '',
  date_joined: new Date().toISOString().slice(0, 10),
  health_notes: '',
  customer: '',
});
const options = ref({ customers: [] });
const creating = ref(false);
const error = ref('');
const firstField = ref(null);

const isValid = computed(() => form.member_name.trim() && form.phone.trim());

function cancel() {
  if (creating.value) return;
  emit('close');
}

async function loadOptions() {
  try {
    options.value = await call('gym_management.admin_api.get_member_form_options');
  } catch (err) {
    // Non-fatal: Customer is an optional field, so the form still works
    // (just without that one dropdown populated) if this fails.
  }
}

async function submit() {
  if (!isValid.value) return;
  creating.value = true;
  error.value = '';
  try {
    const member = await call('gym_management.admin_api.create_member', {
      member_name: form.member_name.trim(),
      phone: form.phone.trim(),
      email: form.email.trim(),
      gender: form.gender,
      date_of_birth: form.date_of_birth,
      address: form.address.trim(),
      emergency_contact_name: form.emergency_contact_name.trim(),
      emergency_contact_phone: form.emergency_contact_phone.trim(),
      date_joined: form.date_joined,
      health_notes: form.health_notes.trim(),
      customer: form.customer,
    });
    emit('created', member);
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not create this member.';
  } finally {
    creating.value = false;
  }
}

onMounted(() => {
  nextTick(() => firstField.value?.focus());
  loadOptions();
});
</script>
