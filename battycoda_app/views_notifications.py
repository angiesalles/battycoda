"""Views for handling notifications."""

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models.notification import UserNotification

@login_required
def notification_list_view(request):
    """Display a list of user notifications."""
    notifications = UserNotification.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    
    return render(request, 'notifications/list.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    notification = get_object_or_404(UserNotification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    # If this is an AJAX request, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    # Otherwise redirect to notification list or the notification link
    if notification.link:
        return redirect(notification.link)
    else:
        return redirect('battycoda_app:notifications')

@login_required
def mark_all_read(request):
    """Mark all notifications as read."""
    UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    # If this is an AJAX request, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    # Otherwise redirect to notification list
    return redirect('battycoda_app:notifications')

@login_required
def get_navbar_notifications(request):
    """Return notifications for the navbar as JSON."""
    # Get 5 most recent notifications
    notifications = UserNotification.objects.filter(user=request.user).order_by('-created_at')[:5]
    unread_count = UserNotification.objects.filter(user=request.user, is_read=False).count()
    
    # Format notifications for JSON response
    notification_data = []
    for notif in notifications:
        notification_data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'icon': notif.icon,
            'created_at': notif.created_at.isoformat(),
            'is_read': notif.is_read,
            'link': notif.link,
        })
    
    return JsonResponse({
        'success': True,
        'notifications': notification_data,
        'unread_count': unread_count,
    })