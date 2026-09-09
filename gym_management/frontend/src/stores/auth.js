import { defineStore } from 'pinia';
import { call, firstServerMessage } from '@/api/frappe';

// Real Frappe session login/logout - "login"/"logout" are special
// whitelisted method names Frappe's own core login page calls the exact
// same way. There's no client-side token here; window.portalBoot (read
// below) is recomputed server-side on every page load - see
// www/gym-portal/index.py.
export const useAuthStore = defineStore('auth', {
  state: () => {
    const boot = window.portalBoot || {};
    return {
      isGuest: boot.is_guest !== false,
      user: boot.user || 'Guest',
      fullName: boot.full_name || '',
      isMember: !!boot.is_member,
      memberName: boot.member_name || '',
      isTrainer: !!boot.is_trainer,
      trainerName: boot.trainer_name || '',
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
        // Full navigation rather than patching this store's state in
        // place: the next request re-renders www/gym-portal/index.html,
        // which recomputes window.portalBoot from frappe.session.user
        // server-side and gives frappe.call() a CSRF token that actually
        // matches the new session.
        window.location.href = redirectTo || '/gym-portal';
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
      window.location.href = '/gym-portal';
    },
  },
});
