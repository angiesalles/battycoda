import { defineConfig } from 'vite';
import { resolve } from 'path';
import { globSync } from 'glob';
import { basename } from 'path';
import { sentryVitePlugin } from '@sentry/vite-plugin';

// Find all theme CSS files and create entry points for them
// Theme files need to be built separately so they can be loaded dynamically
const themeFiles = globSync('static/css/themes/*.css');
const themeInputs = {};
themeFiles.forEach((file) => {
  const name = basename(file, '.css');
  themeInputs[`theme-${name}`] = resolve(__dirname, file);
});

// Sentry configuration for source map uploads
// Only upload source maps when all required env vars are set
const sentryEnabled =
  process.env.SENTRY_AUTH_TOKEN &&
  process.env.SENTRY_ORG &&
  process.env.SENTRY_PROJECT;

const isProduction = process.env.NODE_ENV === 'production';

// Configure plugins array
const plugins = [];

if (sentryEnabled && isProduction) {
  plugins.push(
    sentryVitePlugin({
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      authToken: process.env.SENTRY_AUTH_TOKEN,
      sourcemaps: {
        // Upload source maps from the dist directory
        assets: './static/dist/**',
        // Delete source maps after upload (don't serve them)
        filesToDeleteAfterUpload: './static/dist/**/*.map',
      },
      // Release name - use git commit hash if available
      release: {
        name: process.env.SENTRY_RELEASE || undefined,
      },
      // Disable telemetry
      telemetry: false,
    })
  );
}

export default defineConfig({
  // Plugins
  plugins,
  // Test configuration (Vitest)
  test: {
    // Enable globals like describe, it, expect without imports
    globals: true,

    // Use jsdom for DOM testing
    environment: 'jsdom',

    // Pool configuration - reuse workers to avoid jsdom startup overhead
    pool: 'threads',
    poolOptions: {
      threads: {
        // Reuse threads instead of isolating each test file
        // This dramatically speeds up tests by avoiding repeated jsdom initialization
        isolate: false,
        singleThread: false,
      },
    },

    // Test file patterns - place tests next to source files
    include: ['static/js/**/*.test.{js,ts}', 'static/js/**/*.spec.{js,ts}'],

    // Coverage settings
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: '.coverage-js',
      include: ['static/js/**/*.{js,ts}'],
      exclude: [
        'static/js/**/*.test.{js,ts}',
        'static/js/**/*.spec.{js,ts}',
        'static/js/**/*.d.ts',
        'static/js/app.js', // Third-party Maisonnette
        'static/js/test/**',
        'static/js/types/**',
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
    // Source maps: generate for production debugging
    // - In production: 'hidden' generates maps but doesn't reference them in output
    // - In development: true generates inline source maps
    // The Sentry plugin will upload and then delete .map files in production
    sourcemap: isProduction ? 'hidden' : true,
    rollupOptions: {
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
        profile: resolve(__dirname, 'static/js/profile/index.js'),
        speciesCreate: resolve(__dirname, 'static/js/species/index.js'),

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
