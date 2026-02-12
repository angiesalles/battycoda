/**
 * Initialization - File upload setup and coordination
 *
 * Sets up file upload forms with dropzone, progress tracking,
 * and XHR-based uploads.
 */

import { setupDropzone } from './dropzone.js';
import { getFileInfo, updateFileInfoDisplay } from './progress.js';
import {
  createUploadHandler,
  createUploadHandlerAuto,
  hasRequiredFiles,
} from './upload-handler.js';

/**
 * @typedef {Object} FileUploadElements
 * @property {HTMLFormElement} form - The form element
 * @property {HTMLElement} progressBar - Progress bar element
 * @property {HTMLElement} progressContainer - Progress container
 * @property {HTMLElement} statusText - Status text element
 * @property {HTMLButtonElement|null} cancelButton - Cancel button
 * @property {HTMLInputElement|null} wavFileInput - Single WAV input
 * @property {HTMLInputElement|null} pickleFileInput - Single pickle input
 * @property {HTMLInputElement|null} wavFilesInput - Batch WAV input
 * @property {HTMLInputElement|null} pickleFilesInput - Batch pickle input
 */

/**
 * Get DOM elements for file upload
 * @returns {FileUploadElements|null} Elements or null if not found
 */
function getElements() {
  const form = document.querySelector('form[enctype="multipart/form-data"]');
  const progressBar = document.getElementById('upload-progress-bar');
  const progressContainer = document.getElementById('upload-progress-container');
  const statusText = document.getElementById('upload-status');

  if (!form || !progressBar) {
    return null;
  }

  return {
    form,
    progressBar,
    progressContainer,
    statusText,
    cancelButton: document.getElementById('cancel-upload'),
    // Single file inputs
    wavFileInput: document.querySelector('input[type="file"][name="wav_file"]'),
    pickleFileInput: document.querySelector(
      'input[type="file"][name="pickle_file"]',
    ),
    // Batch file inputs (support both wav_files and wav_zip naming conventions)
    wavFilesInput:
      document.querySelector('input[type="file"][name="wav_files"]') ||
      document.querySelector('input[type="file"][name="wav_zip"]'),
    pickleFilesInput:
      document.querySelector('input[type="file"][name="pickle_files"]') ||
      document.querySelector('input[type="file"][name="pickle_zip"]'),
  };
}

/**
 * Determine the upload form type based on available inputs
 * @param {FileUploadElements} elements - DOM elements
 * @returns {'batch'|'single'|'pickle_only'} Form type
 */
function getFormType(elements) {
  if (elements.wavFilesInput) {
    return 'batch';
  }
  if (elements.wavFileInput) {
    return 'single';
  }
  if (elements.pickleFileInput) {
    return 'pickle_only';
  }
  return 'single'; // default fallback
}

/**
 * Initialize file upload functionality
 * @returns {boolean} True if initialization succeeded
 */
export function initFileUpload() {
  const elements = getElements();

  if (!elements) {
    return false;
  }

  // Determine form type
  const formType = getFormType(elements);
  const isBatchUpload = formType === 'batch';

  // Get file inputs based on form type
  const inputs = {
    wavFileInput: elements.wavFileInput,
    pickleFileInput: elements.pickleFileInput,
    wavFilesInput: elements.wavFilesInput,
    pickleFilesInput: elements.pickleFilesInput,
    formType: formType,
  };

  // Setup dropzones for all available file inputs
  if (formType === 'batch') {
    setupDropzone(elements.wavFilesInput);
    setupDropzone(elements.pickleFilesInput);
  } else if (formType === 'pickle_only') {
    setupDropzone(elements.pickleFileInput);
  } else {
    setupDropzone(elements.wavFileInput);
    setupDropzone(elements.pickleFileInput);
  }

  // Update file info display when files change
  const updateDisplay = () => {
    const fileInfo = getFileInfo(inputs, isBatchUpload);
    updateFileInfoDisplay(
      {
        progressBar: elements.progressBar,
        progressContainer: elements.progressContainer,
        statusText: elements.statusText,
      },
      fileInfo,
    );
  };

  // Attach change listeners
  if (isBatchUpload) {
    elements.wavFilesInput?.addEventListener('change', updateDisplay);
    elements.pickleFilesInput?.addEventListener('change', updateDisplay);
  } else {
    elements.wavFileInput?.addEventListener('change', updateDisplay);
    elements.pickleFileInput?.addEventListener('change', updateDisplay);
  }

  // Create upload handler
  let uploadHandler = null;

  // Setup cancel button
  if (elements.cancelButton) {
    elements.cancelButton.addEventListener('click', () => {
      if (uploadHandler) {
        uploadHandler.abort();
      }
    });
  }

  // Handle form submission
  elements.form.addEventListener('submit', (e) => {
    // Check if required files are present
    if (!hasRequiredFiles(inputs, isBatchUpload)) {
      // Let normal form submission handle validation errors
      return;
    }

    // Prevent default form submission
    e.preventDefault();

    // Create and start upload (TUS for single WAV, XHR for batch/other)
    uploadHandler = createUploadHandlerAuto(
      {
        form: elements.form,
        progressBar: elements.progressBar,
        statusText: elements.statusText,
      },
      inputs,
      isBatchUpload,
    );

    uploadHandler.start();
  });

  // Set global flag for other scripts
  window.advancedUploadInitialized = true;

  return true;
}

/**
 * Auto-initialize when DOM is ready
 */
export function autoInit() {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFileUpload);
  } else {
    initFileUpload();
  }
}
