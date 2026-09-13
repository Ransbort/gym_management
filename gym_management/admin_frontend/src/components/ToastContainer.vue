<template>
  <!-- Single global toast stack, mounted once in App.vue next to
       SessionLockScreen so it overlays every route (shell or not). Pages
       push into it via useUiStore().showToast(message, type) instead of
       each maintaining its own flash/showFlash()/inline-banner copy. -->
  <Teleport to="body">
    <!-- top-24 (not top-4): TopBar sits in normal document flow at the very
         top of the page and is ~96px tall at most (p-6 + up to a h-12
         logo), with its own right-aligned account menu in that same band.
         A toast fixed at top-4 landed in that exact band - right on top of
         the account menu - and even though it renders above it (z-[200] >
         the menu's z-50), the two are easy to misread as one overlapping
         mess. Sitting below the header entirely avoids that regardless of
         z-index. -->
    <div class="pointer-events-none fixed right-4 top-24 z-[200] flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2">
      <TransitionGroup name="toast">
        <div
          v-for="t in ui.toasts"
          :key="t.id"
          :class="['pointer-events-auto flex items-start gap-2 rounded-lg border px-3 py-2.5 text-sm shadow-xl ring-1', styles[t.type] || styles.success]"
          :style="{ backgroundColor: '#ffffff' }"
        >
          <i :class="['bi shrink-0 pt-0.5', iconFor(t.type)]"></i>
          <span class="flex-1">{{ t.message }}</span>
          <button
            type="button"
            class="shrink-0 rounded p-0.5 opacity-60 transition-opacity hover:opacity-100"
            title="Dismiss"
            @click="ui.dismissToast(t.id)"
          >
            <i class="bi bi-x-lg text-xs"></i>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

// Same emerald/red/amber semantic pairing used everywhere else in the
// dashboard (status pills, offline banners) - never the runtime
// --gym-accent tokens, which are brand color, not success/error/warning.
//
// Explicit solid `bg-white` (not just the -50 tint) plus a matching border:
// the toast is teleported to <body> and fixed top-right, right where
// TopBar's own account menu sits, and TopBar's background is white too -
// with only a pale -50 tint and no border, the toast had no visible edge
// against it and looked like it had no background at all.
const styles = {
  success: 'bg-white border-emerald-200 text-emerald-700 ring-emerald-100',
  error: 'bg-white border-red-200 text-red-700 ring-red-100',
  warning: 'bg-white border-amber-200 text-amber-700 ring-amber-100',
};

function iconFor(type) {
  if (type === 'error') return 'bi-x-circle-fill';
  if (type === 'warning') return 'bi-exclamation-triangle-fill';
  return 'bi-check-circle-fill';
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(1rem);
}
.toast-leave-active {
  position: absolute;
  width: 100%;
}
</style>
