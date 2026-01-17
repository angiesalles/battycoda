"""
User-facing email functions for BattyCoda.

This module contains email functions for user authentication and account management:
- Group invitations
- Login codes (OTP)
- Welcome emails
- Password reset
"""

from django.conf import settings
from django.template.loader import render_to_string

from .email_utils import send_mail


def _get_domain():
    """Get the domain name from settings, with localhost fallback."""
    return settings.DOMAIN_NAME if hasattr(settings, "DOMAIN_NAME") else "localhost"


def send_invitation_email(group_name, inviter_name, recipient_email, invitation_link, expires_at):
    """
    Send a group invitation email.

    Args:
        group_name (str): Name of the group
        inviter_name (str): Name of the person who sent the invitation
        recipient_email (str): Email address of the recipient
        invitation_link (str): Link to accept the invitation
        expires_at (datetime): Expiration date of the invitation

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = f"Invitation to join {group_name} on BattyCoda"

    # Create plain text message
    message = (
        f"You have been invited to join {group_name} on BattyCoda by {inviter_name}. "
        f"Visit {invitation_link} to accept. "
        f"This invitation will expire on {expires_at.strftime('%Y-%m-%d %H:%M')}."
    )

    # Create HTML message
    html_message = render_to_string(
        "emails/invitation_email.html",
        {
            "group_name": group_name,
            "inviter_name": inviter_name,
            "invitation_link": invitation_link,
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M"),
        },
    )

    return send_mail(subject=subject, message=message, recipient_list=[recipient_email], html_message=html_message)


def send_login_code_email(user, code, token, expires_at):
    """
    Send a login code email to a user.

    Args:
        user (User): User object
        code (str): One-time login code
        token (str): One-time login token for direct link
        expires_at (datetime): Expiration time for the code

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = "Your BattyCoda Login Code"

    expiry_str = expires_at.strftime("%Y-%m-%d %H:%M")
    domain = _get_domain()
    login_link = f"https://{domain}/accounts/login-with-token/{token}/"

    message = (
        f"Hello {user.username},\n\n"
        f"Your BattyCoda login code is: {code}\n\n"
        f"Or click the following link to log in directly:\n"
        f"{login_link}\n\n"
        f"This code and link will expire on {expiry_str}.\n\n"
        f"If you did not request this code, please ignore this email."
    )

    html_message = f"""
    <html>
    <body>
        <h2>BattyCoda Login Code</h2>
        <p>Hello {user.username},</p>
        <p>Your login code is:</p>
        <h1 style="font-size: 24px; font-weight: bold; background-color: #f0f0f0; padding: 10px; text-align: center;">{code}</h1>
        <p>Or click the following button to log in directly:</p>
        <p style="text-align: center; margin: 20px 0;">
            <a href="{login_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Login Now</a>
        </p>
        <p>This code and link will expire on {expiry_str}.</p>
        <p>If you did not request this code, please ignore this email.</p>
    </body>
    </html>
    """

    return send_mail(subject=subject, message=message, recipient_list=[user.email], html_message=html_message)


def send_welcome_email(user):
    """
    Send a welcome email to a new user.

    Args:
        user (User): User object for the new user

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = "Welcome to BattyCoda!"

    domain = _get_domain()
    login_url = f"https://{domain}/accounts/login/"

    message = (
        f"Hello {user.username},\n\n"
        f"Welcome to BattyCoda! Your account has been successfully created.\n\n"
        f"You can now log in to your account using your username and password at:\n"
        f"{login_url}\n\n"
        f"BattyCoda is a platform for annotating bat call recordings. If you have any questions, "
        f"please contact the administrator.\n\n"
        f"Thank you for joining!\n\n"
        f"The BattyCoda Team"
    )

    html_message = f"""
    <html>
    <body>
        <h2>Welcome to BattyCoda!</h2>
        <p>Hello {user.username},</p>
        <p>Your account has been successfully created.</p>
        <p>You can now log in to your account using your username and password.</p>
        <p style="text-align: center; margin: 20px 0;">
            <a href="{login_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Login Now</a>
        </p>
        <p>BattyCoda is a platform for annotating bat call recordings. If you have any questions, please contact the administrator.</p>
        <p>Thank you for joining!</p>
        <p>The BattyCoda Team</p>
    </body>
    </html>
    """

    return send_mail(subject=subject, message=message, recipient_list=[user.email], html_message=html_message)


def send_password_reset_email(user, token, expires_at):
    """
    Send a password reset email to a user.

    Args:
        user (User): User object
        token (str): Password reset token for the reset link
        expires_at (datetime): Expiration time for the token

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = "Reset Your BattyCoda Password"

    expiry_str = expires_at.strftime("%Y-%m-%d %H:%M")
    domain = _get_domain()
    reset_link = f"https://{domain}/accounts/reset-password/{token}/"

    message = (
        f"Hello {user.username},\n\n"
        f"You have requested to reset your password for your BattyCoda account.\n\n"
        f"Click the following link to reset your password:\n"
        f"{reset_link}\n\n"
        f"This link will expire on {expiry_str}.\n\n"
        f"If you did not request this password reset, please ignore this email."
    )

    html_message = f"""
    <html>
    <body>
        <h2>BattyCoda Password Reset</h2>
        <p>Hello {user.username},</p>
        <p>You have requested to reset your password for your BattyCoda account.</p>
        <p>Click the following button to reset your password:</p>
        <p style="text-align: center; margin: 20px 0;">
            <a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a>
        </p>
        <p>This link will expire on {expiry_str}.</p>
        <p>If you did not request this password reset, please ignore this email.</p>
    </body>
    </html>
    """

    return send_mail(subject=subject, message=message, recipient_list=[user.email], html_message=html_message)
