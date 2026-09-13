<template>
  <!-- Same popup shape as CreateMemberModal.vue - centered card, X close
       top-right, primary+secondary buttons bottom-left. Height auto-sizes
       (no h-[80vh]) since this form is short enough to never need its own
       scrollbar on a normal screen. -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4" @mousedown.self="cancel">
      <div class="flex max-h-[90vh] w-full max-w-md flex-col rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-semibold text-slate-900">Add Body Measurement</h2>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600" @click="cancel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <form id="add-measurement-form" class="flex flex-1 flex-col gap-4 overflow-y-auto pr-1" @submit.prevent="submit">
          <div class="grid grid-cols-2 gap-3">
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">Date<span class="text-red-500">*</span></span>
              <input
                v-model="form.measurement_date" ref="firstField" type="date" required
                class="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">Body Fat %</span>
              <input
                v-model="form.body_fat_percent" type="number" step="0.1" min="0" placeholder="Optional"
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </label>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">Height (cm)<span class="text-red-500">*</span></span>
              <input
                v-model="form.height_cm" type="number" step="0.1" min="0" required placeholder="e.g. 170"
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm font-semibold text-slate-700">Weight (kg)<span class="text-red-500">*</span></span>
              <input
                v-model="form.weight_kg" type="number" step="0.1" min="0" required placeholder="e.g. 68"
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </label>
          </div>
          <p class="-mt-2 text-xs text-slate-400">BMI and weight status are calculated automatically from height and weight.</p>

          <div>
            <div class="mb-2 border-t border-slate-100 pt-3 text-xs font-semibold uppercase tracking-wide text-slate-400">Measurements (cm) - optional</div>
            <div class="grid grid-cols-3 gap-3">
              <label class="block">
                <span class="mb-1 block text-sm font-semibold text-slate-700">Chest</span>
                <input v-model="form.chest_cm" type="number" step="0.1" min="0" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
              </label>
              <label class="block">
                <span class="mb-1 block text-sm font-semibold text-slate-700">Waist</span>
                <input v-model="form.waist_cm" type="number" step="0.1" min="0" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
              </label>
              <label class="block">
                <span class="mb-1 block text-sm font-semibold text-slate-700">Hip</span>
                <input v-model="form.hip_cm" type="number" step="0.1" min="0" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
              </label>
              <label class="block">
                <span class="mb-1 block text-sm font-semibold text-slate-700">Arms</span>
                <input v-model="form.arms_cm" type="number" step="0.1" min="0" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
              </label>
              <label class="block">
                <span class="mb-1 block text-sm font-semibold text-slate-700">Thighs</span>
                <input v-model="form.thighs_cm" type="number" step="0.1" min="0" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" />
              </label>
            </div>
          </div>

          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Notes</span>
            <textarea
              v-model="form.notes" rows="2" placeholder="Optional"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
            ></textarea>
          </label>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
        </form>

        <div class="mt-4 flex shrink-0 items-center gap-2 border-t border-slate-100 pt-4">
          <button
            type="submit" form="add-measurement-form" :disabled="!isValid || saving"
            class="rounded-lg bg-[var(--gym-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ saving ? 'Saving...' : 'Save Measurement' }}
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
import { computed, nextTick, onMounted, reactive, ref } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';

const props = defineProps({ member: { type: String, required: true } });
const emit = defineEmits(['close', 'created']);

const form = reactive({
  measurement_date: new Date().toISOString().slice(0, 10),
  height_cm: '',
  weight_kg: '',
  chest_cm: '',
  waist_cm: '',
  hip_cm: '',
  arms_cm: '',
  thighs_cm: '',
  body_fat_percent: '',
  notes: '',
});
const saving = ref(false);
const error = ref('');
const firstField = ref(null);

const isValid = computed(() => form.measurement_date && form.height_cm !== '' && form.weight_kg !== '');

function cancel() {
  if (saving.value) return;
  emit('close');
}

async function submit() {
  if (!isValid.value) return;
  saving.value = true;
  error.value = '';
  try {
    const doc = await call('gym_management.admin_api.create_body_measurement', {
      member: props.member,
      measurement_date: form.measurement_date,
      height_cm: form.height_cm,
      weight_kg: form.weight_kg,
      chest_cm: form.chest_cm,
      waist_cm: form.waist_cm,
      hip_cm: form.hip_cm,
      arms_cm: form.arms_cm,
      thighs_cm: form.thighs_cm,
      body_fat_percent: form.body_fat_percent,
      notes: form.notes.trim(),
    });
    emit('created', doc);
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not save this measurement.';
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  nextTick(() => firstField.value?.focus());
});
</script>
