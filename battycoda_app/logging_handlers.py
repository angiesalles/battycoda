"""
Custom logging handlers for BattyCoda.

Provides enhanced error email handling with user context.
"""

from django.utils.log import AdminEmailHandler
from django.views.debug import ExceptionReporter


class UserContextAdminEmailHandler(AdminEmailHandler):
    """
    Custom AdminEmailHandler that includes the affected user in the email subject.

    Subject format: [Django] ERROR (user: username): Error message
    """

    def emit(self, record):
        # Extract user from request if available
        request = getattr(record, "request", None)
        if request is not None:
            user = getattr(request, "user", None)
            if user is not None and hasattr(user, "is_authenticated"):
                if user.is_authenticated:
                    record.user_info = user.username
                else:
                    record.user_info = "anonymous"
            else:
                record.user_info = "unknown"
        else:
            record.user_info = "no-request"

        super().emit(record)

    def format_subject(self, subject):
        """
        Format the subject line to include user information.

        Transforms: [Django] ERROR (EXTERNAL IP): /path/
        Into:       [Django] ERROR (user: username): /path/
        """
        # Get user_info that was set in emit()
        user_info = getattr(self, "_current_user_info", "unknown")

        # Replace the IP info with user info
        if "(EXTERNAL IP)" in subject:
            subject = subject.replace("(EXTERNAL IP)", f"(user: {user_info})")
        elif "(internal IP)" in subject:
            subject = subject.replace("(internal IP)", f"(user: {user_info})")
        else:
            # If no IP marker, insert user info after ERROR
            if "ERROR:" in subject:
                subject = subject.replace("ERROR:", f"ERROR (user: {user_info}):")
            elif "ERROR" in subject:
                subject = subject.replace("ERROR", f"ERROR (user: {user_info})")

        return super().format_subject(subject)

    def send_mail(self, subject, message, *args, **kwargs):
        # Store user_info for format_subject to use
        # We need to extract it from the message since it's not directly available here
        self._current_user_info = getattr(self, "_pending_user_info", "unknown")
        super().send_mail(subject, message, *args, **kwargs)

    def emit(self, record):
        # Extract user from request if available and store for later
        request = getattr(record, "request", None)
        if request is not None:
            user = getattr(request, "user", None)
            if user is not None and hasattr(user, "is_authenticated"):
                if user.is_authenticated:
                    self._pending_user_info = user.username
                else:
                    self._pending_user_info = "anonymous"
            else:
                self._pending_user_info = "unknown"
        else:
            self._pending_user_info = "no-request"

        super().emit(record)
