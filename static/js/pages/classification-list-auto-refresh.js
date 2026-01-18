/**
 * Classification List Auto-Refresh Script
 *
 * Handles auto-refresh of progress bars for in-progress classification runs
 * and training jobs in list views.
 *
 * Expected data attributes on #classification-list-data:
 * - data-status-url-template: URL template for status endpoint (use {id} as placeholder)
 * - data-item-attribute: The data attribute name for item IDs (e.g., "run-id" or "job-id")
 *
 * Usage in Django templates:
 * ```html
 * <div id="classification-list-data"
 *      data-status-url-template="/automation/runs/{id}/status/"
 *      data-item-attribute="run-id"
 *      hidden>
 * </div>
 * <script src="{% static 'js/pages/classification-list-auto-refresh.js' %}"></script>
 * ```
 *
 * @module pages/classification-list-auto-refresh
 */

/**
 * Initialize auto-refresh for classification lists.
 */
function initListAutoRefresh() {
  const pageData = document.getElementById('classification-list-data');
  if (!pageData) {
    console.warn('Classification list data element not found');
    return;
  }

  const statusUrlTemplate = pageData.dataset.statusUrlTemplate;
  const itemAttribute = pageData.dataset.itemAttribute;

  if (!statusUrlTemplate) {
    console.warn('Status URL template not configured');
    return;
  }

  if (!itemAttribute) {
    console.warn('Item attribute not configured');
    return;
  }

  // Find in-progress rows (those with the info badge indicating "In Progress")
  const selector = `tr[data-${itemAttribute}]:has(.badge.bg-info)`;
  const inProgressRows = document.querySelectorAll(selector);

  if (inProgressRows.length === 0) {
    return; // No in-progress items, no need to set up polling
  }

  // Set up polling interval
  setInterval(function () {
    inProgressRows.forEach(function (row) {
      const itemId = row.getAttribute(`data-${itemAttribute}`);
      if (!itemId) return;

      const statusUrl = statusUrlTemplate.replace('{id}', itemId);

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
          console.error('Error fetching status:', error);
        });
    });
  }, 5000); // Check every 5 seconds
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initListAutoRefresh);
} else {
  initListAutoRefresh();
}
