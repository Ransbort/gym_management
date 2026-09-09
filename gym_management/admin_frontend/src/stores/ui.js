import { defineStore } from 'pinia';

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
  }),
  actions: {
    setOnline(value) {
      this.isOnline = value;
    },
    triggerRefresh() {
      this.refreshKey += 1;
    },
  },
});
