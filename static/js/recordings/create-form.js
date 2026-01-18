/**
 * Recording Create Form Module
 *
 * Handles form validation for recording creation, including WAV file validation.
 * Also applies Bootstrap classes to form inputs.
 *
 * Usage:
 * Include this script on the create recording page:
 * <script id="recording-form-data" type="application/json">
 * {
 *   "wavFileInputId": "id_wav_file"
 * }
 * </script>
 * <script src="{% static 'js/recordings/create-form.js' %}"></script>
 */

/**
 * Get configuration from page data
 * @returns {Object} Configuration object
 */
function getFormConfig() {
  const dataElement = document.getElementById('recording-form-data');
  if (!dataElement) {
    // Use default ID if no config provided
    return { wavFileInputId: 'id_wav_file' };
  }
  try {
    return JSON.parse(dataElement.textContent);
  } catch (e) {
    console.error('Error parsing recording form data:', e);
    return { wavFileInputId: 'id_wav_file' };
  }
}

/**
 * Add Bootstrap form-control class to inputs that don't have it
 */
function applyBootstrapFormClasses() {
  const formInputs = document.querySelectorAll('input, select, textarea');
  formInputs.forEach((input) => {
    if (
      !input.classList.contains('form-check-input') &&
      !input.classList.contains('form-control') &&
      input.type !== 'hidden'
    ) {
      input.classList.add('form-control');
    }
  });
}

/**
 * Setup form validation
 */
function setupFormValidation() {
  // Only run legacy validation if Vite file_upload is not active
  if (window.advancedUploadInitialized) {
    return;
  }

  const config = getFormConfig();
  const form = document.getElementById('recording-form');

  if (!form) return;

  form.addEventListener('submit', function (event) {
    const wavFileInput = document.getElementById(config.wavFileInputId);
    if (wavFileInput && wavFileInput.files.length === 0) {
      event.preventDefault();
      alert('Please select a WAV file to upload.');
      return false;
    }
  });
}

/**
 * Initialize the module
 */
function init() {
  applyBootstrapFormClasses();
  setupFormValidation();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
