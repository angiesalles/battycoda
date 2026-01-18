/**
 * Classification Job Detail Page Script
 *
 * Handles auto-refresh of progress bar for in-progress classifier training jobs.
 *
 * Expected data attributes on #job-detail-data:
 * - data-job-id: The ID of the job
 * - data-job-status: Current status of the job (pending, in_progress, completed, failed)
 * - data-status-url: URL for fetching job status
 *
 * Usage in Django templates:
 * ```html
 * <div id="job-detail-data"
 *      data-job-id="{{ job.id }}"
 *      data-job-status="{{ job.status }}"
 *      data-status-url="/automation/classifiers/{{ job.id }}/status/"
 *      hidden>
 * </div>
 * <script src="{% static 'js/pages/classification-job-detail.js' %}"></script>
 * ```
 *
 * @module pages/classification-job-detail
 */

/**
 * Initialize job detail auto-refresh functionality.
 */
function initJobDetailAutoRefresh() {
  const pageData = document.getElementById('job-detail-data');
  if (!pageData) {
    console.warn('Job detail data element not found');
    return;
  }

  const jobStatus = pageData.dataset.jobStatus;
  const statusUrl = pageData.dataset.statusUrl;

  // Only set up polling for pending or in-progress jobs
  if (jobStatus !== 'pending' && jobStatus !== 'in_progress') {
    return;
  }

  if (!statusUrl) {
    console.warn('Status URL not configured');
    return;
  }

  // Check status every 5 seconds
  const statusInterval = setInterval(function () {
    fetch(statusUrl)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Update progress bar
          const progressBar = document.querySelector('.progress-bar');
          const progressText = document.querySelector('.d-flex span');

          if (progressBar) {
            progressBar.style.width = `${data.progress}%`;
            progressBar.setAttribute('aria-valuenow', data.progress);
            progressBar.textContent = `${data.progress.toFixed(1)}%`;
          }

          if (progressText) {
            progressText.textContent = `${data.progress.toFixed(1)}%`;
          }

          // If status changed, reload page
          if (data.status !== jobStatus) {
            clearInterval(statusInterval);
            window.location.reload();
          }
        }
      })
      .catch((error) => {
        console.error('Error fetching job status:', error);
      });
  }, 5000);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initJobDetailAutoRefresh);
} else {
  initJobDetailAutoRefresh();
}
