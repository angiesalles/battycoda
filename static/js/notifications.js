/**
 * Notifications Module
 *
 * Handles navbar notification loading, display, and polling.
 * Requires jQuery and template-provided URLs:
 * - navbarNotificationsUrl: URL to fetch notifications
 * - markNotificationReadUrl: URL pattern to mark notification as read
 */

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
 * Load notifications from server and update the navbar dropdown
 */
export function loadNavbarNotifications() {
  // Check if required globals are available
  if (typeof navbarNotificationsUrl === 'undefined') {
    return;
  }

  $.ajax({
    url: navbarNotificationsUrl,
    type: 'GET',
    dataType: 'json',
    success: function (data) {
      if (data.success) {
        // Update notification count indicator
        if (data.unread_count > 0) {
          $('#notificationIndicator').addClass('indicator-new').show().text(data.unread_count);
        } else {
          $('#notificationIndicator').removeClass('indicator-new').hide().text('');
        }

        // Update notification list
        const $notificationsList = $('#notificationsList');
        $notificationsList.empty();

        if (data.notifications.length > 0) {
          $.each(data.notifications, function (i, notification) {
            const notificationUrl = markNotificationReadUrl.replace('0', notification.id);
            const notificationHtml =
              '<li id="notification-' +
              notification.id +
              '"><a href="' +
              (notification.link ? notificationUrl : '#') +
              '">' +
              '<div class="icon"><span class="' +
              notification.icon +
              '"></span></div>' +
              '<div class="content">' +
              '<span class="desc">' +
              notification.title +
              '</span>' +
              '<span class="date">' +
              formatTimeAgo(new Date(notification.created_at)) +
              '</span>' +
              '</div></a></li>';

            $notificationsList.append(notificationHtml);
          });
        } else {
          $notificationsList.append(
            '<li><a href="#">' +
              '<div class="icon"><span class="s7-bell"></span></div>' +
              '<div class="content"><span class="desc">No notifications</span></div>' +
              '</a></li>'
          );
        }
      }
    },
    error: function () {
      const $notificationsList = $('#notificationsList');
      $notificationsList.empty();
      $notificationsList.append(
        '<li><a href="#">' +
          '<div class="icon"><span class="s7-close"></span></div>' +
          '<div class="content"><span class="desc">Failed to load notifications</span></div>' +
          '</a></li>'
      );
    },
  });
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
  $('#notificationsDropdown').on('click', function () {
    loadNavbarNotifications();
  });
}

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function () {
    // Wait for jQuery to be available
    if (typeof $ !== 'undefined') {
      initialize();
    }
  });
} else {
  if (typeof $ !== 'undefined') {
    $(document).ready(initialize);
  }
}

// Expose globally for external use
window.loadNavbarNotifications = loadNavbarNotifications;
