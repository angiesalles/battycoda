"""
Notification URL patterns.

Handles notification viewing and management.
"""

from django.urls import path

from .views_notifications import get_navbar_notifications, mark_all_read, mark_notification_read, notification_list_view

urlpatterns = [
    path("notifications/", notification_list_view, name="notifications"),
    path("notifications/<int:notification_id>/read/", mark_notification_read, name="mark_notification_read"),
    path("notifications/mark-all-read/", mark_all_read, name="mark_all_read"),
    path("notifications/navbar/", get_navbar_notifications, name="get_navbar_notifications"),
]
