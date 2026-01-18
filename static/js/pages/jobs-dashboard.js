/**
 * Jobs Dashboard Page Script
 *
 * Handles auto-refresh of job counters, manual refresh, and job cancellation.
 * Reads configuration from #jobs-page-data data attributes.
 *
 * Expected data attributes on #jobs-page-data:
 * - data-job-status-url: URL for fetching job status
 * - data-cancel-job-url-template: URL template for cancelling jobs (with PLACEHOLDER and 0)
 * - data-csrf-token: CSRF token for POST requests
 *
 * @module pages/jobs-dashboard
 */

/**
 * Initialize the jobs dashboard functionality.
 */
function initJobsDashboard() {
  // Get configuration from data attributes
  const pageData = document.getElementById('jobs-page-data');
  if (!pageData) {
    console.warn('Jobs page data element not found');
    return;
  }

  const jobStatusUrl = pageData.dataset.jobStatusUrl;
  const cancelJobUrlTemplate = pageData.dataset.cancelJobUrlTemplate;
  const csrfToken = pageData.dataset.csrfToken;

  if (!jobStatusUrl) {
    console.warn('Job status URL not configured');
    return;
  }

  let autoRefreshInterval = null;
  let autoRefreshEnabled = true;

  const refreshButton = document.getElementById('refresh-jobs');
  const autoRefreshToggle = document.getElementById('auto-refresh-toggle');

  /**
   * Fetch and update job counters.
   */
  function refreshJobsData() {
    fetch(jobStatusUrl)
      .then((response) => response.json())
      .then((data) => {
        // Update counters
        const segmentationCount = document.getElementById('segmentation-count');
        const detectionCount = document.getElementById('detection-count');
        const trainingCount = document.getElementById('training-count');
        const clusteringCount = document.getElementById('clustering-count');
        const spectrogramCount = document.getElementById('spectrogram-count');

        if (segmentationCount) segmentationCount.textContent = data.segmentation_jobs.length;
        if (detectionCount) detectionCount.textContent = data.detection_jobs.length;
        if (trainingCount) trainingCount.textContent = data.training_jobs.length;
        if (clusteringCount) clusteringCount.textContent = data.clustering_jobs.length;
        if (spectrogramCount) spectrogramCount.textContent = data.spectrogram_jobs.length;

        // Update last refresh time
        const now = new Date().toLocaleTimeString();
        console.log('Jobs refreshed at:', now);
      })
      .catch((error) => {
        console.error('Error refreshing jobs:', error);
      });
  }

  // Manual refresh
  if (refreshButton) {
    refreshButton.addEventListener('click', function () {
      refreshJobsData();
      // Reload the page to update the full tables
      window.location.reload();
    });
  }

  // Auto-refresh toggle
  if (autoRefreshToggle) {
    autoRefreshToggle.addEventListener('click', function () {
      autoRefreshEnabled = !autoRefreshEnabled;

      if (autoRefreshEnabled) {
        autoRefreshToggle.innerHTML = '<i class="fas fa-pause"></i> Auto-refresh: ON';
        autoRefreshToggle.classList.remove('btn-outline-secondary');
        autoRefreshToggle.classList.add('btn-outline-success');

        // Start auto-refresh every 30 seconds
        autoRefreshInterval = setInterval(refreshJobsData, 30000);
      } else {
        autoRefreshToggle.innerHTML = '<i class="fas fa-play"></i> Auto-refresh: OFF';
        autoRefreshToggle.classList.remove('btn-outline-success');
        autoRefreshToggle.classList.add('btn-outline-secondary');

        // Stop auto-refresh
        if (autoRefreshInterval) {
          clearInterval(autoRefreshInterval);
          autoRefreshInterval = null;
        }
      }
    });
  }

  // Start auto-refresh by default
  if (autoRefreshEnabled) {
    autoRefreshInterval = setInterval(refreshJobsData, 30000);
  }

  // Job cancellation
  document.querySelectorAll('.cancel-job').forEach((button) => {
    button.addEventListener('click', function () {
      const jobType = this.dataset.jobType;
      const jobId = this.dataset.jobId;

      if (!cancelJobUrlTemplate) {
        console.error('Cancel job URL template not configured');
        return;
      }

      if (confirm('Are you sure you want to cancel this job?')) {
        const cancelUrl = cancelJobUrlTemplate.replace('PLACEHOLDER', jobType).replace('0', jobId);

        fetch(cancelUrl, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              // Reload the page to show updated status
              window.location.reload();
            } else {
              alert('Error cancelling job: ' + data.error);
            }
          })
          .catch((error) => {
            console.error('Error:', error);
            alert('Error cancelling job');
          });
      }
    });
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initJobsDashboard);
} else {
  initJobsDashboard();
}
