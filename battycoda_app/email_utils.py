"""
Core email utilities for BattyCoda.

This module provides the base email sending function used by all other email modules.
"""

from django.conf import settings
from django.core.mail import send_mail as django_send_mail


def send_mail(subject, message, recipient_list, html_message=None, from_email=None):
    """
    Send an email using AWS SES with better error handling and logging.

    In test mode (DJANGO_TEST_MODE=true), Django uses locmem.EmailBackend which
    stores emails in django.core.mail.outbox instead of sending them. This allows
    tests to verify email content without actually sending emails.

    Args:
        subject (str): Email subject
        message (str): Plain text message
        recipient_list (list): List of recipient email addresses
        html_message (str, optional): HTML message. Defaults to None.
        from_email (str, optional): Sender email address. Defaults to settings.DEFAULT_FROM_EMAIL.

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Skip sending emails in test mode (defense-in-depth alongside locmem backend)
    if getattr(settings, "DJANGO_TEST_MODE", False):
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"Test mode: skipping email to {recipient_list} with subject '{subject}'")
        return True

    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    try:
        # Send email using Django's send_mail which will use AWS SES backend
        django_send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

        return True
    except Exception:
        return False
