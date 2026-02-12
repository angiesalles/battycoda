/**
 * Upload Handler - XHR-based file upload with progress tracking
 *
 * Handles the actual file upload via XMLHttpRequest with progress,
 * success, and error callbacks.
 */

import {
  updateProgress,
  resetProgress,
  showSuccess,
  showError,
  showCancelled,
} from './progress.js';
import { isTusSupported, createTusUploadHandler } from './tus-handler.js';

/**
 * @typedef {Object} UploadConfig
 * @property {HTMLFormElement} form - The form element
 * @property {HTMLElement} progressBar - The progress bar element
 * @property {HTMLElement} statusText - Status text element
 * @property {function} [onSuccess] - Callback on successful upload
 * @property {function} [onError] - Callback on error
 */

/**
 * Create an upload handler for a form
 * @param {UploadConfig} config - Upload configuration
 * @returns {Object} Upload controller with abort method
 */
export function createUploadHandler(config) {
  const { form, progressBar, statusText, onSuccess, onError } = config;
  let xhr = null;

  /**
   * Handle upload errors
   * @param {string} message - Error message
   */
  function handleError(message) {
    showError(progressBar, statusText, message);
    if (onError) onError(message);
  }

  /**
   * Handle successful response
   * @param {Object} response - Parsed JSON response
   */
  function handleSuccess(response) {
    // Use server message if provided (e.g., pickle uploads),
    // otherwise construct message from recordings_created
    let message = response.message;
    if (!message && response.recordings_created !== undefined) {
      message = `Upload complete! Successfully created batch with ${response.recordings_created} recordings.`;
    }
    showSuccess(progressBar, statusText, message);

    // Redirect after short delay
    setTimeout(() => {
      if (response.redirect_url) {
        window.location.assign(response.redirect_url);
      }
    }, 1500);

    if (onSuccess) onSuccess(response);
  }

  /**
   * Start the upload
   */
  function start() {
    resetProgress(progressBar, statusText);

    xhr = new XMLHttpRequest();
    const formData = new FormData(form);

    // Progress tracking
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        updateProgress(progressBar, statusText, e.loaded, e.total);
      }
    });

    // Handle response
    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        try {
          const response = JSON.parse(xhr.responseText);

          if (response.success) {
            handleSuccess(response);
          } else {
            handleError(response.error || 'Upload failed');
          }
        } catch {
          // Handle non-JSON response (likely HTML from successful form submission)
          if (xhr.responseURL) {
            window.location.assign(xhr.responseURL);
          } else {
            handleError('Unknown response from server');
          }
        }
      } else {
        handleError(`Upload failed (${xhr.status}: ${xhr.statusText})`);
      }
    });

    xhr.addEventListener('error', () => {
      handleError('Network error occurred');
    });

    xhr.addEventListener('abort', () => {
      showCancelled(progressBar, statusText);
    });

    // Send the request
    xhr.open('POST', form.action || window.location.href, true);
    xhr.send(formData);
  }

  /**
   * Abort the upload
   */
  function abort() {
    if (xhr && xhr.readyState !== 4) {
      xhr.abort();
    }
  }

  return { start, abort };
}

/**
 * Create an upload handler that automatically chooses TUS for single WAV
 * uploads and falls back to XHR for batch/ZIP uploads or unsupported browsers.
 *
 * @param {UploadConfig} config - Upload configuration (same as createUploadHandler)
 * @param {Object} inputs - File input elements (from initialization.js)
 * @param {boolean} isBatchUpload - Whether this is a batch upload
 * @returns {Object} Upload controller with start() and abort() methods
 */
export function createUploadHandlerAuto(config, inputs, isBatchUpload) {
  // Use TUS for single-file WAV uploads when supported
  if (
    !isBatchUpload &&
    isTusSupported() &&
    inputs.wavFileInput &&
    inputs.wavFileInput.files.length === 1
  ) {
    const file = inputs.wavFileInput.files[0];
    return createTusUploadHandler({
      ...config,
      file: file,
    });
  }

  // Fall back to XHR for batch uploads, ZIP uploads, or unsupported browsers
  return createUploadHandler(config);
}

/**
 * Validate that required files are selected
 * @param {Object} inputs - File input elements
 * @param {boolean} isBatchUpload - Whether this is a batch upload form
 * @returns {boolean} True if valid
 */
export function hasRequiredFiles(inputs, isBatchUpload) {
  // Check form type for pickle-only uploads
  if (inputs.formType === 'pickle_only') {
    return Boolean(inputs.pickleFileInput && inputs.pickleFileInput.files.length > 0);
  }

  if (isBatchUpload) {
    // Batch upload form - just need WAV/ZIP files
    return Boolean(inputs.wavFilesInput && inputs.wavFilesInput.files.length > 0);
  } else {
    // Single upload form - need WAV file (pickle is optional)
    return Boolean(inputs.wavFileInput && inputs.wavFileInput.files.length > 0);
  }
}
