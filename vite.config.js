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
  // Test configuration (Vitest)
  test: {
    // Enable globals like describe, it, expect without imports
    globals: true,

    // Use jsdom for DOM testing
    environment: 'jsdom',

    // Test file patterns - place tests next to source files
    include: ['static/js/**/*.test.js', 'static/js/**/*.spec.js'],

    // Coverage settings
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: 'coverage',
      include: ['static/js/**/*.js'],
      exclude: [
        'static/js/**/*.test.js',
        'static/js/**/*.spec.js',
        'static/js/app.js', // Third-party Maisonnette
        'static/js/test/**',
        'node_modules/**',
      ],
    },

    // Setup files for mocks and global config
    setupFiles: ['static/js/test/setup.js'],
  },

  // Build output goes to static/dist/
  build: {
    outDir: 'static/dist',
    emptyOutDir: true,
    manifest: true,
    // Keep CSS files separate per entry point for dynamic theme loading
    cssCodeSplit: true,
    rollupOptions: {
      // Suppress warnings for missing font files in third-party Maisonnette CSS.
      // The fonts are loaded via Google Fonts CDN, so these local references are dead.
      // TODO: Remove this suppression when app.css is cleaned up (see battycoda-6nn.6)
      onwarn(warning, warn) {
        if (
          warning.message &&
          (warning.message.includes('lib/open-sans') ||
            warning.message.includes('lib/raleway') ||
            warning.message.includes("didn't resolve at build time"))
        ) {
          return; // Suppress font resolution warnings
        }
        warn(warning);
      },

      // External CDN dependencies - these are loaded via CDN in Django templates
      // and should not be bundled by Vite. They are available as globals on window.
      // See CLAUDE.md "External Dependencies (CDN)" section for the full list.
      external: ['jquery'],

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
        // Map external modules to their global variable names
        globals: {
          jquery: 'jQuery',
        },
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
