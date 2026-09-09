import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// Builds straight into this Frappe app's own public/ directory (served at
// /assets/gym_management/portal/... with zero extra hosting/deploy step -
// same as every hand-written JS file already under public/js) rather than
// a separate frontend deployment. Fixed (non-hashed) output filenames so
// www/gym-portal/index.html can reference them directly without parsing
// Vite's manifest.json server-side. Same layout as sports_complex's own
// frontend/vite.config.js - see that file for the fuller rationale.
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  base: '/assets/gym_management/portal/',
  build: {
    outDir: '../public/portal',
    emptyOutDir: false,
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
      },
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]',
      },
    },
  },
  server: {
    port: 8091,
  },
})
