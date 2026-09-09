import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { Alert, Badge, Button, Dialog, ErrorMessage, FormControl, TextInput } from 'frappe-ui';

import App from './App.vue';
import router from './router';
import { applyTheme } from './theme';
import './style.css';

// Applied before mount (straight off window.adminBoot, not through the
// auth store/component tree) so there's no flash of the default indigo
// before the site's configured color takes over.
applyTheme((window.adminBoot || {}).theme_color);

const app = createApp(App);
app.use(createPinia());
app.use(router);

// frappe-ui components, available globally without an import in every
// page - same set POSNext's own src/main.js registers.
const globalComponents = { Button, TextInput, FormControl, ErrorMessage, Dialog, Alert, Badge };
for (const key in globalComponents) {
  app.component(key, globalComponents[key]);
}

app.mount('#app');

// PWA service worker registration - manual because the shipped HTML is
// www/gym-admin/index.html (a hand-authored Jinja template), not Vite's
// own built index.html that vite-plugin-pwa would normally auto-inject
// into (see vite.config.js's injectRegister: false). Same pattern as
// POSNext's own src/main.js.
if ('serviceWorker' in navigator) {
  window.addEventListener(
    'load',
    () => {
      import('virtual:pwa-register').then(({ registerSW }) => {
        registerSW({
          immediate: true,
          onNeedRefresh: () => console.info('[Gym Admin] New content available.'),
          onOfflineReady: () => console.info('[Gym Admin] Ready to work offline.'),
          onRegisterError: (err) => console.error('[Gym Admin] Service worker registration failed.', err),
        });
      });
    },
    { passive: true }
  );
}
