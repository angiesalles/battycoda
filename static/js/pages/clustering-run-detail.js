/**
 * Clustering Run Detail Page Script
 *
 * Handles auto-refresh of progress for in-progress clustering runs.
 *
 * Expected data attributes on #clustering-run-detail-data:
 * - data-run-status-url: URL for fetching the current run's status
 * - data-is-processing: Whether the run is currently processing ("true" or "false")
 *
 * @module pages/clustering-run-detail
 */

/**
 * Initialize the clustering run detail functionality.
 */
function initClusteringRunDetail() {
  // Get configuration from data attributes
  const pageData = document.getElementById('clustering-run-detail-data');
  if (!pageData) {
    console.warn('Clustering run detail page data element not found');
    return;
  }

  const runStatusUrl = pageData.dataset.runStatusUrl;
  const isProcessing = pageData.dataset.isProcessing === 'true';

  // Only set up auto-refresh if the run is processing
  if (!isProcessing) {
    return;
  }

  if (!runStatusUrl) {
    console.warn('Run status URL not configured');
    return;
  }

  /**
   * Refresh progress for the current run.
   */
  function updateProgress() {
    $.get(runStatusUrl, function (data) {
      if (data.progress !== undefined) {
        // Update the progress bar
        const progress = data.progress;
        $('.progress-bar').css('width', `${progress}%`);
        $('.progress-bar').attr('aria-valuenow', progress);
        $('.progress-bar').text(`${progress.toFixed(1)}%`);

        // Update progress message
        if (data.progress_message) {
          $('#progress-message').text(data.progress_message);
        }

        // If status has changed, reload the page
        if (data.status !== 'in_progress' && data.status !== 'pending') {
          location.reload();
        }
      }
    });
  }

  // Update progress every 3 seconds
  setInterval(updateProgress, 3000);
}

// Initialize when DOM is ready
$(document).ready(initClusteringRunDetail);
