<template>
  <div class="flex h-full w-full flex-col bg-slate-50 text-slate-900">
    <TopBar v-if="showShell" />
    <div class="flex min-h-0 flex-1">
      <Sidebar v-if="showShell" />
      <main class="min-w-0 flex-1 overflow-hidden">
        <router-view />
      </main>
    </div>
    <SessionLockScreen v-if="auth.isLoggedIn" />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import TopBar from '@/components/TopBar.vue';
import Sidebar from '@/components/Sidebar.vue';
import SessionLockScreen from '@/components/SessionLockScreen.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { flushPendingActions } from '@/offline/sync';
import { initSocket } from '@/socket';
import { useSessionLock } from '@/composables/useSessionLock';

const route = useRoute();
const auth = useAuthStore();
const ui = useUiStore();
const { configure, startActivityTracking, stopActivityTracking } = useSessionLock();

// The Login page renders its own full-screen layout - the header/sidebar
// chrome only makes sense once there's somewhere for it to navigate to.
const showShell = computed(() => route.name !== 'Login' && auth.isLoggedIn);

onMounted(() => {
  window.addEventListener('online', () => ui.setOnline(true));
  window.addEventListener('offline', () => ui.setOnline(false));

  if (auth.isLoggedIn) {
    initSocket();
    if (navigator.onLine) flushPendingActions();
    configure({ enabled: auth.enableSessionLock, timeoutMinutes: auth.sessionLockTimeout });
    startActivityTracking();
  }
});
onUnmounted(() => {
  stopActivityTracking();
});
// Gym Settings' Security section can change enable_session_lock /
// session_lock_timeout underneath a session that's already open (e.g. via
// the Gym Settings popup, which patches these two auth store fields
// directly on save) - re-apply whenever they change rather than only
// reading them once here.
watch(
  () => [auth.enableSessionLock, auth.sessionLockTimeout],
  ([enabled, timeoutMinutes]) => {
    if (!auth.isLoggedIn) return;
    configure({ enabled, timeoutMinutes });
    if (enabled) startActivityTracking();
  },
);
</script>
