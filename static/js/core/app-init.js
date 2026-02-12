/**
 * Application Initialization
 *
 * This module handles core application initialization including:
 * - Display of Django flash messages via Bootstrap toasts
 * - Management features activation handler
 *
 * Configuration is read from data attributes on #app-config element.
 *
 * @module core/app-init
 */

import { toast } from '../utils/toast.js';
import { getCsrfToken } from '../utils/page-data.js';

/**
 * Display Django flash messages using Bootstrap toasts.
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
      const fn = toast[level] || toast.info;
      fn(text);
    });
  } catch (e) {
    console.warn('Failed to parse Django messages:', e);
  }
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
  const isAuthenticated = configEl.dataset.userAuthenticated === 'true';

  window.activateManagementFeatures = function () {
    if (!isAuthenticated) {
      toast.error('You must be logged in to activate management features.');
      return;
    }

    if (!updateProfileUrl) {
      toast.error('Configuration error: update profile URL not available.');
      return;
    }

    fetch(updateProfileUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCsrfToken(),
      },
      body: new URLSearchParams({
        action: 'update_management_features',
        enabled: 'true',
      }),
    })
      .then((r) => r.json())
      .then((response) => {
        if (response.success) {
          toast.success(response.message);
          setTimeout(() => window.location.reload(), 1000);
        } else {
          toast.error(response.message);
        }
      })
      .catch(() => {
        toast.error('Failed to activate management features. Please try again.');
      });
  };
}

/**
 * Main initialization function.
 */
function initializeApp() {
  displayDjangoMessages();
  setupManagementFeatures();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
