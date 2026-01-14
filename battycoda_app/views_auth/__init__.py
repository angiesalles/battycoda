"""Authentication views package."""

from .ajax import check_email, check_username
from .login import login_view, login_with_token, logout_view, process_invitation
from .password import enter_login_code, password_reset, password_reset_request, request_login_code
from .profile import (
    edit_profile_view,
    generate_api_key_view,
    hijack_user_view,
    profile_view,
    release_hijacked_user_view,
    update_profile_ajax,
    update_theme_preference,
)
from .registration import register_view

__all__ = [
    "check_email",
    "check_username",
    "edit_profile_view",
    "enter_login_code",
    "generate_api_key_view",
    "hijack_user_view",
    "login_view",
    "login_with_token",
    "logout_view",
    "password_reset",
    "password_reset_request",
    "process_invitation",
    "profile_view",
    "register_view",
    "release_hijacked_user_view",
    "request_login_code",
    "update_profile_ajax",
    "update_theme_preference",
]
