// Navbar notifications management

function loadNavbarNotifications() {
    $.ajax({
        url: navbarNotificationsUrl,
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            if (data.success) {
                // Update notification count indicator
                if (data.unread_count > 0) {
                    // Show the indicator with count only when there are unread notifications
                    $('#notificationIndicator').addClass('indicator-new').show().text(data.unread_count);
                } else {
                    // Remove the indicator completely when there are no unread notifications
                    $('#notificationIndicator').removeClass('indicator-new').hide().text('');
                }
                
                // Update notification list
                var $notificationsList = $('#notificationsList');
                $notificationsList.empty();
                
                if (data.notifications.length > 0) {
                    // Add notifications to the list
                    $.each(data.notifications, function(i, notification) {
                        var notificationUrl = markNotificationReadUrl.replace('0', notification.id);
                        var notificationHtml = 
                            '<li id="notification-' + notification.id + '"><a href="' + 
                            (notification.link ? notificationUrl : '#') + 
                            '">' +
                            '<div class="icon"><span class="' + notification.icon + '"></span></div>' +
                            '<div class="content">' +
                            '<span class="desc">' + notification.title + '</span>' +
                            '<span class="date">' + formatTimeAgo(new Date(notification.created_at)) + '</span>' +
                            '</div></a></li>';
                        
                        $notificationsList.append(notificationHtml);
                    });
                } else {
                    // No notifications
                    $notificationsList.append(
                        '<li><a href="#">' +
                        '<div class="icon"><span class="s7-bell"></span></div>' +
                        '<div class="content"><span class="desc">No notifications</span></div>' +
                        '</a></li>'
                    );
                }
            }
        },
        error: function() {
            // Error handling - show error in notification list
            var $notificationsList = $('#notificationsList');
            $notificationsList.empty();
            $notificationsList.append(
                '<li><a href="#">' +
                '<div class="icon"><span class="s7-close"></span></div>' +
                '<div class="content"><span class="desc">Failed to load notifications</span></div>' +
                '</a></li>'
            );
        }
    });
}

// Format time as "X minutes ago", "X hours ago", etc.
function formatTimeAgo(date) {
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
    
    // For older notifications, display the date
    return date.toLocaleDateString();
}

$(document).ready(function() {
    // Load notifications initially
    loadNavbarNotifications();
    
    // Refresh notifications every 60 seconds
    setInterval(loadNavbarNotifications, 60000);
    
    // Reload notifications when the dropdown is opened
    $('#notificationsDropdown').on('click', function() {
        loadNavbarNotifications();
    });
});