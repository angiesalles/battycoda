/**
 * Clustering Dashboard Page Script
 *
 * Handles auto-refresh of progress for in-progress clustering runs.
 *
 * Expected data attributes on #clustering-dashboard-data:
 * - data-run-status-url-template: URL template for fetching run status (with {run_id})
 *
 * @module pages/clustering-dashboard
 */

/**
 * Initialize the clustering dashboard functionality.
 */
function initClusteringDashboard() {
  // Get configuration from data attributes
  const pageData = document.getElementById('clustering-dashboard-data');
  if (!pageData) {
    console.warn('Clustering dashboard page data element not found');
    return;
  }

  const runStatusUrlTemplate = pageData.dataset.runStatusUrlTemplate;

  if (!runStatusUrlTemplate) {
    console.warn('Run status URL template not configured');
    return;
  }

  /**
   * Update progress for in-progress runs.
   */
  function updateProgress() {
    $('tr').each(function () {
      const statusBadge = $(this).find('td:nth-child(4) .badge');
      const status = statusBadge.text().trim();

      if (status === 'in_progress' || status === 'pending') {
        const link = $(this).find('td:nth-child(1) a');
        if (!link.length) return;

        const href = link.attr('href');
        if (!href) return;

        // Extract run ID from the URL (e.g., /clustering/run/123/)
        const match = href.match(/\/run\/(\d+)\//);
        if (!match) return;

        const runId = match[1];
        const statusUrl = runStatusUrlTemplate.replace('{run_id}', runId);

        $.get(
          statusUrl,
          function (data) {
            if (data.status && data.progress !== undefined) {
              const progressBar = $(this).find('.progress-bar');
              if (progressBar.length) {
                progressBar.css('width', `${data.progress}%`);
                progressBar.attr('aria-valuenow', data.progress);
                progressBar.text(`${Math.floor(data.progress)}%`);
              }

              // Update status badge if it changed
              if (data.status !== status) {
                location.reload(); // Just reload the page if status changed
              }
            }
          }.bind(this)
        );
      }
    });
  }

  // Update progress every 5 seconds
  setInterval(updateProgress, 5000);
}

// Initialize when DOM is ready
$(document).ready(initClusteringDashboard);
