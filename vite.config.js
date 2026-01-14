import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  // Build output goes to static/dist/
  build: {
    outDir: 'static/dist',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      // Entry points for code splitting
      // Each entry point produces a separate bundle
      input: {
        // Core bundle - loaded on every page
        main: resolve(__dirname, 'static/js/main.js'),

        // Feature bundles - loaded only on pages that need them
        player: resolve(__dirname, 'static/js/player/index.js'),
        segmentation: resolve(__dirname, 'static/js/segmentation/index.js'),
        clusterExplorer: resolve(__dirname, 'static/js/cluster_explorer/index.js'),
        clusterMapping: resolve(__dirname, 'static/js/cluster_mapping/index.js'),
        fileUpload: resolve(__dirname, 'static/js/file_upload/index.js'),
      },
      output: {
        // Ensure consistent chunk naming
        entryFileNames: '[name]-[hash].js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
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
