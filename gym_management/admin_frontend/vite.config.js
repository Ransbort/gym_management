import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { VitePWA } from 'vite-plugin-pwa';
import Icons from 'unplugin-icons/vite';

// Gym Admin - fullscreen staff dashboard, built straight into
// public/admin (served at /assets/gym_management/admin/...) and rendered
// through www/gym-admin/index.html, same pattern as ../frontend (the Gym
// Portal SPA) but with a PWA manifest + service worker layered on top -
// see that plugin's config below and src/main.js's manual registration.
export default defineConfig({
	plugins: [
		vue(),
		// frappe-ui's own components (e.g. Spinner, used inside Button) import
		// icons via unplugin-icons' `~icons/lucide/<name>` virtual modules -
		// this is normally wired up for you by frappe-ui's own Vite plugin
		// (`frappeui({ lucideIcons: true })`, see POSNext's vite.config.js),
		// which this app doesn't use (see the comment below), so it's
		// registered directly here instead.
		Icons({ compiler: 'vue3' }),
		VitePWA({
			// The built HTML that ships to users is www/gym-admin/index.html
			// (a hand-authored Jinja template, not Vite's own dist/index.html -
			// see that file's own comments), so auto-injecting a register
			// script into the built index.html would land somewhere nobody
			// serves. Registration instead happens explicitly in
			// src/main.js via `import('virtual:pwa-register')`, same as
			// POSNext's own src/main.js does.
			injectRegister: false,
			registerType: 'autoUpdate',
			includeAssets: ['icon.svg', 'icon-maskable.svg'],
			manifest: {
				name: 'Gym Admin',
				short_name: 'Gym Admin',
				description: 'Front-desk check-in, operational overview, and membership & payments for gym staff.',
				// Matches POSNext's own manifest values exactly (see
				// apps/POSNext/POS/vite.config.js) - indigo theme, white
				// background (only the header/sidebar chrome is dark; the
				// content area is light, same split POSNext itself uses).
				theme_color: '#4f46e5',
				background_color: '#ffffff',
				display: 'standalone',
				scope: '/assets/gym_management/admin/',
				start_url: '/gym-admin',
				icons: [
					{ src: '/assets/gym_management/admin/icon.svg', sizes: '192x192', type: 'image/svg+xml', purpose: 'any' },
					{ src: '/assets/gym_management/admin/icon.svg', sizes: '512x512', type: 'image/svg+xml', purpose: 'any' },
					{ src: '/assets/gym_management/admin/icon-maskable.svg', sizes: '192x192', type: 'image/svg+xml', purpose: 'maskable' },
					{ src: '/assets/gym_management/admin/icon-maskable.svg', sizes: '512x512', type: 'image/svg+xml', purpose: 'maskable' },
				],
			},
			workbox: {
				globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
				maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
				navigateFallback: null,
				navigateFallbackDenylist: [/^\/api/, /^\/app/],
				runtimeCaching: [
					{
						urlPattern: /\/assets\/gym_management\/admin\/.*/i,
						handler: 'CacheFirst',
						options: {
							cacheName: 'gym-admin-assets-cache',
							expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 },
						},
					},
					{
						urlPattern: /\/api\/method\/gym_management\..*/i,
						handler: 'NetworkFirst',
						options: {
							cacheName: 'gym-admin-api-cache',
							networkTimeoutSeconds: 8,
							expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 },
							cacheableResponse: { statuses: [0, 200] },
						},
					},
				],
				cleanupOutdatedCaches: true,
				skipWaiting: true,
				clientsClaim: true,
			},
			devOptions: {
				enabled: false,
			},
		}),
	],
	base: '/assets/gym_management/admin/',
	build: {
		outDir: '../public/admin',
		emptyOutDir: false,
		rollupOptions: {
			output: {
				entryFileNames: 'assets/main.js',
				chunkFileNames: 'assets/[name].js',
				assetFileNames: (assetInfo) => {
					const name = assetInfo.name || (assetInfo.names && assetInfo.names[0]) || 'asset';
					if (name.endsWith('.css')) return 'assets/main.css';
					return `assets/${name}`;
				},
			},
		},
	},
	resolve: {
		alias: {
			'@': fileURLToPath(new URL('./src', import.meta.url)),
		},
	},
	server: {
		port: 8082,
		proxy: {
			'^/(app|api|assets|files|socket.io)': {
				target: 'http://127.0.0.1:8000',
				ws: true,
				changeOrigin: true,
				secure: false,
				router: function (req) {
					const site_name = req.headers.host.split(':')[0];
					return `http://${site_name}:8000`;
				},
			},
		},
	},
});
