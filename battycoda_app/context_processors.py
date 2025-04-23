from battycoda_app.models.user import UserProfile

def theme_choices(request):
    """
    Adds theme choices to template context for use in templates.
    """
    return {
        'THEME_CHOICES': UserProfile.THEME_CHOICES,
    }

def hijack_notification(request):
    """Add hijack notification data to the template context."""
    return {
        "is_hijacked": getattr(request, 'hijack', {}).get('is_hijacked', False),
        "hijacked_user": request.user if getattr(request, 'hijack', {}).get('is_hijacked', False) else None,
    }