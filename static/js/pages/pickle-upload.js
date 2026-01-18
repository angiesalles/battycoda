/**
 * Pickle Upload Page Module
 *
 * Handles pickle file upload for segmentation via AJAX.
 *
 * Usage:
 * Include this script with URL configuration:
 * <script id="pickle-upload-data" type="application/json">
 * {
 *   "uploadUrl": "{% url 'battycoda_app:upload_pickle_segments' recording.id %}",
 *   "redirectUrl": "{% url 'battycoda_app:recording_detail' recording_id=recording.id %}"
 * }
 * </script>
 * <script src="{% static 'js/pages/pickle-upload.js' %}"></script>
 */

/**
 * Get configuration from page data
 * @returns {Object} Configuration object
 */
function getPickleUploadConfig() {
  const dataElement = document.getElementById('pickle-upload-data');
  if (!dataElement) {
    console.warn('pickle-upload-data element not found');
    return {};
  }
  try {
    return JSON.parse(dataElement.textContent);
  } catch {
    console.error('Error parsing pickle upload data');
    return {};
  }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Show an alert message before the form
 * @param {HTMLElement} form - The form element
 * @param {string} message - Message to display
 * @param {string} type - Alert type: 'success' or 'danger'
 */
function showAlert(form, message, type) {
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type}`;
  alertDiv.innerHTML = type === 'danger' ? `Error: ${escapeHtml(message)}` : escapeHtml(message);
  form.parentNode.insertBefore(alertDiv, form);
}

/**
 * Setup the pickle upload form handler
 */
function setupPickleUploadForm() {
  // Skip if Vite file_upload module is active
  if (window.advancedUploadInitialized) {
    return;
  }

  const form = document.getElementById('pickle-upload-form');
  if (!form) return;

  const config = getPickleUploadConfig();

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;

    // Show loading indicator
    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';

    // Create FormData object
    const formData = new FormData(form);

    // Submit form via fetch
    fetch(config.uploadUrl, {
      method: 'POST',
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Show success message
          const message = data.message || 'Pickle file processed successfully.';
          showAlert(form, message, 'success');

          // Redirect after short delay
          setTimeout(() => {
            window.location.href = data.redirect_url || config.redirectUrl;
          }, 1500);
        } else {
          // Show error message
          const errorMsg = data.error || 'An unknown error occurred.';
          showAlert(form, errorMsg, 'danger');
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
        }
      })
      .catch((error) => {
        console.error('Upload error:', error);
        showAlert(form, 'Server error occurred.', 'danger');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      });
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupPickleUploadForm);
} else {
  setupPickleUploadForm();
}
