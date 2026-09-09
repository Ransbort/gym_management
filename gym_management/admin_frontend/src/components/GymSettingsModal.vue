<template>
  <!-- Same popup convention as CreateMemberModal.vue/NewMembershipModal.vue
       (Teleport to body, title + X close, red-asterisk-free since nothing
       here is required) - opened from Sidebar's gear icon instead of
       navigating out to the Desk form for the handful of settings that are
       worth a quick in-dashboard edit. Starts with just Theme Color; more
       of Gym Settings can move in here later the same way. -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4" @mousedown.self="cancel">
      <div class="flex w-full max-w-md flex-col rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex shrink-0 items-center justify-between border-b border-slate-100 pb-3">
          <h2 class="text-base font-semibold text-slate-900">Gym Settings</h2>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600" @click="cancel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <div v-if="loading" class="py-6 text-center text-sm text-slate-500">Loading...</div>
        <form v-else id="gym-settings-form" class="flex flex-col gap-4" @submit.prevent="submit">
          <label class="block">
            <span class="mb-1 block text-sm font-semibold text-slate-700">Theme Color</span>
            <span class="mb-2 block text-xs text-slate-500">Used for buttons, links and highlights across the dashboard.</span>
            <div class="flex items-center gap-2">
              <input
                v-model="form.theme_color" type="color"
                class="h-10 w-12 shrink-0 cursor-pointer rounded-lg border border-slate-300 bg-white p-1"
              />
              <input
                v-model="form.theme_color" type="text" placeholder="#4f46e5" pattern="^#[0-9a-fA-F]{6}$"
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              />
            </div>
          </label>

          <div>
            <label class="flex items-start gap-2">
              <input v-model="form.enable_paystack_payments" type="checkbox" class="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-[var(--gym-accent)] focus:ring-[var(--gym-accent-ring)]" />
              <span>
                <span class="block text-sm font-semibold text-slate-700">Enable Paystack Payments</span>
                <span class="block text-xs text-slate-500">Lets staff generate a Paystack payment link from Memberships. Also requires a matching, enabled Paystack Gateway Setting record for the company.</span>
              </span>
            </label>

            <label v-if="form.enable_paystack_payments" class="mt-2 block pl-6">
              <span class="mb-1 block text-xs font-semibold text-slate-700">Default Payment Gateway</span>
              <select
                v-model="form.default_payment_gateway"
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
              >
                <option value="">Select...</option>
                <option v-for="g in options.payment_gateways" :key="g.name" :value="g.name">{{ g.name }}</option>
              </select>
            </label>
          </div>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
          <p v-if="saved" class="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">Saved.</p>
        </form>

        <div class="mt-4 flex shrink-0 items-center gap-2 border-t border-slate-100 pt-4">
          <button
            type="submit" form="gym-settings-form" :disabled="loading || saving"
            class="rounded-lg bg-[var(--gym-accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ saving ? 'Saving...' : 'Save' }}
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
import { onMounted, reactive, ref } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';
import { useAuthStore } from '@/stores/auth';
import { applyTheme } from '@/theme';

const emit = defineEmits(['close']);
const auth = useAuthStore();

const form = reactive({ theme_color: auth.themeColor, enable_paystack_payments: false, default_payment_gateway: '' });
const options = ref({ payment_gateways: [] });
const loading = ref(true);
const saving = ref(false);
const error = ref('');
const saved = ref(false);

function cancel() {
  if (saving.value) return;
  emit('close');
}

async function load() {
  loading.value = true;
  try {
    const settings = await call('gym_management.admin_api.get_gym_settings');
    form.theme_color = settings.theme_color;
    form.enable_paystack_payments = !!settings.enable_paystack_payments;
    form.default_payment_gateway = settings.default_payment_gateway || '';
    options.value.payment_gateways = settings.payment_gateways || [];
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not load Gym Settings.';
  } finally {
    loading.value = false;
  }
}

async function submit() {
  saving.value = true;
  error.value = '';
  saved.value = false;
  try {
    const result = await call('gym_management.admin_api.update_gym_settings', {
      theme_color: form.theme_color,
      enable_paystack_payments: form.enable_paystack_payments ? 1 : 0,
      default_payment_gateway: form.default_payment_gateway,
    });
    // Live-apply immediately (window.adminBoot itself only refreshes on the
    // next full page load) so the color change is visible the instant this
    // popup closes, same idea as theme.js's own pre-mount applyTheme() call.
    auth.themeColor = result.theme_color;
    applyTheme(result.theme_color);
    saved.value = true;
    setTimeout(() => emit('close'), 600);
  } catch (err) {
    error.value = firstServerMessage(err) || 'Could not save Gym Settings.';
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>
