/**
 * Notifications Module
 *
 * Handles navbar notification loading, display, and polling.
 * Requires page data from templates:
 * - data-navbar-notifications-url: URL to fetch notifications
 * - data-mark-notification-read-url: URL pattern to mark notification as read
 */

import { getPageData, fetchWithCsrf } from './utils/page-data.js';

/**
 * Format time as "X minutes ago", "X hours ago", etc.
 * @param {Date} date - Date to format
 * @returns {string} Formatted time string
 */
export function formatTimeAgo(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.round(diffMs / 1000);
  const diffMin = Math.round(diffSec / 60);
  const diffHour = Math.round(diffMin / 60);
  const diffDay = Math.round(diffHour / 24);

  if (diffSec < 60) return 'Just now';
  if (diffMin < 60) return diffMin + ' min ago';
  if (diffHour < 24) return diffHour + ' hour' + (diffHour > 1 ? 's' : '') + ' ago';
  if (diffDay < 7) return diffDay + ' day' + (diffDay > 1 ? 's' : '') + ' ago';

  return date.toLocaleDateString();
}

/**
 * Create notification HTML element
 * @param {Object} notification - Notification data
 * @param {string} markNotificationReadUrl - URL pattern for marking as read
 * @returns {HTMLElement} The notification list item element
 */
function createNotificationElement(notification, markNotificationReadUrl) {
  const li = document.createElement('li');
  li.id = `notification-${notification.id}`;

  const notificationUrl = markNotificationReadUrl.replace('0', notification.id);
  const link = document.createElement('a');
  link.href = notification.link ? notificationUrl : '#';

  const iconDiv = document.createElement('div');
  iconDiv.className = 'icon';
  const iconSpan = document.createElement('span');
  iconSpan.className = notification.icon;
  iconDiv.appendChild(iconSpan);

  const contentDiv = document.createElement('div');
  contentDiv.className = 'content';
  const descSpan = document.createElement('span');
  descSpan.className = 'desc';
  descSpan.textContent = notification.title;
  const dateSpan = document.createElement('span');
  dateSpan.className = 'date';
  dateSpan.textContent = formatTimeAgo(new Date(notification.created_at));
  contentDiv.appendChild(descSpan);
  contentDiv.appendChild(dateSpan);

  link.appendChild(iconDiv);
  link.appendChild(contentDiv);
  li.appendChild(link);

  return li;
}

/**
 * Create empty state notification element
 * @param {string} icon - Icon class name
 * @param {string} message - Message to display
 * @returns {HTMLElement} The notification list item element
 */
function createEmptyStateElement(icon, message) {
  const li = document.createElement('li');
  const link = document.createElement('a');
  link.href = '#';

  const iconDiv = document.createElement('div');
  iconDiv.className = 'icon';
  const iconSpan = document.createElement('span');
  iconSpan.className = icon;
  iconDiv.appendChild(iconSpan);

  const contentDiv = document.createElement('div');
  contentDiv.className = 'content';
  const descSpan = document.createElement('span');
  descSpan.className = 'desc';
  descSpan.textContent = message;
  contentDiv.appendChild(descSpan);

  link.appendChild(iconDiv);
  link.appendChild(contentDiv);
  li.appendChild(link);

  return li;
}

/**
 * Update the notification indicator with unread count
 * @param {number} unreadCount - Number of unread notifications
 */
function updateNotificationIndicator(unreadCount) {
  const indicator = document.getElementById('notificationIndicator');
  if (!indicator) return;

  if (unreadCount > 0) {
    indicator.classList.add('indicator-new');
    indicator.style.display = '';
    indicator.textContent = unreadCount;
  } else {
    indicator.classList.remove('indicator-new');
    indicator.style.display = 'none';
    indicator.textContent = '';
  }
}

/**
 * Load notifications from server and update the navbar dropdown
 * @returns {Promise<void>}
 */
export async function loadNavbarNotifications() {
  // Get URLs from page data
  const pageData = getPageData();
  const navbarNotificationsUrl = pageData.navbarNotificationsUrl;
  const markNotificationReadUrl = pageData.markNotificationReadUrl;

  // Check if required data is available
  if (!navbarNotificationsUrl) {
    return;
  }

  const notificationsList = document.getElementById('notificationsList');

  try {
    const response = await fetchWithCsrf(navbarNotificationsUrl);
    const data = await response.json();

    if (data.success) {
      // Update notification count indicator
      updateNotificationIndicator(data.unread_count);

      // Update notification list
      if (notificationsList) {
        notificationsList.innerHTML = '';

        if (data.notifications.length > 0) {
          data.notifications.forEach((notification) => {
            const element = createNotificationElement(notification, markNotificationReadUrl);
            notificationsList.appendChild(element);
          });
        } else {
          notificationsList.appendChild(createEmptyStateElement('s7-bell', 'No notifications'));
        }
      }
    }
  } catch {
    // Handle fetch errors
    if (notificationsList) {
      notificationsList.innerHTML = '';
      notificationsList.appendChild(createEmptyStateElement('s7-close', 'Failed to load notifications'));
    }
  }
}

/**
 * Initialize notifications polling and event handlers
 */
export function initialize() {
  // Load notifications initially
  loadNavbarNotifications();

  // Refresh notifications every 60 seconds
  setInterval(loadNavbarNotifications, 60000);

  // Reload notifications when the dropdown is opened
  const dropdown = document.getElementById('notificationsDropdown');
  if (dropdown) {
    dropdown.addEventListener('click', function () {
      loadNavbarNotifications();
    });
  }
}

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

// Expose globally for external use
window.loadNavbarNotifications = loadNavbarNotifications;
