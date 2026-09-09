<template>
  <div class="mx-auto flex max-w-md flex-col gap-6 px-6 py-14">
    <div>
      <h1 class="text-2xl font-extrabold text-slate-900">Sign in</h1>
      <p class="mt-1 text-sm text-slate-500">Use your gym login to reach your membership or trainer dashboard.</p>
    </div>

    <form class="flex flex-col gap-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-sm font-semibold text-slate-700" for="usr">Email</label>
        <input
          id="usr" v-model="usr" type="email" autocomplete="username" required
          class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-[var(--portal-primary,#ea580c)] focus:outline-none focus:ring-2 focus:ring-[color-mix(in_srgb,var(--portal-primary,#ea580c)_25%,white)]"
        />
      </div>
      <div>
        <label class="mb-1 block text-sm font-semibold text-slate-700" for="pwd">Password</label>
        <input
          id="pwd" v-model="pwd" type="password" autocomplete="current-password" required
          class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-[var(--portal-primary,#ea580c)] focus:outline-none focus:ring-2 focus:ring-[color-mix(in_srgb,var(--portal-primary,#ea580c)_25%,white)]"
        />
      </div>

      <p v-if="auth.loginError" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ auth.loginError }}</p>

      <button
        type="submit" :disabled="auth.loggingIn"
        class="gp-submit-btn rounded-lg px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:opacity-60"
      >
        {{ auth.loggingIn ? 'Signing in...' : 'Sign in' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();
const route = useRoute();
const usr = ref('');
const pwd = ref('');

function submit() {
  const redirect = route.query.redirect ? `/gym-portal${route.query.redirect}` : '/gym-portal';
  auth.login(usr.value, pwd.value, redirect);
}
</script>

<style scoped>
.gp-submit-btn {
  background-color: var(--portal-primary, #ea580c);
}
.gp-submit-btn:hover:not(:disabled) {
  background-color: var(--portal-primary-hover, #c2410c);
}
</style>
