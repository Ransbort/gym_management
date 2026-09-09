import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import Home from '@/pages/Home.vue';
import Login from '@/pages/Login.vue';
import Member from '@/pages/Member.vue';
import Trainer from '@/pages/Trainer.vue';

const routes = [
  { path: '/', name: 'home', component: Home, meta: { title: 'Gym Portal' } },
  { path: '/login', name: 'login', component: Login, meta: { title: 'Sign In' } },
  { path: '/member', name: 'member', component: Member, meta: { title: 'My Membership', requiresAuth: true } },
  { path: '/trainer', name: 'trainer', component: Trainer, meta: { title: 'Trainer Dashboard', requiresAuth: true } },
];

const router = createRouter({
  // Base matches website_route_rules' catch-all in hooks.py - any
  // /gym-portal/<path:app_path> request server-side resolves to this
  // same shell page, which is what lets a hard reload/deep link on e.g.
  // /gym-portal/trainer work at all instead of 404ing before Vue Router
  // ever gets a chance to take over client-side.
  history: createWebHistory('/gym-portal'),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

// /member and /trainer both need a signed-in session (unlike
// sports_complex's guest-booking flow, there's no anonymous path through
// either dashboard) - bounce to /login with a redirect-back query param
// rather than letting the page load and immediately fail its own
// require_member()/require_trainer() API call.
router.beforeEach((to) => {
  if (!to.meta.requiresAuth) return true;
  const auth = useAuthStore();
  if (auth.isLoggedIn) return true;
  return { path: '/login', query: { redirect: to.fullPath } };
});

export default router;
