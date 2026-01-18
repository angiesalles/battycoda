/**
 * Application Initialization
 *
 * This module handles core application initialization including:
 * - Maisonnette App.init()
 * - Select2 initialization on form controls
 * - Toastr notification configuration
 * - Display of Django flash messages
 * - Management features activation handler
 *
 * Configuration is read from data attributes on #app-config element.
 *
 * @module core/app-init
 */

/**
 * Configure toastr notification options.
 */
function configureToastr() {
  if (typeof toastr === 'undefined') {
    console.warn('Toastr not loaded, skipping configuration');
    return;
  }

  toastr.options = {
    closeButton: true,
    debug: false,
    newestOnTop: true,
    progressBar: true,
    positionClass: 'toast-top-right',
    preventDuplicates: false,
    onclick: null,
    showDuration: '300',
    hideDuration: '1000',
    timeOut: '5000',
    extendedTimeOut: '1000',
    showEasing: 'swing',
    hideEasing: 'linear',
    showMethod: 'fadeIn',
    hideMethod: 'fadeOut',
  };
}

/**
 * Display Django flash messages using toastr.
 *
 * Reads messages from #django-messages script tag (JSON format).
 */
function displayDjangoMessages() {
  const messagesEl = document.getElementById('django-messages');
  if (!messagesEl) return;

  try {
    const messages = JSON.parse(messagesEl.textContent);
    if (!Array.isArray(messages)) return;

    messages.forEach((msg) => {
      const level = msg.level || 'info';
      const text = msg.message || '';

      switch (level) {
        case 'success':
          toastr.success(text);
          break;
        case 'warning':
          toastr.warning(text);
          break;
        case 'error':
          toastr.error(text);
          break;
        case 'info':
        default:
          toastr.info(text);
          break;
      }
    });
  } catch (e) {
    console.warn('Failed to parse Django messages:', e);
  }
}

/**
 * Initialize Select2 on all select elements with form-control class.
 */
function initializeSelect2() {
  if (typeof $ === 'undefined' || typeof $.fn.select2 === 'undefined') {
    console.warn('jQuery or Select2 not loaded, skipping initialization');
    return;
  }

  $('select.form-control').select2({
    width: '100%',
  });
}

/**
 * Set up the management features activation handler.
 *
 * This function is exposed globally as window.activateManagementFeatures
 * for backwards compatibility with onclick handlers.
 */
function setupManagementFeatures() {
  const configEl = document.getElementById('app-config');
  if (!configEl) return;

  const updateProfileUrl = configEl.dataset.updateProfileUrl;
  const csrfToken = configEl.dataset.csrfToken;
  const isAuthenticated = configEl.dataset.userAuthenticated === 'true';

  window.activateManagementFeatures = function () {
    if (!isAuthenticated) {
      toastr.error('You must be logged in to activate management features.');
      return;
    }

    if (!updateProfileUrl) {
      toastr.error('Configuration error: update profile URL not available.');
      return;
    }

    $.ajax({
      url: updateProfileUrl,
      type: 'POST',
      data: {
        action: 'update_management_features',
        enabled: 'true',
        csrfmiddlewaretoken: csrfToken,
      },
      success: function (response) {
        if (response.success) {
          toastr.success(response.message);
          // Reload the page to show the new menu items
          setTimeout(function () {
            window.location.reload();
          }, 1000);
        } else {
          toastr.error(response.message);
        }
      },
      error: function () {
        toastr.error('Failed to activate management features. Please try again.');
      },
    });
  };
}

/**
 * Main initialization function.
 */
function initializeApp() {
  // Initialize Maisonnette App
  if (typeof App !== 'undefined' && typeof App.init === 'function') {
    App.init();
  }

  // Initialize Select2
  initializeSelect2();

  // Configure toastr
  configureToastr();

  // Display Django messages
  displayDjangoMessages();

  // Set up management features handler
  setupManagementFeatures();
}

// Initialize when DOM is ready (jQuery version for compatibility)
if (typeof $ !== 'undefined') {
  $(document).ready(initializeApp);
} else if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
