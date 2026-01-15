import js from '@eslint/js';
import prettier from 'eslint-config-prettier';

export default [
  js.configs.recommended,
  prettier,
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        requestAnimationFrame: 'readonly',
        cancelAnimationFrame: 'readonly',
        FormData: 'readonly',
        Headers: 'readonly',
        Request: 'readonly',
        Response: 'readonly',
        URLSearchParams: 'readonly',
        URL: 'readonly',
        Event: 'readonly',
        CustomEvent: 'readonly',
        MouseEvent: 'readonly',
        KeyboardEvent: 'readonly',
        HTMLElement: 'readonly',
        HTMLCanvasElement: 'readonly',
        HTMLAudioElement: 'readonly',
        HTMLInputElement: 'readonly',
        Node: 'readonly',
        NodeList: 'readonly',
        DOMRect: 'readonly',
        ResizeObserver: 'readonly',
        MutationObserver: 'readonly',
        IntersectionObserver: 'readonly',
        navigator: 'readonly',
        location: 'readonly',
        history: 'readonly',
        alert: 'readonly',
        confirm: 'readonly',
        // jQuery (external CDN)
        $: 'readonly',
        jQuery: 'readonly',
        // D3 (external CDN)
        d3: 'readonly',
        // Toastr (external CDN)
        toastr: 'readonly',
        // Select2 (external CDN)
        select2: 'readonly',
        // Audio context
        AudioContext: 'readonly',
        webkitAudioContext: 'readonly',
        // Performance API
        performance: 'readonly',
        // Blob and File APIs
        Blob: 'readonly',
        File: 'readonly',
        FileReader: 'readonly',
        // Error types
        Error: 'readonly',
        TypeError: 'readonly',
        // Math and other built-ins
        Math: 'readonly',
        JSON: 'readonly',
        Date: 'readonly',
        Number: 'readonly',
        String: 'readonly',
        Array: 'readonly',
        Object: 'readonly',
        Map: 'readonly',
        Set: 'readonly',
        Promise: 'readonly',
        // Canvas
        CanvasRenderingContext2D: 'readonly',
        Image: 'readonly',
        ImageData: 'readonly',
        // Text encoding/decoding
        TextDecoder: 'readonly',
        TextEncoder: 'readonly',
        // DataTransfer (for drag-and-drop)
        DataTransfer: 'readonly',
        // XMLHttpRequest
        XMLHttpRequest: 'readonly',
      },
    },
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      'no-console': 'off', // Allow console for now
      'prefer-const': 'warn',
      'no-var': 'error',
      eqeqeq: ['error', 'always', { null: 'ignore' }],
      'no-undef': 'error',
    },
  },
  // Test file configuration - add Vitest/Node.js globals
  {
    files: ['**/*.test.js', '**/*.spec.js', '**/test/**/*.js'],
    languageOptions: {
      globals: {
        // Vitest globals (enabled via globals: true in vite.config.js)
        describe: 'readonly',
        it: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        beforeAll: 'readonly',
        afterAll: 'readonly',
        vi: 'readonly',
        // Node.js global object (for mocking fetch, Audio, etc.)
        global: 'writable',
      },
    },
  },
  {
    ignores: [
      'node_modules/**',
      'static/dist/**',
      'static/js/app.js', // Third-party Maisonnette
      'static/js/theme-switcher/theme-switcher.min.js', // Minified
      'static/lib/**',
      'staticfiles/**',
      'venv/**',
      '*.min.js',
      // Incomplete ES6 module fragments (to be fixed in separate task)
      'static/js/file_upload/dropzone.js',
      'static/js/file_upload/progress.js',
      'static/js/file_upload/validation.js',
      'static/js/file_upload/initialization.js',
    ],
  },
];
