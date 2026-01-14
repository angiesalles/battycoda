import { defineConfig } from 'vite';
import { resolve } from 'path';
import { globSync } from 'glob';
import { basename } from 'path';

// Find all theme CSS files and create entry points for them
// Theme files need to be built separately so they can be loaded dynamically
const themeFiles = globSync('static/css/themes/*.css');
const themeInputs = {};
themeFiles.forEach((file) => {
  const name = basename(file, '.css');
  themeInputs[`theme-${name}`] = resolve(__dirname, file);
});

export default defineConfig({
  // Build output goes to static/dist/
  build: {
    outDir: 'static/dist',
    emptyOutDir: true,
    manifest: true,
    // Keep CSS files separate per entry point for dynamic theme loading
    cssCodeSplit: true,
    rollupOptions: {
      // Entry points for code splitting
      // Each entry point produces a separate bundle
      input: {
        // Core JS bundle - loaded on every page
        main: resolve(__dirname, 'static/js/main.js'),

        // Core CSS bundle - loaded on every page
        styles: resolve(__dirname, 'static/css/main.css'),

        // Feature bundles - loaded only on pages that need them
        player: resolve(__dirname, 'static/js/player/index.js'),
        segmentation: resolve(__dirname, 'static/js/segmentation/index.js'),
        clusterExplorer: resolve(__dirname, 'static/js/cluster_explorer/index.js'),
        clusterMapping: resolve(__dirname, 'static/js/cluster_mapping/index.js'),
        fileUpload: resolve(__dirname, 'static/js/file_upload/index.js'),

        // Theme CSS files - built separately for dynamic loading
        ...themeInputs,
      },
      output: {
        // Ensure consistent chunk naming
        entryFileNames: '[name]-[hash].js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },

  // CSS configuration
  css: {
    // Enable source maps for debugging in development
    devSourcemap: true,
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
