/**
 * DateTime Formatter Module
 *
 * Converts UTC timestamps to local time for display.
 * Looks for elements with data-utc-date attribute and formats them.
 */

/**
 * Format all datetime elements in a container
 * @param {HTMLElement|Document} container - Container to search for elements
 */
export function formatDateTimeElements(container = document) {
  const utcDateElements = container.querySelectorAll('[data-utc-date]');

  utcDateElements.forEach(function (element) {
    const utcDateStr = element.getAttribute('data-utc-date');
    if (utcDateStr) {
      const date = new Date(utcDateStr);
      const format = element.getAttribute('data-date-format') || 'full';

      let formattedDate;
      if (format === 'date') {
        // Date only: Feb 5, 2023
        formattedDate = date.toLocaleDateString();
      } else if (format === 'time') {
        // Time only: 14:30:45
        formattedDate = date.toLocaleTimeString();
      } else if (format === 'datetime') {
        // Date and time: Feb 5, 2023, 14:30
        formattedDate =
          date.toLocaleDateString() +
          ' ' +
          date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else {
        // Full date and time (default)
        formattedDate = date.toLocaleString();
      }

      element.textContent = formattedDate;
    }
  });
}

/**
 * Initialize datetime formatting on page load
 */
export function initialize() {
  formatDateTimeElements();
}

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

// Expose globally for AJAX content updates
window.formatDateTimeElements = formatDateTimeElements;
