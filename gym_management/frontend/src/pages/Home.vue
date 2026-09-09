<template>
  <div class="mx-auto max-w-2xl px-6 py-14">
    <h1 class="text-2xl font-extrabold text-slate-900">Gym Portal</h1>

    <p v-if="!auth.isLoggedIn" class="mt-2 text-slate-500">Sign in to see your membership or trainer dashboard.</p>
    <router-link
      v-if="!auth.isLoggedIn" to="/login"
      class="gp-btn-primary mt-5 inline-block rounded-lg px-4 py-2.5 text-sm font-semibold text-white shadow-sm"
    >
      Sign in
    </router-link>

    <template v-else>
      <p class="mt-2 text-slate-500">Welcome back{{ auth.fullName ? `, ${auth.fullName}` : '' }}.</p>

      <p v-if="!auth.isMember && !auth.isTrainer" class="mt-5 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
        Your account isn't linked to a Gym Member or Trainer profile yet. Ask gym staff to link your login to get access.
      </p>

      <div class="mt-6 flex flex-wrap gap-4">
        <router-link
          v-if="auth.isMember" to="/member"
          class="flex w-64 flex-col gap-1 rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-[var(--portal-primary,#ea580c)]"
        >
          <span class="flex h-9 w-9 items-center justify-center rounded-lg" style="background-color: color-mix(in srgb, var(--portal-primary, #ea580c) 14%, white);">
            <i class="bi bi-person-badge text-[var(--portal-primary,#ea580c)]"></i>
          </span>
          <span class="mt-2 font-semibold text-slate-900">My Membership</span>
          <span class="text-sm text-slate-500">{{ auth.memberName || 'View your membership, attendance, invoices and plans.' }}</span>
        </router-link>

        <router-link
          v-if="auth.isTrainer" to="/trainer"
          class="flex w-64 flex-col gap-1 rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-[var(--portal-primary,#ea580c)]"
        >
          <span class="flex h-9 w-9 items-center justify-center rounded-lg" style="background-color: color-mix(in srgb, var(--portal-primary, #ea580c) 14%, white);">
            <i class="bi bi-clipboard-check text-[var(--portal-primary,#ea580c)]"></i>
          </span>
          <span class="mt-2 font-semibold text-slate-900">Trainer Dashboard</span>
          <span class="text-sm text-slate-500">{{ auth.trainerName || 'View your classes, PT sessions and members.' }}</span>
        </router-link>
      </div>
    </template>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();
</script>

<style scoped>
.gp-btn-primary {
  background-color: var(--portal-primary, #ea580c);
}
.gp-btn-primary:hover {
  background-color: var(--portal-primary-hover, #c2410c);
}
</style>
