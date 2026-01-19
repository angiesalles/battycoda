/**
 * Run Detail Page Module
 * Handles auto-refresh progress, search filtering, and probability highlighting
 */

/**
 * Set up auto-refresh for in-progress classification runs
 * @param {Object} options - Configuration options
 * @param {string} options.statusUrl - URL to fetch status updates
 * @param {HTMLElement} options.progressBar - Progress bar element
 * @param {number} [options.refreshInterval=3000] - Refresh interval in ms
 * @returns {number|null} - Interval ID or null if not started
 */
export function setupAutoRefresh(options = {}) {
  const { statusUrl, progressBar, refreshInterval = 3000 } = options;

  if (!statusUrl || !progressBar) {
    return null;
  }

  return setInterval(function () {
    fetch(statusUrl)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          progressBar.style.width = `${data.progress}%`;
          progressBar.setAttribute('aria-valuenow', data.progress);
          progressBar.textContent = `${data.progress.toFixed(1)}%`;

          if (data.status !== 'in_progress') {
            // Status changed - reload page to show final state
            window.location.reload();
          }
        }
      })
      .catch((error) => {
        console.error('Error fetching status:', error);
      });
  }, refreshInterval);
}

/**
 * Set up search filtering for the results table
 * @param {HTMLInputElement} searchInput - The search input element
 * @param {HTMLTableElement} resultsTable - The results table element
 */
export function setupSearchFilter(searchInput, resultsTable) {
  if (!searchInput || !resultsTable) {
    return;
  }

  searchInput.addEventListener('keyup', function () {
    const searchTerm = this.value.toLowerCase();
    const rows = resultsTable.querySelectorAll('tbody tr');

    rows.forEach(function (row) {
      const text = row.textContent.toLowerCase();
      const display = text.includes(searchTerm) ? '' : 'none';
      row.style.display = display;
    });
  });
}

/**
 * Highlight the highest probability cell in each row
 * @param {NodeList|Array} rows - Table rows to process
 */
export function highlightHighestProbabilities(rows) {
  if (!rows || rows.length === 0) {
    return;
  }

  rows.forEach((row) => {
    let highestValue = 0;
    let highestCell = null;

    // Find the highest probability cell
    row.querySelectorAll('.probability-cell').forEach((cell) => {
      const value = parseFloat(cell.dataset.value);
      if (value > highestValue) {
        highestValue = value;
        highestCell = cell;
      }
    });

    // Apply highlighting to the highest probability cell
    if (highestCell) {
      // Style the progress bar
      const progressBar = highestCell.querySelector('.progress-bar');
      if (progressBar) {
        progressBar.classList.remove('bg-info');
        progressBar.classList.add('bg-success');
      }

      // Make the value text bold and slightly larger
      highestCell.classList.add('fw-bold');

      // Add a highlight effect to the entire cell
      highestCell.style.backgroundColor = 'rgba(40, 167, 69, 0.1)'; // Light green background
      highestCell.style.borderLeft = '3px solid #28a745'; // Green left border

      // Make the value more visible
      const valueSpan = highestCell.querySelector('span');
      if (valueSpan) {
        valueSpan.style.color = '#28a745'; // Green text
        valueSpan.style.fontSize = '1.05em'; // Slightly larger
      }

      // Add a "Highest Probability" tooltip
      highestCell.setAttribute('title', 'Highest Probability');
      highestCell.style.cursor = 'help';
    }
  });
}

/**
 * Initialize the run detail page
 * Sets up auto-refresh, search, and probability highlighting
 */
export function initialize() {
  // Auto-refresh progress information for in-progress runs
  const statusBadge = document.querySelector('.badge');

  if (statusBadge && statusBadge.classList.contains('bg-info')) {
    const runConfig = document.getElementById('run-config');
    const statusUrl = runConfig?.dataset.statusUrl;
    const progressBar = document.querySelector('.progress-bar');

    if (statusUrl && progressBar) {
      setupAutoRefresh({ statusUrl, progressBar });
    } else if (!statusUrl) {
      console.warn('Status URL not found in run-config');
    }
  }

  // Search functionality for results table
  const searchInput = document.getElementById('resultsSearch');
  const resultsTable = document.getElementById('resultsTable');
  setupSearchFilter(searchInput, resultsTable);

  // Highlight highest probability in each row
  const rows = document.querySelectorAll('tbody tr');
  highlightHighestProbabilities(rows);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}
