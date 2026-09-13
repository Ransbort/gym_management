import { defineStore } from 'pinia';

let nextToastId = 1;

// Small piece of shared UI state: a live online/offline flag the whole
// shell (TopBar's status pill, and the offline queue in offline/sync.js)
// can read.
export const useUiStore = defineStore('ui', {
  state: () => ({
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    // Bumped by TopBar's header refresh icon; pages that have their own
    // data to reload watch this and re-run their own load() function, so
    // one button in the shell can refresh whichever page is on screen
    // without every page needing its own refresh control.
    refreshKey: 0,
    // Toast notifications, rendered by the single <ToastContainer /> in
    // App.vue - was previously a `flash`/`flashError`/showFlash() ref pair
    // duplicated per-page as an inline banner; centralizing it here means
    // every page calls the same showToast() and gets the same floating,
    // auto-dismissing notification instead of maintaining its own copy.
    toasts: [],
  }),
  actions: {
    setOnline(value) {
      this.isOnline = value;
    },
    triggerRefresh() {
      this.refreshKey += 1;
    },
    // type: 'success' (default), 'error', or 'warning' - see
    // ToastContainer.vue for how each renders.
    showToast(message, type = 'success') {
      const id = nextToastId++;
      this.toasts.push({ id, message, type });
      setTimeout(() => this.dismissToast(id), 4000);
      return id;
    },
    dismissToast(id) {
      this.toasts = this.toasts.filter((t) => t.id !== id);
    },
  },
});
