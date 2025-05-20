"""Views for handling notifications."""

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models.notification import UserNotification

@login_required
def notification_list_view(request):
    """Display a list of user notifications with pagination."""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    # Get all notifications for this user
    notifications_list = UserNotification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications_list.filter(is_read=False).count()
    
    # Set up pagination - 20 notifications per page
    paginator = Paginator(notifications_list, 20)
    page = request.GET.get('page')
    
    try:
        # Get the requested page
        notifications = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        notifications = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        notifications = paginator.page(paginator.num_pages)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'total_count': notifications_list.count(),
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
    
    # Return to the same page if page parameter is provided
    page = request.GET.get('page')
    if page:
        return redirect(f"{reverse('battycoda_app:notifications')}?page={page}")
    
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