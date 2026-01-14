import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  // Build output goes to static/dist/
  build: {
    outDir: 'static/dist',
    emptyDirBeforeWrite: true,
    manifest: true,
    rollupOptions: {
      // Entry points - add more as features are migrated
      input: {
        main: resolve(__dirname, 'static/js/vite/main.js'),
        // Example: 'theme-switcher': resolve(__dirname, 'static/js/theme-switcher/index.js'),
      },
    },
  },

  // Development server configuration
  server: {
    port: 5173,
    strictPort: true,
    // Allow Django to proxy requests to Vite
    origin: 'http://localhost:5173',
  },

  // Resolve aliases for cleaner imports
  resolve: {
    alias: {
      '@': resolve(__dirname, 'static/js'),
    },
  },
});
