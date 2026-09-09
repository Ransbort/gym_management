<template>
  <div class="flex h-full items-center justify-center bg-slate-50 px-6">
    <div class="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl">
      <div class="mb-6 flex items-center gap-3">
        <img v-if="auth.gymLogo" :src="auth.gymLogo" alt="" class="h-10 w-10 shrink-0 rounded-xl object-cover" />
        <span v-else class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--gym-accent)] text-base font-bold text-white">{{ brandInitials }}</span>
        <div>
          <h1 class="text-lg font-bold text-slate-900">{{ auth.gymName || 'Gym Admin' }}</h1>
          <p class="text-xs text-slate-500">Staff sign in</p>
        </div>
      </div>

      <form class="flex flex-col gap-4" @submit.prevent="submit">
        <div>
          <label class="mb-1 block text-sm font-semibold text-slate-700" for="usr">Email</label>
          <input
            id="usr" v-model="usr" type="email" autocomplete="username" required
            class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
          />
        </div>
        <div>
          <label class="mb-1 block text-sm font-semibold text-slate-700" for="pwd">Password</label>
          <input
            id="pwd" v-model="pwd" type="password" autocomplete="current-password" required
            class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]"
          />
        </div>

        <p v-if="auth.loginError" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ auth.loginError }}</p>

        <button
          type="submit" :disabled="auth.loggingIn"
          class="rounded-lg bg-[var(--gym-accent)] px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-[var(--gym-accent-hover)] disabled:opacity-60"
        >
          {{ auth.loggingIn ? 'Signing in...' : 'Sign in' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();
const route = useRoute();
const usr = ref('');
const pwd = ref('');

const brandInitials = computed(() => {
  const name = auth.gymName || 'Gym Admin';
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return 'GA';
  return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : parts[0].slice(0, 2).toUpperCase();
});

function submit() {
  const redirect = route.query.redirect ? `/gym-admin${route.query.redirect}` : '/gym-admin';
  auth.login(usr.value, pwd.value, redirect);
}
</script>
