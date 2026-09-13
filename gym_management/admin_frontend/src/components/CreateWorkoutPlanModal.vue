<template>
  <!-- Same popup convention as CreateMemberModal.vue - opened from the
       "Create new template" link on AssignWorkoutPlanModal so a Gym Manager
       (or Gym Trainer) can define a reusable Workout Plan without leaving
       the dashboard for the full Desk form. Exercise rows are optional and
       can be filled in later from Desk - a template with no rows yet is
       still a valid, nameable plan. -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[110] flex items-center justify-center bg-black/40 p-4" @mousedown.self="cancel">
      <div class="flex h-[80vh] w-full max-w-lg flex-col rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-semibold text-slate-900">Create Workout Plan</h2>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600" @click="cancel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <form id="create-workout-plan-form" class="flex flex-1 flex-col gap-4 overflow-y-auto pr-1" @submit.prevent="submit">
          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Plan Name<span class="text-red-500">*</span></span>
            <input
              v-model="form.plan_name" ref="firstField" type="text" required placeholder="e.g. Beginner Strength Split"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            />
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Goal</span>
            <select
              v-model="form.goal"
              class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            >
              <option value="">Select...</option>
              <option v-for="g in GOALS" :key="g" :value="g">{{ g }}</option>
            </select>
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Description</span>
            <textarea
              v-model="form.description" rows="2" placeholder="Optional notes about who this plan suits"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            ></textarea>
          </label>

          <div>
            <div class="mb-2 flex items-center justify-between border-t border-slate-100 pt-3">
              <span class="text-xs font-semibold uppercase tracking-wide text-slate-400">Exercises</span>
              <button
                type="button"
                class="text-xs font-semibold text-[var(--gym-accent)] hover:text-[var(--gym-accent-hover)]"
                @click="addRow"
              >
                <i class="bi bi-plus-lg"></i> Add exercise
              </button>
            </div>

            <p v-if="!form.exercises.length" class="text-xs text-slate-400">
              No exercises yet - add some now or fine-tune this template later from the full Desk form.
            </p>

            <div v-for="(row, idx) in form.exercises" :key="idx" class="mb-2 rounded-lg border border-slate-200 p-3">
              <div class="mb-2 flex items-center justify-between">
                <select
                  v-model="row.exercise"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
                >
                  <option value="" disabled>Select an exercise...</option>
                  <option v-for="e in exercises" :key="e.name" :value="e.name">{{ e.exercise_name }}</option>
                </select>
                <button
                  type="button"
                  class="ml-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-red-600"
                  @click="removeRow(idx)"
                >
                  <i class="bi bi-trash"></i>
                </button>
              </div>
              <div class="grid grid-cols-3 gap-2">
                <label class="block">
                  <span class="mb-1 block text-xs font-semibold text-slate-700">Sets</span>
                  <input
                    v-model="row.sets" type="number" min="1" step="1"
                    class="w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
                  />
                </label>
                <label class="block">
                  <span class="mb-1 block text-xs font-semibold text-slate-700">Reps</span>
                  <input
                    v-model="row.reps" type="text" placeholder="8-12"
                    class="w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
                  />
                </label>
                <label class="block">
                  <span class="mb-1 block text-xs font-semibold text-slate-700">Rest (sec)</span>
                  <input
                    v-model="row.rest_seconds" type="number" min="0" step="5"
                    class="w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
                  />
                </label>
              </div>
            </div>
          </div>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
        </form>

        <div class="mt-4 flex shrink-0 items-center gap-2 border-t border-slate-100 pt-4">
          <button
            type="submit" form="create-workout-plan-form" :disabled="!form.plan_name.trim() || creating"
            class="rounded-lg bg-[var(--gym-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ creating ? 'Creating...' : 'Create Plan' }}
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
import { nextTick, onMounted, reactive, ref } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';

// Exercise options are already fetched by the parent (AssignWorkoutPlanModal
// loads get_fitness_form_options for its own Trainer/Workout Plan dropdowns)
// so this just reuses that list instead of firing a second, identical call.
const props = defineProps({ exercises: { type: Array, default: () => [] } });
const emit = defineEmits(['close', 'created']);

// Mirrors Workout Plan's own Goal Select options in generate.py.
const GOALS = ['Weight Loss', 'Muscle Gain', 'Endurance', 'General Fitness', 'Rehabilitation'];

const form = reactive({
  plan_name: '',
  goal: '',
  description: '',
  exercises: [],
});
const creating = ref(false);
const error = ref('');
const firstField = ref(null);

function addRow() {
  form.exercises.push({ exercise: '', sets: 3, reps: '8-12', rest_seconds: 60 });
}
function removeRow(idx) {
  form.exercises.splice(idx, 1);
}

function cancel() {
  if (creating.value) return;
  emit('close');
}

async function submit() {
  if (!form.plan_name.trim()) return;
  creating.value = true;
  error.value = '';
  try {
    const plan = await call('gym_management.admin_api.create_workout_plan', {
      plan_name: form.plan_name.trim(),
      goal: form.goal,
      description: form.description.trim(),
      exercises: form.exercises.filter((r) => r.exercise),
    });
    emit('created', plan);
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not create this workout plan.';
  } finally {
    creating.value = false;
  }
}

onMounted(() => {
  nextTick(() => firstField.value?.focus());
});
</script>
