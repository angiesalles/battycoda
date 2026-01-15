/**
 * File Upload Module
 *
 * Advanced file upload functionality with drag-and-drop support,
 * progress tracking, and validation for WAV and pickle files.
 *
 * Components:
 * - dropzone.js     : Drag-and-drop file selection
 * - progress.js     : Upload progress bar and status updates
 * - upload-handler.js : XHR-based upload with progress
 * - validation.js   : File type and size validation
 * - initialization.js : Main setup and form handling
 *
 * Usage:
 * Include this module on upload pages. Automatically initializes
 * when DOM is ready if form[enctype="multipart/form-data"] exists.
 *
 * Supports both single file and batch upload forms.
 */

// Re-export public API
export { setupDropzone } from './dropzone.js';
export {
  getFileInfo,
  updateFileInfoDisplay,
  updateProgress,
  resetProgress,
  showSuccess,
  showError,
  showCancelled,
} from './progress.js';
export { createUploadHandler, hasRequiredFiles } from './upload-handler.js';
export {
  isValidWavFile,
  isValidPickleFile,
  validateFiles,
  formatFileSize,
} from './validation.js';
export { initFileUpload, autoInit } from './initialization.js';

// Auto-initialize when this module is loaded
import { autoInit } from './initialization.js';
autoInit();
