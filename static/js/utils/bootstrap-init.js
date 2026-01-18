/**
 * Bootstrap Component Auto-Initialization
 *
 * This module automatically initializes common Bootstrap components
 * on page load, eliminating the need for inline scripts in templates.
 *
 * Initializes:
 * - Tooltips: Any element with data-bs-toggle="tooltip"
 * - Popovers: Any element with data-bs-toggle="popover"
 *
 * @module utils/bootstrap-init
 */

/**
 * Initialize all Bootstrap tooltips on the page.
 */
function initializeTooltips() {
  if (typeof bootstrap === 'undefined' || typeof bootstrap.Tooltip === 'undefined') {
    console.warn('Bootstrap not loaded, skipping tooltip initialization');
    return;
  }

  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggerList.forEach((tooltipTriggerEl) => {
    new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

/**
 * Initialize all Bootstrap popovers on the page.
 */
function initializePopovers() {
  if (typeof bootstrap === 'undefined' || typeof bootstrap.Popover === 'undefined') {
    console.warn('Bootstrap not loaded, skipping popover initialization');
    return;
  }

  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  popoverTriggerList.forEach((popoverTriggerEl) => {
    new bootstrap.Popover(popoverTriggerEl);
  });
}

/**
 * Initialize all Bootstrap components.
 */
function initializeBootstrapComponents() {
  initializeTooltips();
  initializePopovers();
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeBootstrapComponents);
} else {
  initializeBootstrapComponents();
}

// Export for manual initialization if needed
export { initializeTooltips, initializePopovers, initializeBootstrapComponents };
