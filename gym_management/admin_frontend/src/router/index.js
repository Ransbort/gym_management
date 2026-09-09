import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const routes = [
  {
    path: '/',
    name: 'Overview',
    component: () => import('@/pages/Overview.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/checkin',
    name: 'CheckIn',
    component: () => import('@/pages/CheckIn.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/members',
    name: 'Members',
    component: () => import('@/pages/Members.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/memberships',
    name: 'Memberships',
    component: () => import('@/pages/Memberships.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
];

// Base must match hooks.py's website_route_rules catch-all
// (/gym-admin/<path:app_path> -> gym-admin) - a hard reload on any nested
// route still lands on this same shell, and Vue Router needs the same
// base to make sense of the resulting URL.
const router = createRouter({
  history: createWebHistory('/gym-admin'),
  routes,
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'Login', query: { redirect: to.fullPath } };
  }
  return true;
});

export default router;
