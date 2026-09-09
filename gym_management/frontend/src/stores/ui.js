import { defineStore } from 'pinia';

// Drives the Navbar's slide-out sidebar menu - a plain boolean rather
// than local component state, since the backdrop/sidebar are Teleported
// out of Navbar's own subtree (see Navbar.vue).
export const useUiStore = defineStore('ui', {
  state: () => ({
    menuOpen: false,
    navbarHidden: false,
  }),
  actions: {
    openMenu() {
      this.menuOpen = true;
    },
    closeMenu() {
      this.menuOpen = false;
    },
  },
});
