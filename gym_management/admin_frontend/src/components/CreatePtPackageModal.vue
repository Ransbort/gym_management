<template>
  <!-- Same popup convention as CreateWorkoutPlanModal.vue - opened from the
       "Create new package" link on NewPtPurchaseModal so a Gym Manager can
       define a reusable PT Package without leaving the dashboard for the
       full Desk form. -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[110] flex items-center justify-center bg-black/40 p-4" @mousedown.self="cancel">
      <div class="flex w-full max-w-md flex-col rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-semibold text-slate-900">Create PT Package</h2>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600" @click="cancel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <form id="create-pt-package-form" class="flex flex-col gap-4" @submit.prevent="submit">
          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Package Name<span class="text-red-500">*</span></span>
            <input
              v-model="form.package_name" ref="firstField" type="text" required placeholder="e.g. 10-Session Starter Pack"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            />
          </label>

          <div class="grid grid-cols-2 gap-3">
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">No. of Sessions<span class="text-red-500">*</span></span>
              <input
                v-model="form.no_of_sessions" type="number" min="1" step="1" required
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">Validity (days)</span>
              <input
                v-model="form.validity_days" type="number" min="1" step="1"
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </label>
          </div>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Price<span class="text-red-500">*</span></span>
            <input
              v-model="form.price" type="number" min="0" step="0.01" required
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            />
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Description</span>
            <textarea
              v-model="form.description" rows="2" placeholder="Optional notes about what this package includes"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            ></textarea>
          </label>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
        </form>

        <div class="mt-4 flex shrink-0 items-center gap-2 border-t border-slate-100 pt-4">
          <button
            type="submit" form="create-pt-package-form" :disabled="!isValid || creating"
            class="rounded-lg bg-[var(--gym-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ creating ? 'Creating...' : 'Create Package' }}
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

const emit = defineEmits(['close', 'created']);

const form = reactive({
  package_name: '',
  no_of_sessions: 10,
  validity_days: 90,
  price: '',
  description: '',
});
const creating = ref(false);
const error = ref('');
const firstField = ref(null);

const isValid = computed(() => form.package_name.trim() && Number(form.no_of_sessions) > 0 && form.price !== '');

function cancel() {
  if (creating.value) return;
  emit('close');
}

async function submit() {
  if (!isValid.value) return;
  creating.value = true;
  error.value = '';
  try {
    const pkg = await call('gym_management.admin_api.create_pt_package', {
      package_name: form.package_name.trim(),
      no_of_sessions: form.no_of_sessions,
      validity_days: form.validity_days,
      price: form.price,
      description: form.description.trim(),
    });
    emit('created', pkg);
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not create this package.';
  } finally {
    creating.value = false;
  }
}

onMounted(() => {
  nextTick(() => firstField.value?.focus());
});
</script>
