/**
 * Segmentation Parameters Module
 *
 * Handles fetching and displaying segmentation jobs with adaptive polling.
 * Polls more frequently when jobs are in progress, less frequently when idle.
 *
 * Usage:
 * Include this script with URL configuration:
 * <script id="segmentation-params-data" type="application/json">
 * {
 *   "jobsStatusUrl": "{% url 'battycoda_app:segmentation_jobs_status' %}"
 * }
 * </script>
 * <script src="{% static 'js/pages/segmentation-params.js' %}"></script>
 */

// Polling configuration
const ACTIVE_POLLING_INTERVAL = 5000; // 5 seconds when active jobs are running
const IDLE_POLLING_INTERVAL = 30000; // 30 seconds when no active jobs

let refreshInterval = null;

/**
 * Get configuration from page data
 * @returns {Object} Configuration object
 */
function getConfig() {
  const dataElement = document.getElementById('segmentation-params-data');
  if (!dataElement) {
    console.warn('segmentation-params-data element not found');
    return {};
  }
  try {
    return JSON.parse(dataElement.textContent);
  } catch (e) {
    console.error('Error parsing segmentation params data:', e);
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
 * Validate URL for use in the UI
 * @param {string} url - URL to validate
 * @returns {string|null} Valid URL or null
 */
function validateUrl(url) {
  if (!url) return null;
  try {
    const parsed = new URL(url, window.location.origin);
    // Only allow same-origin or relative URLs
    if (parsed.origin === window.location.origin) {
      return url;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Update the jobs display with fetched data
 * @param {Object} data - Jobs data from server
 */
function updateJobsDisplay(data) {
  const loadingElement = document.getElementById('loading-jobs');
  const jobsContentElement = document.getElementById('jobs-content');
  const jobsTableElement = document.getElementById('jobs-table');
  const noJobsMessageElement = document.getElementById('no-jobs-message');
  const errorMessageElement = document.getElementById('error-message');

  // Hide loading, show content
  if (loadingElement) loadingElement.style.display = 'none';
  if (jobsContentElement) jobsContentElement.style.display = 'block';

  // Hide all content containers initially
  if (jobsTableElement) jobsTableElement.style.display = 'none';
  if (noJobsMessageElement) noJobsMessageElement.style.display = 'none';
  if (errorMessageElement) errorMessageElement.style.display = 'none';

  if (data.jobs && data.jobs.length > 0) {
    if (jobsTableElement) {
      jobsTableElement.style.display = 'block';

      const jobsList = document.getElementById('jobs-list');
      if (jobsList) {
        jobsList.innerHTML = '';

        data.jobs.forEach((job) => {
          const row = document.createElement('tr');

          // Format progress bar
          const progressBarClass =
            job.status === 'completed'
              ? 'bg-success'
              : job.status === 'failed'
                ? 'bg-danger'
                : 'bg-primary';
          const progressBar = `
            <div class="progress" style="height: 20px;">
              <div class="progress-bar ${progressBarClass}"
                   role="progressbar"
                   style="width: ${job.progress}%;"
                   aria-valuenow="${job.progress}"
                   aria-valuemin="0"
                   aria-valuemax="100">
                ${job.progress}%
              </div>
            </div>
          `;

          // Format status badge
          let statusBadge;
          if (job.status === 'completed') {
            statusBadge = '<span class="badge badge-success badge-pill px-3 py-2">Completed</span>';
          } else if (job.status === 'failed') {
            statusBadge = '<span class="badge badge-danger badge-pill px-3 py-2">Failed</span>';
          } else if (job.status === 'in_progress') {
            statusBadge =
              '<span class="badge badge-primary badge-pill px-3 py-2">In Progress</span>';
          } else {
            statusBadge = '<span class="badge badge-secondary badge-pill px-3 py-2">Unknown</span>';
          }

          // Add active badge
          if (job.is_active) {
            statusBadge +=
              '<br><span class="badge badge-info mt-1" data-bs-toggle="tooltip" title="Current active segmentation">Active</span>';
          }

          // Add algorithm badge
          if (job.algorithm_name && job.algorithm_name !== 'Manual Import') {
            statusBadge += `
              <br><span class="badge badge-secondary mt-1" data-bs-toggle="tooltip"
              title="${escapeHtml(job.algorithm_type)}">
                <span class="fas fa-cog"></span> ${escapeHtml(job.algorithm_name)}
              </span>
            `;
          }

          // Add manually edited badge
          if (job.manually_edited) {
            statusBadge += `
              <br><span class="badge badge-warning mt-1" data-bs-toggle="tooltip"
              title="This segmentation has been manually edited">
                <span class="fas fa-pen"></span> Manually Edited
              </span>
            `;
          }

          // Add debug visualization badge
          if (job.debug_visualization && job.debug_visualization.url) {
            statusBadge += `
              <br><span class="badge badge-info mt-1 viz-badge" data-bs-toggle="tooltip"
              title="Debug visualization available"
              data-viz-url="${escapeHtml(job.debug_visualization.url)}">
                <span class="fas fa-chart-bar"></span> Debug Viz
              </span>
            `;
          }

          // Build actions buttons
          let actionsHtml = '';
          if (job.status === 'completed') {
            actionsHtml = `
              <a href="${escapeHtml(job.view_url)}" class="btn btn-sm btn-primary" data-bs-toggle="tooltip" data-placement="top" title="View Segments">
                <span class="fas fa-eye"></span>
              </a>
            `;
          } else if (job.status === 'in_progress') {
            actionsHtml = `
              <a href="${escapeHtml(job.view_url)}" class="btn btn-sm btn-info" data-bs-toggle="tooltip" data-placement="top" title="View Details">
                <span class="fas fa-info-circle"></span>
              </a>
            `;
          } else if (job.status === 'failed') {
            actionsHtml = `
              <a href="${escapeHtml(job.retry_url)}" class="btn btn-sm btn-warning" data-bs-toggle="tooltip" data-placement="top" title="Retry">
                <span class="fas fa-sync"></span>
              </a>
            `;
          }

          row.innerHTML = `
            <td><a href="${escapeHtml(job.view_url)}" class="text-decoration-none">${escapeHtml(job.recording_name)}</a></td>
            <td>${escapeHtml(job.name) || 'Unnamed Segmentation'}</td>
            <td><span data-utc-date="${escapeHtml(job.start_time)}" data-date-format="datetime">${new Date(job.start_time).toLocaleString()}</span></td>
            <td>${statusBadge}</td>
            <td><span class="badge badge-info">${job.segments_created || 0}</span></td>
            <td>${progressBar}</td>
            <td>
              <div class="btn-group">
                ${actionsHtml}
              </div>
            </td>
          `;

          jobsList.appendChild(row);
        });

        // Initialize Bootstrap 5 tooltips
        const tooltipTriggerList = [].slice.call(
          document.querySelectorAll('[data-bs-toggle="tooltip"]')
        );
        tooltipTriggerList.forEach(function (tooltipTriggerEl) {
          new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Add click handlers for visualization badges
        document.querySelectorAll('.viz-badge').forEach(function (badge) {
          badge.addEventListener('click', function (e) {
            e.preventDefault();

            const vizUrl = this.getAttribute('data-viz-url');
            const validVizUrl = validateUrl(vizUrl);
            if (!validVizUrl) {
              console.warn('Invalid visualization URL');
              return;
            }

            const vizImage = document.getElementById('vizImage');
            const vizDownloadLink = document.getElementById('vizDownloadLink');

            if (vizImage) vizImage.src = validVizUrl;
            if (vizDownloadLink) vizDownloadLink.href = validVizUrl;

            const vizModalElement = document.getElementById('vizModal');
            if (vizModalElement) {
              const vizModal = new bootstrap.Modal(vizModalElement);
              vizModal.show();
            }
          });
        });
      }
    }
  } else {
    if (noJobsMessageElement) {
      noJobsMessageElement.style.display = 'block';
    }
  }
}

/**
 * Update polling frequency based on job status
 * @param {Array} jobs - Array of job objects
 */
function updatePollingFrequency(jobs) {
  const config = getConfig();

  // Clear existing interval
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }

  // Check if there are any in-progress jobs
  const hasInProgressJobs = jobs && jobs.some((job) => job.status === 'in_progress');
  const interval = hasInProgressJobs ? ACTIVE_POLLING_INTERVAL : IDLE_POLLING_INTERVAL;

  // Create new interval
  refreshInterval = setInterval(function () {
    fetch(config.jobsStatusUrl)
      .then((response) => response.json())
      .then((data) => {
        updateJobsDisplay(data);

        // Check if polling frequency needs to change
        const currentlyHasActiveJobs =
          data.jobs && data.jobs.some((job) => job.status === 'in_progress');

        if (hasInProgressJobs !== currentlyHasActiveJobs) {
          updatePollingFrequency(data.jobs);
        }
      })
      .catch((error) => {
        console.error('Error in auto-refresh:', error);
      });
  }, interval);

  console.log(
    `Polling frequency set to ${interval}ms (${hasInProgressJobs ? 'active' : 'idle'} mode)`
  );
}

/**
 * Fetch segmentation jobs from the server
 */
function fetchSegmentationJobs() {
  const config = getConfig();
  const loadingElement = document.getElementById('loading-jobs');
  const jobsContentElement = document.getElementById('jobs-content');

  if (loadingElement) loadingElement.style.display = 'block';
  if (jobsContentElement) jobsContentElement.style.display = 'none';

  fetch(config.jobsStatusUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then((data) => {
      updateJobsDisplay(data);
      updatePollingFrequency(data.jobs);
    })
    .catch((error) => {
      console.error('Error fetching segmentations:', error);

      if (loadingElement) loadingElement.style.display = 'none';
      if (jobsContentElement) jobsContentElement.style.display = 'block';

      const errorElement = document.getElementById('error-message');
      if (errorElement) {
        errorElement.style.display = 'block';
        errorElement.innerHTML = `
          <div class="alert alert-danger">
            <span class="fas fa-exclamation-triangle me-1"></span> Error loading segmentations: ${escapeHtml(error.message)}
          </div>
          <div class="text-center mt-3">
            <button id="retry-btn" class="btn btn-primary">
              <span class="fas fa-sync me-1"></span> Retry
            </button>
          </div>
        `;

        const retryBtn = document.getElementById('retry-btn');
        if (retryBtn) {
          retryBtn.addEventListener('click', function () {
            fetchSegmentationJobs();
          });
        }
      }
    });
}

/**
 * Initialize the segmentation params module
 */
function init() {
  // Initial jobs fetch
  fetchSegmentationJobs();

  // Refresh when tab becomes visible again
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') {
      fetchSegmentationJobs();
    }
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
