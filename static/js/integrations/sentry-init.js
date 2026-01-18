/**
 * Sentry Error Tracking Initialization
 *
 * This module initializes Sentry error tracking by reading configuration
 * from data attributes on the #sentry-config element in the page.
 *
 * Expected data attributes:
 * - data-environment: The Sentry environment (e.g., 'production', 'staging')
 * - data-user-id: Optional user ID for user context
 * - data-user-email: Optional user email for user context
 * - data-user-username: Optional username for user context
 *
 * @module integrations/sentry-init
 */

/**
 * Initialize Sentry with configuration from DOM.
 *
 * Waits for Sentry to be loaded (via the CDN script), then configures it
 * with the environment and user context from data attributes.
 */
function initializeSentry() {
  // Get configuration from data attributes
  const configEl = document.getElementById('sentry-config');
  if (!configEl) {
    console.warn('Sentry config element not found');
    return;
  }

  const environment = configEl.dataset.environment || 'production';
  const userId = configEl.dataset.userId;
  const userEmail = configEl.dataset.userEmail;
  const userUsername = configEl.dataset.userUsername;

  // Wait for Sentry to be available
  if (typeof Sentry === 'undefined' || typeof Sentry.onLoad !== 'function') {
    console.warn('Sentry not loaded, skipping initialization');
    return;
  }

  Sentry.onLoad(function () {
    Sentry.init({
      environment: environment,
      tracesSampleRate: 0.1,
    });

    // Set user context if available
    if (userId) {
      Sentry.setUser({
        id: userId,
        email: userEmail || undefined,
        username: userUsername || undefined,
      });
    }
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeSentry);
} else {
  initializeSentry();
}
