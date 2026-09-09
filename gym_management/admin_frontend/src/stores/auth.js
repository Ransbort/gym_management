import { defineStore } from 'pinia';
import { call, firstServerMessage } from '@/api/frappe';
import { useSessionLock } from '@/composables/useSessionLock';

// Real Frappe session login/logout, same pattern as ../../frontend's own
// stores/auth.js (the Gym Portal SPA) - see that file's comments.
// window.adminBoot is recomputed server-side on every page load, see
// www/gym-admin/index.py.
export const useAuthStore = defineStore('auth', {
  state: () => {
    const boot = window.adminBoot || {};
    return {
      isGuest: boot.is_guest !== false,
      user: boot.user || 'Guest',
      fullName: boot.full_name || '',
      userImage: boot.user_image || '',
      isStaff: !!boot.is_staff,
      siteName: boot.site_name || window.location.hostname,
      gymName: boot.gym_name || '',
      gymLogo: boot.gym_logo || '',
      themeColor: boot.theme_color || '#4f46e5',
      enableSessionLock: !!boot.enable_session_lock,
      sessionLockTimeout: boot.session_lock_timeout || 5,
      loggingIn: false,
      loginError: '',
    };
  },
  getters: {
    isLoggedIn: (state) => !state.isGuest,
  },
  actions: {
    async login(usr, pwd, redirectTo) {
      this.loggingIn = true;
      this.loginError = '';
      try {
        await call('login', { usr, pwd });
        // Cache a hash of the password locally so the session lock screen
        // can still verify an unlock attempt while offline (see
        // useSessionLock.js) - has to happen here, before the redirect
        // below throws this whole page away, and localStorage survives
        // that full navigation just fine.
        try {
          await useSessionLock().cachePasswordHashFromLogin(pwd);
        } catch (e) {
          // Non-fatal: worst case offline unlock isn't available until the
          // next successful login.
        }
        // Full navigation rather than patching this store's state in
        // place: the next request re-renders www/gym-admin/index.html,
        // which recomputes window.adminBoot from frappe.session.user
        // server-side and gives frappe.call() a CSRF token that actually
        // matches the new session.
        window.location.href = redirectTo || '/gym-admin';
      } catch (err) {
        this.loginError = firstServerMessage(err) || 'Could not sign in - check your email and password.';
      } finally {
        this.loggingIn = false;
      }
    },
    async logout() {
      try {
        await call('logout');
      } catch (e) {
        // Best-effort - redirect regardless.
      }
      window.location.href = '/gym-admin';
    },
  },
});
