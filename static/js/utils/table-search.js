/**
 * Table Search Utility
 *
 * Provides simple client-side search functionality for HTML tables.
 * Reads configuration from data attributes on a page data element.
 *
 * Expected data attributes on the page data element:
 * - data-search-input-id: ID of the search input element
 * - data-search-table-id: ID of the table to search in
 *
 * Usage in Django templates:
 * ```html
 * <div id="table-search-data"
 *      data-search-input-id="mySearch"
 *      data-search-table-id="myTable"
 *      hidden>
 * </div>
 * <script src="{% static 'js/utils/table-search.js' %}"></script>
 * ```
 *
 * Or initialize programmatically:
 * ```javascript
 * import { initTableSearch } from './utils/table-search.js';
 * initTableSearch('mySearch', 'myTable');
 * ```
 *
 * @module utils/table-search
 */

/**
 * Initialize table search functionality for a given input and table.
 *
 * @param {string} searchInputId - The ID of the search input element
 * @param {string} tableId - The ID of the table to search in
 * @returns {boolean} True if initialization was successful
 */
export function initTableSearch(searchInputId, tableId) {
  const searchInput = document.getElementById(searchInputId);
  const table = document.getElementById(tableId);

  if (!searchInput) {
    console.warn(`Table search: input element "${searchInputId}" not found`);
    return false;
  }

  if (!table) {
    console.warn(`Table search: table element "${tableId}" not found`);
    return false;
  }

  searchInput.addEventListener('keyup', function () {
    const searchTerm = this.value.toLowerCase();
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach(function (row) {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
  });

  return true;
}

/**
 * Auto-initialize table search from page data element.
 * Looks for #table-search-data element with data attributes.
 */
function autoInit() {
  const pageData = document.getElementById('table-search-data');
  if (!pageData) {
    return; // No auto-init data present
  }

  const searchInputId = pageData.dataset.searchInputId;
  const tableId = pageData.dataset.searchTableId;

  if (searchInputId && tableId) {
    initTableSearch(searchInputId, tableId);
  }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', autoInit);
} else {
  autoInit();
}
