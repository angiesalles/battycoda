/**
 * Pickle Upload Page Module
 *
 * Handles pickle file upload for segmentation via AJAX.
 * Uses jQuery for legacy compatibility.
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
  } catch (e) {
    console.error('Error parsing pickle upload data:', e);
    return {};
  }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtmlPickle(text) {
  if (text === null || text === undefined) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Setup the pickle upload form handler
 */
function setupPickleUploadForm() {
  // Skip if Vite file_upload module is active
  if (window.advancedUploadInitialized) {
    return;
  }

  const config = getPickleUploadConfig();

  // Handle form submission
  $('#pickle-upload-form').on('submit', function (e) {
    e.preventDefault();

    // Show loading indicator
    const submitBtn = $(this).find('button[type="submit"]');
    const originalText = submitBtn.text();
    submitBtn
      .prop('disabled', true)
      .html(
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...'
      );

    // Create FormData object
    const formData = new FormData(this);

    // Submit form via AJAX
    $.ajax({
      url: config.uploadUrl,
      type: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        if (response.success) {
          // Show success message
          const message = response.message || 'Pickle file processed successfully.';
          const alert = `<div class="alert alert-success">${escapeHtmlPickle(message)}</div>`;
          $('#pickle-upload-form').before(alert);

          // Redirect after short delay
          setTimeout(function () {
            window.location.href = response.redirect_url || config.redirectUrl;
          }, 1500);
        } else {
          // Show error message
          const errorMsg = response.error || 'An unknown error occurred.';
          const alert = `<div class="alert alert-danger">Error: ${escapeHtmlPickle(errorMsg)}</div>`;
          $('#pickle-upload-form').before(alert);
          submitBtn.prop('disabled', false).text(originalText);
        }
      },
      error: function (xhr) {
        // Show error message
        let errorMsg = 'Server error occurred.';
        try {
          const response = JSON.parse(xhr.responseText);
          errorMsg = response.error || errorMsg;
        } catch (e) {
          console.error('Error parsing response:', e);
        }

        const alert = `<div class="alert alert-danger">Error: ${escapeHtmlPickle(errorMsg)}</div>`;
        $('#pickle-upload-form').before(alert);
        submitBtn.prop('disabled', false).text(originalText);
      },
    });
  });
}

// Initialize when DOM is ready (jQuery style)
$(document).ready(function () {
  setupPickleUploadForm();
});
