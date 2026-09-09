<template>
  <header class="flex shrink-0 items-center justify-between border-b border-slate-200 bg-white p-6 text-slate-900 shadow-sm">
    <div class="flex items-center gap-2.5">
      <img v-if="auth.gymLogo" :src="auth.gymLogo" alt="" class="h-12 shrink-0" />
      <span v-else class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--gym-accent)] text-sm font-bold text-white">{{ brandInitials }}</span>
      <div class="leading-tight">
        <div class="text-sm font-bold text-slate-900">{{ auth.gymName || 'Gym Admin' }}</div>
        <div class="text-[11px] text-slate-500">{{ auth.siteName }}</div>
      </div>
    </div>

    <div class="flex items-center gap-3">
      <span class="hidden items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 sm:flex">
        <i class="bi bi-clock"></i>{{ clock }}
      </span>

      <span
        class="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
        :class="ui.isOnline ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'"
      >
        <i :class="['bi', ui.isOnline ? 'bi-wifi' : 'bi-wifi-off']"></i>
        {{ ui.isOnline ? 'Online' : 'Offline' }}
      </span>

      <!-- Global refresh - moved here from Overview's own page header so
           any page can be refreshed from one place; pages that have data
           to reload watch ui.refreshKey (see stores/ui.js). -->
      <button
        type="button" title="Refresh"
        class="flex h-8 w-8 items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-slate-200 hover:text-slate-700"
        @click="refresh"
      >
        <i class="bi bi-arrow-clockwise" :class="{ 'animate-spin': spinning }"></i>
      </button>

      <div ref="menuRoot" class="relative">
        <button
          class="flex items-center gap-2 rounded-lg px-2 py-1.5 transition-colors hover:bg-slate-200"
          @click="menuOpen = !menuOpen"
        >
          <img v-if="auth.userImage" :src="auth.userImage" alt="" class="h-7 w-7 shrink-0 rounded-full object-cover" />
          <span v-else class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--gym-accent)] text-xs font-bold text-white">{{ initials }}</span>
          <span class="text-sm font-medium text-slate-700">{{ auth.fullName || auth.user }}</span>
          <i class="bi bi-chevron-down text-xs text-slate-400"></i>
        </button>

        <!-- User menu - same card shape POSNext uses for its own account
             dropdown (avatar+name header, icon rows, a divider, red
             sign-out row at the bottom). Only real, working actions are
             listed - no shift/invoice rows like POSNext's own, since
             gym_management has no shift or invoice concept (yet - see
             this component's own extension note below). -->
        <div
          v-if="menuOpen"
          class="absolute right-0 top-full z-50 mt-2 w-60 overflow-hidden rounded-2xl border border-slate-200 bg-white text-slate-700 shadow-xl"
        >
          <div class="flex items-center gap-3 border-b border-slate-100 px-4 py-3.5">
            <img v-if="auth.userImage" :src="auth.userImage" alt="" class="h-10 w-10 shrink-0 rounded-full object-cover" />
            <span v-else class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--gym-accent)] text-sm font-bold text-white">{{ initials }}</span>
            <div class="min-w-0 leading-tight">
              <div class="truncate text-sm font-semibold text-slate-900">{{ auth.fullName || auth.user }}</div>
              <div class="truncate text-xs text-slate-500">{{ auth.siteName }}</div>
            </div>
          </div>

          <div class="py-1.5">
            <a
              href="/me" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-slate-50"
              @click="menuOpen = false"
            >
              <span class="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--gym-accent-tint)] text-[var(--gym-accent)]">
                <i class="bi bi-person-circle"></i>
              </span>
              My Account
            </a>
          </div>

          <div class="border-t border-slate-100 py-1.5">
            <button class="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50" @click="auth.logout">
              <span class="flex h-7 w-7 items-center justify-center rounded-full bg-red-50 text-red-500">
                <i class="bi bi-box-arrow-right"></i>
              </span>
              Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';

const auth = useAuthStore();
const ui = useUiStore();
const menuOpen = ref(false);
const menuRoot = ref(null);
const clock = ref(formatClock());
const spinning = ref(false);
let clockTimer = null;

// One clean full turn (Tailwind's animate-spin is 1s/rotation, linear) per
// click, independent of how long each page's own reload actually takes -
// there's no single shared "is anything loading" flag across pages to tie
// this to (see ui.refreshKey in stores/ui.js), and a one-shot spin still
// reads clearly as "refresh happened" without needing one.
function refresh() {
  ui.triggerRefresh();
  spinning.value = true;
  setTimeout(() => { spinning.value = false; }, 1000);
}

const initials = computed(() => {
  const name = auth.fullName || auth.user || '';
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '?';
  return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : parts[0].slice(0, 2).toUpperCase();
});

// Fallback badge (used only when Gym Settings has no logo uploaded yet) -
// same "first letter of each word" treatment as `initials` above, but for
// the gym's own name rather than the signed-in user's.
const brandInitials = computed(() => {
  const name = auth.gymName || 'Gym Admin';
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return 'GA';
  return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : parts[0].slice(0, 2).toUpperCase();
});

function formatClock() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function handleOutsideClick(event) {
  if (menuOpen.value && menuRoot.value && !menuRoot.value.contains(event.target)) {
    menuOpen.value = false;
  }
}

onMounted(() => {
  clockTimer = setInterval(() => { clock.value = formatClock(); }, 1000);
  window.addEventListener('click', handleOutsideClick);
});
onUnmounted(() => {
  clearInterval(clockTimer);
  window.removeEventListener('click', handleOutsideClick);
});
</script>
