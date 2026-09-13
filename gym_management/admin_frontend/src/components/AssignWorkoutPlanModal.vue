<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4" @mousedown.self="cancel">
      <div class="flex max-h-[90vh] w-full max-w-md flex-col rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-semibold text-slate-900">Assign Workout Plan</h2>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600" @click="cancel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <form id="assign-workout-form" class="flex flex-1 flex-col gap-4 overflow-y-auto pr-1" @submit.prevent="submit">
          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Workout Plan Template</span>
            <select
              v-model="form.workout_plan" ref="firstField"
              class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            >
              <option value="">Custom (no template)</option>
              <option v-for="p in options.workout_plans" :key="p.name" :value="p.name">{{ p.plan_name }}</option>
            </select>
            <span class="mt-1 block text-xs text-slate-400">Copies that template's exercises onto this assignment - fine-tune per-member sets/reps afterward from the full Desk form if needed.</span>
            <button
              type="button"
              class="mt-1 text-xs font-semibold text-[var(--gym-accent)] hover:text-[var(--gym-accent-hover)]"
              @click="showCreateWorkoutPlan = true"
            >
              <i class="bi bi-plus-lg"></i> Create new template
            </button>
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
              <span class="mb-1 block text-sm font-semibold text-slate-700">Duration (weeks)</span>
              <input
                v-model="form.duration_weeks" type="number" min="1" step="1"
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
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
            type="submit" form="assign-workout-form" :disabled="saving"
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

    <CreateWorkoutPlanModal
      v-if="showCreateWorkoutPlan"
      :exercises="options.exercises"
      @close="showCreateWorkoutPlan = false"
      @created="onWorkoutPlanCreated"
    />
  </Teleport>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';
import CreateWorkoutPlanModal from '@/components/CreateWorkoutPlanModal.vue';

const props = defineProps({ member: { type: String, required: true } });
const emit = defineEmits(['close', 'created']);

const form = reactive({
  workout_plan: '',
  assigned_by: '',
  start_date: new Date().toISOString().slice(0, 10),
  duration_weeks: 4,
  status: 'Active',
});
const options = ref({ workout_plans: [], diet_plans: [], trainers: [], exercises: [] });
const saving = ref(false);
const error = ref('');
const firstField = ref(null);
const showCreateWorkoutPlan = ref(false);

function cancel() {
  if (saving.value) return;
  emit('close');
}

function onWorkoutPlanCreated(plan) {
  showCreateWorkoutPlan.value = false;
  // Newly created, so it isn't in the options.workout_plans list this modal
  // already fetched at mount - add it in place and select it, same pattern
  // NewMembershipModal.vue uses for a newly-created member.
  options.value.workout_plans = [...options.value.workout_plans, plan];
  form.workout_plan = plan.name;
}

async function loadOptions() {
  try {
    options.value = await call('gym_management.admin_api.get_fitness_form_options');
  } catch (err) {
    // Non-fatal: both dropdowns are optional (a plan can be assigned as
    // "Custom" and left unassigned to a trainer), so the form still works.
  }
}

async function submit() {
  saving.value = true;
  error.value = '';
  try {
    const doc = await call('gym_management.admin_api.create_assigned_workout_plan', {
      member: props.member,
      workout_plan: form.workout_plan,
      assigned_by: form.assigned_by,
      start_date: form.start_date,
      duration_weeks: form.duration_weeks,
      status: form.status,
    });
    emit('created', doc);
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not assign this workout plan.';
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  nextTick(() => firstField.value?.focus());
  loadOptions();
});
</script>
