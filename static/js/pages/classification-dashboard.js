/**
 * Classification Dashboard Page Script
 *
 * Handles tab navigation from URL parameters and auto-refresh of progress bars
 * for in-progress classification runs and training jobs.
 *
 * Expected data attributes on #classification-page-data:
 * - data-run-status-url-template: URL template for run status (use {id} as placeholder)
 * - data-job-status-url-template: URL template for job status (use {id} as placeholder)
 *
 * @module pages/classification-dashboard
 */

/**
 * Initialize the classification dashboard functionality.
 */
function initClassificationDashboard() {
  // Initialize tab handling
  initTabNavigation();

  // Initialize auto-refresh for runs and jobs
  initAutoRefresh();
}

/**
 * Initialize tab navigation from URL parameters and click handlers.
 */
function initTabNavigation() {
  // Check URL parameter for tab selection
  const urlParams = new URLSearchParams(window.location.search);
  const tabParam = urlParams.get('tab');

  if (tabParam) {
    const tabButton = document.getElementById(`${tabParam}-tab`);
    const tabContent = document.getElementById(`${tabParam}-content`);

    if (tabButton && tabContent) {
      // Deactivate all tabs
      document.querySelectorAll('.nav-link').forEach(function (navLink) {
        navLink.classList.remove('active');
        navLink.setAttribute('aria-selected', 'false');
      });

      // Hide all tab panes
      document.querySelectorAll('.tab-pane').forEach(function (pane) {
        pane.classList.remove('show', 'active');
      });

      // Activate the requested tab
      tabButton.classList.add('active');
      tabButton.setAttribute('aria-selected', 'true');
      tabContent.classList.add('show', 'active');
    }
  }

  // Initialize Bootstrap tabs click handlers
  const tabs = document.querySelectorAll('button[data-bs-toggle="tab"]');
  tabs.forEach(function (tab) {
    tab.addEventListener('click', function (event) {
      event.preventDefault();

      // Hide all tab panes
      document.querySelectorAll('.tab-pane').forEach(function (pane) {
        pane.classList.remove('show', 'active');
      });

      // Deactivate all tabs
      document.querySelectorAll('.nav-link').forEach(function (navLink) {
        navLink.classList.remove('active');
        navLink.setAttribute('aria-selected', 'false');
      });

      // Activate clicked tab
      this.classList.add('active');
      this.setAttribute('aria-selected', 'true');

      // Show the target pane
      const target = document.querySelector(this.dataset.bsTarget);
      if (target) {
        target.classList.add('show', 'active');
      }
    });
  });
}

/**
 * Initialize auto-refresh for in-progress runs and jobs.
 */
function initAutoRefresh() {
  const pageData = document.getElementById('classification-page-data');

  // Get URL templates from data attributes (optional)
  const runStatusUrlTemplate = pageData ? pageData.dataset.runStatusUrlTemplate : null;
  const jobStatusUrlTemplate = pageData ? pageData.dataset.jobStatusUrlTemplate : null;

  // Auto-refresh progress bars for in-progress runs
  const inProgressRuns = document.querySelectorAll('tr[data-run-id]:has(.badge.bg-info)');

  if (inProgressRuns.length > 0 && runStatusUrlTemplate) {
    setInterval(function () {
      inProgressRuns.forEach(function (row) {
        const runId = row.getAttribute('data-run-id');
        if (!runId) return;

        const statusUrl = runStatusUrlTemplate.replace('{id}', runId);

        fetch(statusUrl)
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              const progressBar = row.querySelector('.progress-bar');

              if (progressBar) {
                progressBar.style.width = `${data.progress}%`;
                progressBar.setAttribute('aria-valuenow', data.progress);
                progressBar.textContent = `${data.progress.toFixed(1)}%`;
              }

              if (data.status !== 'in_progress') {
                window.location.reload(); // Refresh when status changes
              }
            }
          })
          .catch((error) => {
            console.error('Error fetching run status:', error);
          });
      });
    }, 5000); // Check every 5 seconds
  }

  // Auto-refresh progress bars for training jobs
  const inProgressJobs = document.querySelectorAll('tr[data-job-id]:has(.badge.bg-info)');

  if (inProgressJobs.length > 0 && jobStatusUrlTemplate) {
    setInterval(function () {
      inProgressJobs.forEach(function (row) {
        const jobId = row.getAttribute('data-job-id');
        if (!jobId) return;

        const statusUrl = jobStatusUrlTemplate.replace('{id}', jobId);

        fetch(statusUrl)
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              const progressBar = row.querySelector('.progress-bar');

              if (progressBar) {
                progressBar.style.width = `${data.progress}%`;
                progressBar.setAttribute('aria-valuenow', data.progress);
                progressBar.textContent = `${data.progress.toFixed(1)}%`;
              }

              if (data.status !== 'in_progress') {
                window.location.reload(); // Refresh when status changes
              }
            }
          })
          .catch((error) => {
            console.error('Error fetching job status:', error);
          });
      });
    }, 5000); // Check every 5 seconds
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initClassificationDashboard);
} else {
  initClassificationDashboard();
}
