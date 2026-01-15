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
    showSuccess(progressBar, statusText, response.recordings_created);

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
 * Validate that required files are selected
 * @param {Object} inputs - File input elements
 * @param {boolean} isBatchUpload - Whether this is a batch upload form
 * @returns {boolean} True if valid
 */
export function hasRequiredFiles(inputs, isBatchUpload) {
  if (isBatchUpload) {
    // Batch upload form - just need WAV files
    return inputs.wavFilesInput && inputs.wavFilesInput.files.length > 0;
  } else {
    // Single upload form - need both WAV and pickle files
    return (
      inputs.wavFileInput &&
      inputs.pickleFileInput &&
      inputs.wavFileInput.files.length > 0 &&
      inputs.pickleFileInput.files.length > 0
    );
  }
}
