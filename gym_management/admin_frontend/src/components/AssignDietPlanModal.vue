<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4" @mousedown.self="cancel">
      <div class="flex max-h-[90vh] w-full max-w-md flex-col rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-semibold text-slate-900">Assign Diet Plan</h2>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600" @click="cancel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <form id="assign-diet-form" class="flex flex-1 flex-col gap-4 overflow-y-auto pr-1" @submit.prevent="submit">
          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Diet Plan Template</span>
            <select
              v-model="form.diet_plan" ref="firstField"
              class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            >
              <option value="">Custom (no template)</option>
              <option v-for="p in options.diet_plans" :key="p.name" :value="p.name">{{ p.plan_name }}</option>
            </select>
            <span class="mt-1 block text-xs text-slate-400">Copies that template's meals onto this assignment - fine-tune per-member portions afterward from the full Desk form if needed.</span>
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Trainer</span>
            <select
              v-model="form.assigned_by"
              class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            >
              <option value="">Unassigned</option>
              <option v-for="t in options.trainers" :key="t.name" :value="t.name">{{ t.trainer_name }}</option>
            </select>
          </label>

          <div class="grid grid-cols-2 gap-3">
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">Start Date</span>
              <input
                v-model="form.start_date" type="date"
                class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">End Date</span>
              <input
                v-model="form.end_date" type="date" placeholder="Optional"
                class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </label>
          </div>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Status</span>
            <select
              v-model="form.status"
              class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            >
              <option value="Active">Active</option>
              <option value="Completed">Completed</option>
              <option value="Discontinued">Discontinued</option>
            </select>
          </label>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
        </form>

        <div class="mt-4 flex shrink-0 items-center gap-2 border-t border-slate-100 pt-4">
          <button
            type="submit" form="assign-diet-form" :disabled="saving"
            class="rounded-lg bg-[var(--gym-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ saving ? 'Assigning...' : 'Assign Plan' }}
          </button>
          <button
            type="button" :disabled="saving"
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
import { nextTick, onMounted, reactive, ref } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';

const props = defineProps({ member: { type: String, required: true } });
const emit = defineEmits(['close', 'created']);

const form = reactive({
  diet_plan: '',
  assigned_by: '',
  start_date: new Date().toISOString().slice(0, 10),
  end_date: '',
  status: 'Active',
});
const options = ref({ workout_plans: [], diet_plans: [], trainers: [] });
const saving = ref(false);
const error = ref('');
const firstField = ref(null);

function cancel() {
  if (saving.value) return;
  emit('close');
}

async function loadOptions() {
  try {
    options.value = await call('gym_management.admin_api.get_fitness_form_options');
  } catch (err) {
    // Non-fatal: both dropdowns are optional.
  }
}

async function submit() {
  saving.value = true;
  error.value = '';
  try {
    const doc = await call('gym_management.admin_api.create_assigned_diet_plan', {
      member: props.member,
      diet_plan: form.diet_plan,
      assigned_by: form.assigned_by,
      start_date: form.start_date,
      end_date: form.end_date,
      status: form.status,
    });
    emit('created', doc);
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not assign this diet plan.';
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  nextTick(() => firstField.value?.focus());
  loadOptions();
});
</script>
