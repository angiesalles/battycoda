/**
 * TUS Resumable Upload Handler
 *
 * Uses tus-js-client for resumable uploads with automatic retry.
 * Falls back to XHR for unsupported browsers or non-WAV uploads.
 */

import * as tus from 'tus-js-client';
import {
  updateProgress,
  resetProgress,
  showSuccess,
  showError,
  showCancelled,
} from './progress.js';

const TUS_ENDPOINT = '/tus/';
const CHUNK_SIZE = 5 * 1024 * 1024; // 5 MB
const RETRY_DELAYS = [0, 1000, 3000, 5000, 10000];

/**
 * Check if TUS uploads are supported in this browser
 * @returns {boolean}
 */
export function isTusSupported() {
  return tus.isSupported;
}

/**
 * Extract recording metadata from the upload form
 * @param {HTMLFormElement} form
 * @returns {Object} Metadata key-value pairs for TUS Upload-Metadata header
 */
export function extractFormMetadata(form) {
  const meta = {};
  const formData = new FormData(form);

  // Map form fields to metadata keys
  const fieldMap = {
    name: 'name',
    species: 'species_id',
    project: 'project_id',
    description: 'description',
    recorded_date: 'recorded_date',
    location: 'location',
    equipment: 'equipment',
    environmental_conditions: 'environmental_conditions',
  };

  for (const [formField, metaKey] of Object.entries(fieldMap)) {
    const value = formData.get(formField);
    if (value) {
      meta[metaKey] = value;
    }
  }

  // Handle split_long_files checkbox
  meta.split_long_files = formData.get('split_long_files') === 'on' ? 'true' : 'false';

  return meta;
}

/**
 * Generate a fingerprint for resumable uploads.
 * Uses filename + size + lastModified to identify the same file.
 * @param {File} file
 * @returns {string}
 */
function getFingerprint(file) {
  return `tus-${file.name}-${file.size}-${file.lastModified}`;
}

/**
 * @typedef {Object} TusUploadConfig
 * @property {HTMLFormElement} form - The form element
 * @property {HTMLElement} progressBar - Progress bar element
 * @property {HTMLElement} statusText - Status text element
 * @property {File} file - The file to upload
 * @property {function} [onSuccess] - Callback on successful upload
 * @property {function} [onError] - Callback on error
 */

/**
 * Create a TUS upload handler
 * @param {TusUploadConfig} config
 * @returns {Object} Upload controller with start() and abort() methods
 */
export function createTusUploadHandler(config) {
  const { form, progressBar, statusText, file, onSuccess, onError } = config;
  let upload = null;

  function handleError(message) {
    showError(progressBar, statusText, message);
    if (onError) onError(message);
  }

  function start() {
    resetProgress(progressBar, statusText);

    const metadata = extractFormMetadata(form);
    metadata.filename = file.name;
    metadata.content_type = file.type || 'audio/wav';

    upload = new tus.Upload(file, {
      endpoint: TUS_ENDPOINT,
      chunkSize: CHUNK_SIZE,
      retryDelays: RETRY_DELAYS,
      metadata: metadata,
      fingerprint: () => Promise.resolve(getFingerprint(file)),
      removeFingerprintOnSuccess: true,

      onProgress: (bytesUploaded, bytesTotal) => {
        updateProgress(progressBar, statusText, bytesUploaded, bytesTotal);
      },

      onSuccess: () => {
        // Extract redirect URL from upload response headers if available
        const xhr = upload._xhr || {};
        const redirectUrl =
          xhr.getResponseHeader?.('X-Redirect-Url') || null;
        const recordingId =
          xhr.getResponseHeader?.('X-Recording-Id') || null;

        const message = 'Upload complete! Recording created successfully.';
        showSuccess(progressBar, statusText, message);

        // Redirect after short delay
        setTimeout(() => {
          if (redirectUrl) {
            window.location.assign(redirectUrl);
          } else {
            // Fallback: reload or go to recordings list
            window.location.assign('/recordings/');
          }
        }, 1500);

        if (onSuccess) onSuccess({ redirectUrl, recordingId });
      },

      onError: (error) => {
        // tus-js-client wraps errors; extract the message
        const msg =
          error.originalResponse?.getHeader?.('X-Error') ||
          error.message ||
          'Upload failed';

        // Check if the error is recoverable (network issue)
        if (
          error.originalRequest &&
          !error.originalResponse
        ) {
          handleError(
            'Network error. The upload will resume automatically when connection is restored.',
          );
        } else {
          handleError(msg);
        }
      },
    });

    // Check for previous uploads to resume
    upload.findPreviousUploads().then((previousUploads) => {
      if (previousUploads.length > 0) {
        // Resume the most recent upload
        upload.resumeFromPreviousUpload(previousUploads[0]);
      }
      upload.start();
    });
  }

  function abort() {
    if (upload) {
      upload.abort(true); // true = remove from URL storage
      showCancelled(progressBar, statusText);
    }
  }

  return { start, abort };
}
