from battycoda_app.models.user import UserProfile

def theme_choices(request):
    """
    Adds theme choices to template context for use in templates.
    """
    return {
        'THEME_CHOICES': UserProfile.THEME_CHOICES,
    }