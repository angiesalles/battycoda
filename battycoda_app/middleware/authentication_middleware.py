"""
Standard authentication middleware for BattyCoda Django application

This middleware ensures users are authenticated and handles redirects to login page.
"""

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils import timezone


class AuthenticationMiddleware:
    """
    Django middleware to verify user authentication
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip authentication for some paths
        skip_paths = [
            "/admin/",
            "/accounts/login/",
            "/login/",
            "/static/",
            "/media/",
            "/accounts/register/",
            "/register/",
            "/invitation/",
            "/accounts/request-login-code/",
            "/accounts/enter-login-code/",
            "/accounts/login-with-token/",
            "/accounts/password-reset/",
            "/accounts/reset-password/",
            "/accounts/check-username/",
            "/accounts/check-email/",
            "/welcome/",  # Allow access to the landing page
            "/hijack/",  # Allow hijack functionality access
            "/simple-api/",  # Allow simple API access (uses API key auth)
        ]

        # Skip for Let's Encrypt ACME challenges
        if request.path.startswith("/.well-known/acme-challenge/"):
            return self.get_response(request)

        # Also skip for authentication-related URLs
        if any(request.path.startswith(path) for path in skip_paths):
            return self.get_response(request)

        # Check if the user is authenticated
        if not request.user.is_authenticated:
            # If this is the root URL, redirect to landing page instead of login
            if request.path == "/" or request.path == "":
                try:
                    landing_url = reverse("battycoda_app:landing")
                    return HttpResponseRedirect(landing_url)
                except NoReverseMatch:
                    pass

            # Otherwise redirect to login page
            try:
                login_url = reverse("battycoda_app:login")
            except NoReverseMatch:
                # Fallback to absolute URL if reverse fails
                login_url = "/accounts/login/"

            return HttpResponseRedirect(login_url)

        # Update last activity for authenticated users (throttled to avoid too many DB writes)
        if hasattr(request.user, "profile"):
            profile = request.user.profile
            now = timezone.now()

            # Only update if more than 5 minutes have passed since last update
            if not profile.last_activity or (now - profile.last_activity).total_seconds() > 300:
                profile.last_activity = now
                profile.save(update_fields=["last_activity"])

        # Process the request and return the response
        return self.get_response(request)
