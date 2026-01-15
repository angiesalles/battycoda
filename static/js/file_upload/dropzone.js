/**
 * Dropzone - Drag and drop file selection
 *
 * Creates enhanced dropzone UI for file inputs with drag-and-drop support.
 */

/**
 * Create a dropzone wrapper around a file input
 * @param {HTMLInputElement} fileInput - The file input element to wrap
 */
export function setupDropzone(fileInput) {
  if (!fileInput) return;

  const dropArea = document.createElement('div');
  dropArea.className =
    'file-dropzone p-4 mb-3 text-center border border-secondary rounded';

  // Change wording for multiple files
  const isMultiple = fileInput.multiple;
  const uploadText = isMultiple
    ? 'Drag & drop your files here or click to browse'
    : 'Drag & drop your file here or click to browse';
  const selectedText = isMultiple ? 'Selected files:' : 'Selected file:';

  dropArea.innerHTML = `
    <div class="file-icon mb-2"><i class="fas fa-file-upload fa-2x"></i></div>
    <p>${uploadText}</p>
    <small class="text-muted">${selectedText} <span class="selected-filename">None</span></small>
  `;

  // Insert dropzone before fileInput
  fileInput.parentNode.insertBefore(dropArea, fileInput);

  // Hide the original input
  fileInput.style.display = 'none';

  // Click on dropzone should trigger file input
  dropArea.addEventListener('click', () => {
    fileInput.click();
  });

  // Update dropzone when file is selected
  fileInput.addEventListener('change', () => {
    updateDropzoneDisplay(dropArea, fileInput, isMultiple);
  });

  // Setup drag and drop handlers
  setupDragAndDrop(dropArea, fileInput);
}

/**
 * Update the dropzone display when files are selected
 * @param {HTMLElement} dropArea - The dropzone element
 * @param {HTMLInputElement} fileInput - The file input
 * @param {boolean} isMultiple - Whether multiple files are allowed
 */
function updateDropzoneDisplay(dropArea, fileInput, isMultiple) {
  const filenameSpan = dropArea.querySelector('.selected-filename');
  if (fileInput.files.length > 0) {
    if (isMultiple && fileInput.files.length > 1) {
      const totalSize = Array.from(fileInput.files).reduce(
        (sum, file) => sum + file.size,
        0,
      );
      const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);
      filenameSpan.textContent = `${fileInput.files.length} files selected (${totalSizeMB} MB)`;
    } else {
      const fileName = fileInput.files[0].name;
      const fileSize = (fileInput.files[0].size / (1024 * 1024)).toFixed(2);
      filenameSpan.textContent = `${fileName} (${fileSize} MB)`;
    }
    dropArea.classList.add('border-success');
    dropArea.classList.remove('border-secondary');
  } else {
    filenameSpan.textContent = 'None';
    dropArea.classList.remove('border-success');
    dropArea.classList.add('border-secondary');
  }
}

/**
 * Setup drag and drop event handlers
 * @param {HTMLElement} dropArea - The dropzone element
 * @param {HTMLInputElement} fileInput - The file input
 */
function setupDragAndDrop(dropArea, fileInput) {
  // Prevent default drag behaviors
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  // Visual feedback during drag
  ['dragenter', 'dragover'].forEach((eventName) => {
    dropArea.addEventListener(eventName, () => {
      dropArea.classList.add('border-primary', 'bg-dark');
    });
  });

  ['dragleave', 'drop'].forEach((eventName) => {
    dropArea.addEventListener(eventName, () => {
      dropArea.classList.remove('border-primary', 'bg-dark');
    });
  });

  // Handle the actual drop
  dropArea.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;

    if (files.length > 0) {
      const dataTransfer = new DataTransfer();

      if (fileInput.multiple) {
        // Add all dropped files for multiple inputs
        for (let i = 0; i < files.length; i++) {
          dataTransfer.items.add(files[i]);
        }
      } else {
        // Only use first file for single inputs
        dataTransfer.items.add(files[0]);
      }

      fileInput.files = dataTransfer.files;

      // Trigger change event
      fileInput.dispatchEvent(new Event('change'));
    }
  });
}
