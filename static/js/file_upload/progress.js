/**
 * Progress - Upload progress tracking and display
 *
 * Manages progress bar updates and file info display during uploads.
 */

import { escapeHtml } from '../utils/html.js';

/**
 * @typedef {Object} FileInputs
 * @property {HTMLInputElement|null} wavFileInput - Single WAV file input
 * @property {HTMLInputElement|null} pickleFileInput - Single pickle file input
 * @property {HTMLInputElement|null} wavFilesInput - Multiple WAV files input (batch)
 * @property {HTMLInputElement|null} pickleFilesInput - Multiple pickle files input (batch)
 */

/**
 * @typedef {Object} ProgressElements
 * @property {HTMLElement} progressBar - The progress bar element
 * @property {HTMLElement} progressContainer - Container for progress UI
 * @property {HTMLElement} statusText - Status text element
 */

/**
 * @typedef {Object} FileInfo
 * @property {number} totalSize - Total size of selected files in bytes
 * @property {number} count - Number of files selected
 * @property {string[]} filenames - Array of filenames
 */

/**
 * Calculate total file info from inputs
 * @param {FileInputs} inputs - The file input elements
 * @param {boolean} isBatchUpload - Whether this is a batch upload form
 * @returns {FileInfo} File information
 */
export function getFileInfo(inputs, isBatchUpload) {
  let totalSize = 0;
  let count = 0;
  const filenames = [];

  // Handle pickle-only form type
  if (inputs.formType === 'pickle_only') {
    if (inputs.pickleFileInput?.files.length > 0) {
      totalSize += inputs.pickleFileInput.files[0].size;
      count++;
      filenames.push(inputs.pickleFileInput.files[0].name);
    }
    return { totalSize, count, filenames };
  }

  if (isBatchUpload) {
    // Batch upload form - handle multiple files
    if (inputs.wavFilesInput?.files.length > 0) {
      for (const file of inputs.wavFilesInput.files) {
        totalSize += file.size;
        count++;
        filenames.push(file.name);
      }
    }

    if (inputs.pickleFilesInput?.files.length > 0) {
      for (const file of inputs.pickleFilesInput.files) {
        totalSize += file.size;
        count++;
        filenames.push(file.name);
      }
    }
  } else {
    // Single file upload form
    if (inputs.wavFileInput?.files.length > 0) {
      totalSize += inputs.wavFileInput.files[0].size;
      count++;
      filenames.push(inputs.wavFileInput.files[0].name);
    }

    if (inputs.pickleFileInput?.files.length > 0) {
      totalSize += inputs.pickleFileInput.files[0].size;
      count++;
      filenames.push(inputs.pickleFileInput.files[0].name);
    }
  }

  return { totalSize, count, filenames };
}

/**
 * Update the file info display in the progress container
 * @param {ProgressElements} elements - Progress UI elements
 * @param {FileInfo} fileInfo - File information to display
 */
export function updateFileInfoDisplay(elements, fileInfo) {
  const { progressContainer, statusText } = elements;
  const { totalSize, count, filenames } = fileInfo;

  if (count > 0) {
    const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);

    // Show full file list for small number of files, or summary for many files
    const maxDisplayFiles = 10;
    let fileListHtml = '';

    if (filenames.length <= maxDisplayFiles) {
      fileListHtml = filenames
        .map(
          (name) =>
            `<span class="badge bg-info me-2 mb-1">${escapeHtml(name)}</span>`,
        )
        .join('');
    } else {
      const displayedFiles = filenames.slice(0, maxDisplayFiles);
      const remainingCount = filenames.length - maxDisplayFiles;
      fileListHtml =
        displayedFiles
          .map(
            (name) =>
              `<span class="badge bg-info me-2 mb-1">${escapeHtml(name)}</span>`,
          )
          .join('') +
        `<span class="badge bg-secondary">+${remainingCount} more file${remainingCount > 1 ? 's' : ''}</span>`;
    }

    statusText.innerHTML = `
      <div class="mb-2">Selected ${count} file${count > 1 ? 's' : ''} (${totalSizeMB} MB total)</div>
      <div class="file-badges-container">${fileListHtml}</div>
    `;
    progressContainer.classList.remove('d-none');
  } else {
    progressContainer.classList.add('d-none');
  }
}

/**
 * Update progress bar during upload
 * @param {HTMLElement} progressBar - The progress bar element
 * @param {HTMLElement} statusText - Status text element
 * @param {number} loaded - Bytes loaded
 * @param {number} total - Total bytes
 */
export function updateProgress(progressBar, statusText, loaded, total) {
  // Guard against division by zero - show 0% if total is 0
  const percentComplete = total > 0 ? Math.round((loaded / total) * 100) : 0;

  progressBar.style.width = percentComplete + '%';
  progressBar.textContent = percentComplete + '%';
  progressBar.setAttribute('aria-valuenow', percentComplete);

  if (percentComplete < 100) {
    statusText.textContent = `Uploading files: ${percentComplete}% (${Math.round(loaded / 1048576)}MB / ${Math.round(total / 1048576)}MB)`;
  } else {
    statusText.innerHTML =
      '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Processing files and creating tasks...';
    progressBar.classList.remove('progress-bar-animated');
  }
}

/**
 * Reset progress bar to initial state
 * @param {HTMLElement} progressBar - The progress bar element
 * @param {HTMLElement} statusText - Status text element
 */
export function resetProgress(progressBar, statusText) {
  progressBar.style.width = '0%';
  progressBar.textContent = '0%';
  progressBar.setAttribute('aria-valuenow', 0);
  progressBar.classList.remove('bg-success', 'bg-danger', 'bg-warning');
  progressBar.classList.add(
    'progress-bar-striped',
    'progress-bar-animated',
    'bg-primary',
  );
  statusText.textContent = 'Preparing files for upload...';
}

/**
 * Show success state on progress bar
 * @param {HTMLElement} progressBar - The progress bar element
 * @param {HTMLElement} statusText - Status text element
 * @param {string} [message] - Custom success message (optional)
 */
export function showSuccess(progressBar, statusText, message) {
  const displayMessage =
    message || 'Upload complete! Successfully created batch.';
  statusText.innerHTML = `
    <div class="alert alert-success">
      <i class="fas fa-check-circle me-2"></i>
      ${escapeHtml(displayMessage)}
    </div>
  `;
  progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
  progressBar.classList.add('bg-success');
}

/**
 * Show error state on progress bar
 * @param {HTMLElement} progressBar - The progress bar element
 * @param {HTMLElement} statusText - Status text element
 * @param {string} errorMessage - Error message to display
 */
export function showError(progressBar, statusText, errorMessage) {
  statusText.innerHTML = `
    <div class="alert alert-danger">
      <i class="fas fa-exclamation-circle me-2"></i>
      ${escapeHtml(errorMessage)}
    </div>
  `;
  progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
  progressBar.classList.add('bg-danger');
}

/**
 * Show cancelled state on progress bar
 * @param {HTMLElement} progressBar - The progress bar element
 * @param {HTMLElement} statusText - Status text element
 */
export function showCancelled(progressBar, statusText) {
  statusText.textContent = 'Upload cancelled';
  progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
  progressBar.classList.add('bg-warning');
}
