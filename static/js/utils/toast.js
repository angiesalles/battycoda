/**
 * Bootstrap 5 Toast Notifications
 *
 * Drop-in replacement for toastr using Bootstrap's native Toast component.
 * Provides a simple imperative API: showToast(message, type)
 *
 * @module utils/toast
 */

const ICONS = {
  success: 'fas fa-check-circle',
  error: 'fas fa-exclamation-circle',
  warning: 'fas fa-exclamation-triangle',
  info: 'fas fa-info-circle',
};

const BG_CLASSES = {
  success: 'text-bg-success',
  error: 'text-bg-danger',
  warning: 'text-bg-warning',
  info: 'text-bg-info',
};

let container = null;

function getContainer() {
  if (!container) {
    container = document.getElementById('toast-container');
  }
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1090';
    document.body.appendChild(container);
  }
  return container;
}

/**
 * Show a toast notification.
 *
 * @param {string} message - The message to display
 * @param {string} [type='info'] - One of 'success', 'error', 'warning', 'info'
 * @param {object} [options] - Optional overrides
 * @param {number} [options.delay=5000] - Auto-hide delay in ms
 * @param {string} [options.title] - Optional title (shown bold before message)
 */
export function showToast(message, type = 'info', options = {}) {
  const delay = options.delay || 5000;
  const bgClass = BG_CLASSES[type] || BG_CLASSES.info;
  const icon = ICONS[type] || ICONS.info;

  const toast = document.createElement('div');
  toast.className = `toast align-items-center border-0 ${bgClass}`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');

  const title = options.title ? `<strong>${options.title}</strong> ` : '';

  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <i class="${icon} me-2"></i>${title}${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  getContainer().appendChild(toast);

  const bsToast = new bootstrap.Toast(toast, { delay });
  bsToast.show();

  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

// Convenience methods matching the toastr API
export const toast = {
  success: (message, title) => showToast(message, 'success', { title }),
  error: (message, title) => showToast(message, 'error', { title }),
  warning: (message, title) => showToast(message, 'warning', { title }),
  info: (message, title) => showToast(message, 'info', { title }),
};

// Expose globally for non-module scripts
window.showToast = showToast;
window.toast = toast;
