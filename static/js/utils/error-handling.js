/**
 * Error Handling Utilities
 *
 * Provides consistent error display with retry capabilities
 * for AJAX operations throughout the clustering interfaces.
 */

import { escapeHtml } from './html.js';

/**
 * Display an error message with optional retry button
 * @param {jQuery} $container - jQuery container element for the error message
 * @param {string} message - Error message to display
 * @param {Object} options - Optional configuration
 * @param {Function} options.onRetry - Callback for retry button
 * @param {string} options.errorCode - Specific error code for debugging
 * @param {string} options.alertClass - Bootstrap alert class (default: alert-danger)
 * @returns {jQuery} The error element for further manipulation
 */
export function showErrorWithRetry($container, message, options = {}) {
  const { onRetry, errorCode, alertClass = 'alert-danger' } = options;

  const errorCodeHtml = errorCode
    ? `<small class="text-muted ms-2">(${escapeHtml(errorCode)})</small>`
    : '';

  const retryButtonHtml = onRetry
    ? '<button class="btn btn-sm btn-outline-danger ms-2 error-retry-btn"><i class="fas fa-redo"></i> Retry</button>'
    : '';

  const errorHtml = `
    <div class="alert ${alertClass} alert-dismissible d-flex align-items-center" role="alert">
      <div class="flex-grow-1">
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong>Error:</strong> ${escapeHtml(message)}
        ${errorCodeHtml}
      </div>
      ${retryButtonHtml}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  `;

  $container.html(errorHtml);

  if (onRetry) {
    $container.find('.error-retry-btn').on('click', function () {
      // Show loading state on button
      const $btn = window.jQuery(this);
      const originalHtml = $btn.html();
      $btn.html('<i class="fas fa-spinner fa-spin"></i> Retrying...').prop('disabled', true);

      // Call retry function, reset button state on failure
      Promise.resolve(onRetry()).catch(() => {
        $btn.html(originalHtml).prop('disabled', false);
      });
    });
  }

  return $container.find('.alert');
}

/**
 * Parse AJAX error response and return user-friendly message
 * @param {jqXHR} xhr - jQuery XHR object
 * @param {string} defaultMessage - Default message if parsing fails
 * @returns {Object} Object with message and optional errorCode
 */
export function parseErrorResponse(xhr, defaultMessage = 'An error occurred') {
  let message = defaultMessage;
  let errorCode = null;

  // Handle undefined or null xhr
  if (!xhr) {
    return { message, errorCode };
  }

  // Try to parse JSON response
  try {
    const response = JSON.parse(xhr.responseText);
    if (response.error) {
      message = response.error;
    } else if (response.message) {
      message = response.message;
    }
    if (response.error_code) {
      errorCode = response.error_code;
    }
  } catch {
    // Not a JSON response, use HTTP status-based messages
    switch (xhr.status) {
      case 0:
        message = 'Network error. Please check your connection.';
        errorCode = 'NETWORK_ERROR';
        break;
      case 400:
        message = 'Invalid request. Please check your input.';
        errorCode = 'BAD_REQUEST';
        break;
      case 403:
        message = 'Permission denied. You may not have access to this resource.';
        errorCode = 'FORBIDDEN';
        break;
      case 404:
        message = 'The requested resource was not found.';
        errorCode = 'NOT_FOUND';
        break;
      case 500:
        message = 'Server error. Please try again later.';
        errorCode = 'SERVER_ERROR';
        break;
      case 502:
      case 503:
      case 504:
        message = 'Service temporarily unavailable. Please try again.';
        errorCode = 'SERVICE_UNAVAILABLE';
        break;
      default:
        // Keep default message
        break;
    }
  }

  return { message, errorCode };
}

/**
 * Show a loading state in a container
 * @param {jQuery} $container - jQuery container element
 * @param {string} message - Loading message (default: 'Loading...')
 */
export function showLoading($container, message = 'Loading...') {
  $container.html(`
    <div class="text-center py-3">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">${escapeHtml(message)}</span>
      </div>
      <p class="mt-2 text-muted">${escapeHtml(message)}</p>
    </div>
  `);
}

/**
 * Create a toast notification for transient errors
 * Uses toastr if available, falls back to console
 * @param {string} message - Error message
 * @param {string} type - 'error', 'warning', 'success', 'info'
 */
export function showToast(message, type = 'error') {
  if (window.toastr && typeof window.toastr[type] === 'function') {
    window.toastr[type](message);
  } else {
    console[type === 'error' ? 'error' : type === 'warning' ? 'warn' : 'log'](
      `[Toast ${type}]`,
      message
    );
  }
}
