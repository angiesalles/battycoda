/**
 * File Upload - Module Loader
 *
 * This file has been refactored into smaller modules for better maintainability.
 * The modules are located in the file_upload/ subdirectory:
 * - initialization.js: Setup and initialization
 * - dropzone.js: Dropzone configuration and handlers
 * - progress.js: Progress tracking and display
 * - validation.js: File validation logic
 *
 * This loader loads all modules in the correct order.
 */

(function () {
  const modules = [
    'file_upload/validation.js',
    'file_upload/progress.js',
    'file_upload/dropzone.js',
    'file_upload/initialization.js',
  ];

  const basePath = document.currentScript.src.replace(/[^/]*$/, '');

  modules.forEach(function (module) {
    const script = document.createElement('script');
    script.src = basePath + module;
    script.async = false; // Maintain order
    document.head.appendChild(script);
  });
})();
