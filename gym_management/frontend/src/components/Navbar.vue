<template>
  <nav v-if="!ui.navbarHidden" class="shrink-0 z-20 border-b border-slate-900/5 bg-white px-6 py-5">
    <div class="mx-auto flex max-w-6xl items-center justify-between">
      <router-link to="/" class="flex items-center gap-2.5 shrink-0" @click="closeMenu">
        <span
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
          style="background-color: color-mix(in srgb, var(--portal-primary, #ea580c) 14%, white);"
        >
          <i class="bi bi-lightning-charge-fill text-[var(--portal-primary,#ea580c)]"></i>
        </span>
        <span class="font-extrabold leading-tight text-slate-900">Gym Portal</span>
      </router-link>

      <button
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white p-0 text-slate-700 shadow-sm hover:bg-slate-50"
        aria-label="Open menu"
        aria-haspopup="true"
        :aria-expanded="ui.menuOpen"
        @click="ui.openMenu()"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
          <path d="M4 5h16"/>
          <path d="M4 12h16"/>
          <path d="M4 19h16"/>
        </svg>
      </button>
    </div>
  </nav>

  <Teleport to="body">
    <Transition name="gp-fade">
      <div v-if="ui.menuOpen" class="fixed inset-0 z-30 bg-slate-900/40" @click="closeMenu"></div>
    </Transition>

    <Transition name="gp-slide">
      <aside
        v-if="ui.menuOpen"
        class="fixed inset-y-0 right-0 z-40 flex w-72 max-w-[85vw] flex-col bg-white shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-label="Navigation"
      >
        <div class="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <span class="flex items-center gap-2 font-extrabold text-slate-900">
            <i class="bi bi-lightning-charge-fill text-[var(--portal-primary,#ea580c)]"></i>
            Gym Portal
          </span>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg border-0 bg-transparent p-0 text-[var(--portal-primary,#ea580c)] hover:bg-slate-100"
            aria-label="Close menu"
            @click="closeMenu"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
              <path d="M18 6 6 18"/>
              <path d="m6 6 12 12"/>
            </svg>
          </button>
        </div>

        <nav class="flex flex-1 flex-col gap-0.5 overflow-y-auto px-3 py-4 text-sm font-semibold text-slate-600">
          <router-link
            to="/" class="rounded-lg px-3 py-2.5 hover:bg-slate-50 hover:text-[var(--portal-primary,#ea580c)]"
            active-class="bg-slate-50 text-[var(--portal-primary,#ea580c)]" @click="closeMenu"
          >
            <i class="bi bi-house mr-2"></i>Home
          </router-link>
          <router-link
            v-if="auth.isMember"
            to="/member" class="rounded-lg px-3 py-2.5 hover:bg-slate-50 hover:text-[var(--portal-primary,#ea580c)]"
            active-class="bg-slate-50 text-[var(--portal-primary,#ea580c)]" @click="closeMenu"
          >
            <i class="bi bi-person-badge mr-2"></i>My Membership
          </router-link>
          <router-link
            v-if="auth.isTrainer"
            to="/trainer" class="rounded-lg px-3 py-2.5 hover:bg-slate-50 hover:text-[var(--portal-primary,#ea580c)]"
            active-class="bg-slate-50 text-[var(--portal-primary,#ea580c)]" @click="closeMenu"
          >
            <i class="bi bi-clipboard-check mr-2"></i>Trainer Dashboard
          </router-link>
        </nav>

        <div class="border-t border-slate-200 px-4 py-3.5">
          <template v-if="auth.isLoggedIn">
            <div class="mb-2.5 truncate text-sm text-slate-500">{{ auth.fullName || auth.user }}</div>
            <button
              type="button"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
              @click="handleSignOut"
            >
              Sign out
            </button>
          </template>
          <router-link
            v-else to="/login"
            class="gp-signin-btn block rounded-lg px-3 py-2 text-center text-sm font-semibold text-white shadow-sm"
            @click="closeMenu"
          >
            Sign in
          </router-link>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';

const auth = useAuthStore();
const ui = useUiStore();
const route = useRoute();

function closeMenu() {
  ui.closeMenu();
}

function handleSignOut() {
  closeMenu();
  auth.logout();
}

watch(() => route.fullPath, closeMenu);

function handleKeydown(e) {
  if (e.key === 'Escape') closeMenu();
}
watch(() => ui.menuOpen, (open) => {
  document.documentElement.classList.toggle('gp-menu-open', open);
  if (open) {
    window.addEventListener('keydown', handleKeydown);
  } else {
    window.removeEventListener('keydown', handleKeydown);
  }
});
onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown);
  document.documentElement.classList.remove('gp-menu-open');
});
</script>

<style scoped>
.gp-signin-btn {
  background-color: var(--portal-primary, #ea580c);
}
.gp-signin-btn:hover {
  background-color: var(--portal-primary-hover, #c2410c);
}

.gp-fade-enter-active,
.gp-fade-leave-active {
  transition: opacity 0.2s ease;
}
.gp-fade-enter-from,
.gp-fade-leave-to {
  opacity: 0;
}

.gp-slide-enter-active,
.gp-slide-leave-active {
  transition: transform 0.25s ease;
}
.gp-slide-enter-from,
.gp-slide-leave-to {
  transform: translateX(100%);
}
</style>

<style>
html.gp-menu-open,
html.gp-menu-open body {
  overflow: hidden;
}
</style>
