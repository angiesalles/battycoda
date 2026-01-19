/**
 * Batch Review Module
 * Handles filtering and relabeling tasks in the batch review interface
 */
import { getPageData, getCsrfToken } from './utils/page-data.js';
import { escapeHtml } from './utils/html.js';

// Module state (initialized lazily)
let relabelTaskUrl = null;

/**
 * Filter tasks by call type - redirects to URL with call_type parameter
 */
export function filterByCallType() {
  const select = document.getElementById('call-type-filter');
  const selectedCallType = select.value;

  // Update URL with the selected call type
  const url = new URL(window.location);
  url.searchParams.set('call_type', selectedCallType);
  window.location.href = url.toString();
}

/**
 * Relabel a task with a new call type
 * @param {HTMLSelectElement} selectElement - The select element triggering the relabel
 */
export function relabelTask(selectElement) {
  const taskId = selectElement.getAttribute('data-task-id');
  const newLabel = selectElement.value;

  if (!newLabel) {
    return;
  }

  // Lazy-initialize relabelTaskUrl if not set
  if (!relabelTaskUrl) {
    const pageData = getPageData();
    relabelTaskUrl = pageData.relabelTaskUrl;
  }

  // Show loading
  document.getElementById('loading-overlay').style.display = 'flex';

  // Prepare form data
  const formData = new FormData();
  formData.append('task_id', taskId);
  formData.append('new_label', newLabel);
  formData.append('csrfmiddlewaretoken', getCsrfToken());

  fetch(relabelTaskUrl, {
    method: 'POST',
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      document.getElementById('loading-overlay').style.display = 'none';

      if (data.success) {
        // Show success message
        showToast('Task relabeled successfully', 'success');

        // Reload the page to reflect changes
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        showToast('Error: ' + data.error, 'error');
        selectElement.value = ''; // Reset dropdown
      }
    })
    .catch((error) => {
      document.getElementById('loading-overlay').style.display = 'none';
      showToast('Error relabeling task: ' + error, 'error');
      selectElement.value = ''; // Reset dropdown
    });
}

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of toast ('success' or 'error')
 */
export function showToast(message, type) {
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
  toast.style.cssText = 'top: 20px; right: 20px; z-index: 10000; min-width: 300px;';
  toast.innerHTML = `
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

  document.body.appendChild(toast);

  // Remove toast after 5 seconds
  setTimeout(() => {
    if (toast && toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 5000);
}

/**
 * Initialize the batch review module
 * Sets up event listeners for filter and relabel functionality
 */
export function initialize() {
  // Pre-fetch page data for relabel URL
  const pageData = getPageData();
  relabelTaskUrl = pageData.relabelTaskUrl;

  // Set up call type filter listener
  const callTypeFilter = document.getElementById('call-type-filter');
  if (callTypeFilter) {
    callTypeFilter.addEventListener('change', filterByCallType);
  }

  // Set up relabel dropdown listeners (multiple dropdowns on page)
  const relabelDropdowns = document.querySelectorAll('.relabel-dropdown');
  relabelDropdowns.forEach((dropdown) => {
    dropdown.addEventListener('change', function () {
      relabelTask(this);
    });
  });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}
