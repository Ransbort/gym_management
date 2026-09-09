<template>
  <!-- Ported from POSNext's SessionLockScreen.vue - same blurred-backdrop
       lock card, restyled to this app's own conventions: bi-* Bootstrap
       Icons instead of frappe-ui's FeatherIcon, --gym-accent CSS vars
       instead of blue-600, and auth.logout() for Sign Out instead of
       POSNext's cleanupUserSession()+session.logout.submit(). -->
  <Teleport to="body">
    <Transition name="lock-overlay">
      <div v-if="isLocked" class="fixed inset-0 z-[10000] flex items-center justify-center">
        <div class="absolute inset-0 bg-black/70 backdrop-blur-md"></div>

        <div class="relative z-10 mx-4 w-full max-w-sm">
          <div class="rounded-2xl bg-white p-8 shadow-2xl">
            <div class="mb-5 flex justify-center">
              <div class="flex h-16 w-16 items-center justify-center rounded-full bg-amber-100">
                <i class="bi bi-lock-fill text-2xl text-amber-600"></i>
              </div>
            </div>

            <div class="mb-6 text-center">
              <div class="mb-3 flex justify-center">
                <img
                  v-if="lockedUser?.image" :src="lockedUser.image" :alt="lockedUser.name"
                  class="h-14 w-14 rounded-full border-2 border-slate-200 object-cover"
                />
                <div v-else class="flex h-14 w-14 items-center justify-center rounded-full border-2 border-[var(--gym-accent-hover)] bg-[var(--gym-accent)] text-lg font-bold text-white">
                  {{ lockedUser?.initials || '?' }}
                </div>
              </div>
              <h3 class="text-lg font-bold text-slate-900">{{ lockedUser?.name || 'User' }}</h3>
              <p class="mt-1 text-sm text-slate-500">Session Locked</p>
              <div v-if="isOffline" class="mt-2 inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700">
                <i class="bi bi-wifi-off"></i>
                Offline
              </div>
            </div>

            <form class="space-y-4" @submit.prevent="handleUnlock">
              <div>
                <label class="mb-1.5 block text-sm font-medium text-slate-700">Password</label>
                <div class="relative">
                  <input
                    ref="passwordInputRef" v-model="password" :type="showPassword ? 'text' : 'password'"
                    placeholder="Enter your password" :disabled="isVerifying" autocomplete="current-password"
                    class="block w-full rounded-lg border px-3 py-2.5 pe-10 text-sm transition-colors focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)] disabled:opacity-50"
                    :class="verifyError ? 'border-red-400 bg-red-50' : 'border-slate-300'"
                  />
                  <button
                    type="button" :disabled="isVerifying" tabindex="-1"
                    :aria-label="showPassword ? 'Hide password' : 'Show password'"
                    class="absolute inset-y-0 end-0 flex items-center pe-3 text-slate-500 transition-colors hover:text-slate-700 focus:outline-none"
                    @click="showPassword = !showPassword"
                  >
                    <i :class="['bi', showPassword ? 'bi-eye-slash' : 'bi-eye']"></i>
                  </button>
                </div>
                <p v-if="verifyError" class="mt-1.5 text-sm text-red-600">{{ verifyError }}</p>
              </div>

              <button
                type="submit" :disabled="!password || isVerifying"
                class="w-full rounded-lg bg-[var(--gym-accent)] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-[var(--gym-accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span v-if="isVerifying" class="flex items-center justify-center gap-2">
                  <i class="bi bi-arrow-repeat animate-spin"></i>
                  Verifying...
                </span>
                <span v-else>Unlock</span>
              </button>
            </form>

            <div class="relative my-5">
              <div class="absolute inset-0 flex items-center">
                <div class="w-full border-t border-slate-200"></div>
              </div>
              <div class="relative flex justify-center text-xs">
                <span class="bg-white px-3 text-slate-400">or</span>
              </div>
            </div>

            <button
              :disabled="isVerifying"
              class="w-full rounded-lg bg-slate-100 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-200 disabled:opacity-50"
              @click="handleSignOut"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { useSessionLock } from '@/composables/useSessionLock';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';

const { isLocked, isVerifying, verifyError, lockedUser, unlock } = useSessionLock();
const auth = useAuthStore();
const ui = useUiStore();
// ui.isOnline already exists (see stores/ui.js) and is set from the
// browser's own online/offline events in App.vue.
const isOffline = computed(() => !ui.isOnline);

const password = ref('');
const showPassword = ref(false);
const passwordInputRef = ref(null);

watch(isLocked, async (locked) => {
  if (locked) {
    password.value = '';
    showPassword.value = false;
    await nextTick();
    passwordInputRef.value?.focus();
  }
});

async function handleUnlock() {
  if (!password.value || isVerifying.value) return;
  const result = await unlock(password.value);
  if (result.sessionExpired) {
    // Session expired server-side - a real sign-out is the only honest
    // recovery (matches every other "no longer logged in" path in this
    // app, which all bounce through auth.logout()'s full navigation).
    await auth.logout();
    return;
  }
  if (!result.success) {
    password.value = '';
    await nextTick();
    passwordInputRef.value?.focus();
  }
}

async function handleSignOut() {
  await auth.logout();
}
</script>

<style scoped>
.lock-overlay-enter-active,
.lock-overlay-leave-active {
  transition: opacity 0.3s ease;
}
.lock-overlay-enter-from,
.lock-overlay-leave-to {
  opacity: 0;
}
</style>
