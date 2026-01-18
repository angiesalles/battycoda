/**
 * Spectrogram Job Module
 *
 * Handles creating spectrogram generation jobs from the recording detail page.
 *
 * Usage:
 * Include this script on the recording detail page with URL and CSRF data:
 * <script id="spectrogram-job-data" type="application/json">
 * {
 *   "createJobUrlTemplate": "{% url 'battycoda_app:create_spectrogram_job' recording_id=0 %}",
 *   "csrfToken": "{{ csrf_token }}"
 * }
 * </script>
 * <script src="{% static 'js/recordings/spectrogram-job.js' %}"></script>
 */

/**
 * Get configuration from page data
 * @returns {Object} Configuration object
 */
function getConfig() {
  const dataElement = document.getElementById('spectrogram-job-data');
  if (!dataElement) {
    console.warn('spectrogram-job-data element not found');
    return {};
  }
  try {
    return JSON.parse(dataElement.textContent);
  } catch (e) {
    console.error('Error parsing spectrogram job data:', e);
    return {};
  }
}

/**
 * Setup the spectrogram job creation button
 */
function setupSpectrogramJobButton() {
  const createSpectrogramBtn = document.getElementById('createSpectrogramJobBtn');

  if (!createSpectrogramBtn) return;

  const config = getConfig();

  createSpectrogramBtn.addEventListener('click', function () {
    const recordingId = this.dataset.recordingId;
    const btn = this;

    // Disable button and show loading state
    btn.disabled = true;
    btn.innerHTML = '<span class="fas fa-spinner fa-spin me-1"></span> Creating Job...';

    // Build the URL by replacing the placeholder
    const url = config.createJobUrlTemplate.replace('/0/', `/${recordingId}/`);

    // Create the spectrogram job
    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': config.csrfToken,
        'Content-Type': 'application/json',
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Show success message
          if (typeof toastr !== 'undefined') {
            toastr.success(data.message);
          }

          // Update button to show success state temporarily
          btn.innerHTML = '<span class="fas fa-check me-1"></span> Job Created!';

          // Reset button after 3 seconds
          setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = '<span class="fas fa-chart-line me-1"></span> Generate Spectrogram';
          }, 3000);
        } else {
          // Show error message
          if (typeof toastr !== 'undefined') {
            toastr.error(data.error || 'Failed to create spectrogram job');
          }

          // Reset button
          btn.disabled = false;
          btn.innerHTML = '<span class="fas fa-chart-line me-1"></span> Generate Spectrogram';
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        if (typeof toastr !== 'undefined') {
          toastr.error('Failed to create spectrogram job');
        }

        // Reset button
        btn.disabled = false;
        btn.innerHTML = '<span class="fas fa-chart-line me-1"></span> Generate Spectrogram';
      });
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupSpectrogramJobButton);
} else {
  setupSpectrogramJobButton();
}
