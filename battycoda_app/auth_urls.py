"""
Authentication URL patterns.

Handles user authentication, registration, profile management,
password resets, and API key generation.
"""
from django.urls import path
from . import views_auth

urlpatterns = [
    path("accounts/login/", views_auth.login_view, name="login"),
    path("accounts/register/", views_auth.register_view, name="register"),
    path("accounts/logout/", views_auth.logout_view, name="logout"),
    path("accounts/profile/", views_auth.edit_profile_view, name="profile"),
    path("accounts/profile/edit/", views_auth.edit_profile_view, name="edit_profile"),
    path("accounts/password-reset/", views_auth.password_reset_request, name="password_reset_request"),
    path("accounts/reset-password/<str:token>/", views_auth.password_reset, name="password_reset"),
    path("accounts/request-login-code/", views_auth.request_login_code, name="request_login_code"),
    path("accounts/enter-login-code/<str:username>/", views_auth.enter_login_code, name="enter_login_code"),
    path("accounts/login-with-token/<str:token>/", views_auth.login_with_token, name="login_with_token"),
    path("accounts/check-username/", views_auth.check_username, name="check_username"),
    path("accounts/check-email/", views_auth.check_email, name="check_email"),
    path("accounts/generate-api-key/", views_auth.generate_api_key_view, name="generate_api_key"),
    path("update_theme_preference/", views_auth.update_theme_preference, name="update_theme_preference"),
    path("update_profile_ajax/", views_auth.update_profile_ajax, name="update_profile_ajax"),
]
