from django.conf import settings

from battycoda_app.models.user import UserProfile


def theme_choices(request):
    """
    Adds theme choices to template context for use in templates.
    """
    return {
        "THEME_CHOICES": UserProfile.THEME_CHOICES,
    }


def hijack_notification(request):
    """Add hijack notification data to the template context."""
    return {
        "is_hijacked": getattr(request, "hijack", {}).get("is_hijacked", False),
        "hijacked_user": request.user if getattr(request, "hijack", {}).get("is_hijacked", False) else None,
    }


def sentry_settings(request):
    """Add Sentry configuration to template context for frontend error tracking."""
    return {
        "SENTRY_DSN": getattr(settings, "SENTRY_DSN", None),
        "SENTRY_ENVIRONMENT": getattr(settings, "SENTRY_ENVIRONMENT", "production"),
    }


def vite_features(request):
    """
    Add Vite feature flags to template context for incremental JS migration.

    This enables page-by-page migration from traditional Django static files
    to Vite-bundled JavaScript modules with rollback capability.
    """
    return {
        "VITE_ENABLED": getattr(settings, "VITE_ENABLED", False),
        "VITE_FEATURES": getattr(settings, "VITE_FEATURES", {}),
    }
