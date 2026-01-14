/**
 * File Upload Module
 *
 * Advanced file upload functionality with drag-and-drop support,
 * progress tracking, and validation for WAV and pickle files.
 *
 * Dependencies:
 * - None (vanilla JavaScript)
 *
 * Components (to be converted to ES6 modules):
 * - initialization.js : Main setup and form handling
 * - dropzone.js       : Drag-and-drop file selection
 * - progress.js       : Upload progress bar and status updates
 * - validation.js     : File type and size validation
 *
 * Usage:
 * Include this module on upload pages. Automatically initializes
 * when DOM is ready if form[enctype="multipart/form-data"] exists.
 *
 * Supports both single file and batch upload forms.
 *
 * Global flag:
 * - window.advancedUploadInitialized: Set to true when initialized
 *
 * Note: The component files are currently not ES6 modules.
 * They will be converted as part of the ES6 module migration task.
 * For now, they are loaded via script tags in Django templates.
 */

// Placeholder for future ES6 module exports
// Once the component files are converted to ES6 modules, this file will:
// import './initialization.js';
// export { initFileUpload } from './initialization.js';

console.log('File upload module entry point loaded');
