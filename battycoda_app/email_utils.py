from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.template.loader import render_to_string


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

    # Send the email
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
    from django.conf import settings

    subject = "Your BattyCoda Login Code"

    # Format expiry time
    expiry_str = expires_at.strftime("%Y-%m-%d %H:%M")

    # Create login link URL using the domain name from settings
    domain = settings.DOMAIN_NAME if hasattr(settings, "DOMAIN_NAME") else "localhost"
    login_link = f"https://{domain}/accounts/login-with-token/{token}/"

    # Create plain text message
    message = (
        f"Hello {user.username},\n\n"
        f"Your BattyCoda login code is: {code}\n\n"
        f"Or click the following link to log in directly:\n"
        f"{login_link}\n\n"
        f"This code and link will expire on {expiry_str}.\n\n"
        f"If you did not request this code, please ignore this email."
    )

    # Create HTML message
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

    # Send the email
    return send_mail(subject=subject, message=message, recipient_list=[user.email], html_message=html_message)


def send_welcome_email(user):
    """
    Send a welcome email to a new user.

    Args:
        user (User): User object for the new user

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    from django.conf import settings

    subject = "Welcome to BattyCoda!"

    # Create login URL using the domain name from settings
    domain = settings.DOMAIN_NAME if hasattr(settings, "DOMAIN_NAME") else "localhost"
    login_url = f"https://{domain}/accounts/login/"

    # Create plain text message
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

    # Create HTML message
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

    # Send the email
    return send_mail(subject=subject, message=message, recipient_list=[user.email], html_message=html_message)


def send_worker_failure_email(service_name, failure_reason=None, hostname=None):
    """
    Send an email notification when a Celery worker fails (e.g., OOM kill).

    Args:
        service_name (str): Name of the failed service (e.g., 'battycoda-celery')
        failure_reason (str, optional): Reason for failure (e.g., 'oom-kill')
        hostname (str, optional): Hostname of the server

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    import datetime

    from django.conf import settings

    subject = f"[BattyCoda ALERT] Worker {service_name} failed"

    if hostname is None:
        import socket

        hostname = socket.gethostname()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    reason_text = failure_reason if failure_reason else "Unknown"

    message = (
        f"BattyCoda Worker Failure Alert\n"
        f"==============================\n\n"
        f"Service: {service_name}\n"
        f"Server: {hostname}\n"
        f"Time: {timestamp}\n"
        f"Failure Reason: {reason_text}\n\n"
        f"The service has been configured to auto-restart.\n"
        f"Please check server logs for more details:\n"
        f"  sudo journalctl -u {service_name} -n 100\n"
    )

    html_message = f"""
    <html>
    <body>
        <h2 style="color: #dc3545;">BattyCoda Worker Failure Alert</h2>
        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Service</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{service_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Server</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{hostname}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Time</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{timestamp}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Failure Reason</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: #dc3545;">{reason_text}</td>
            </tr>
        </table>
        <p>The service has been configured to auto-restart.</p>
        <p>Please check server logs for more details:</p>
        <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">sudo journalctl -u {service_name} -n 100</pre>
    </body>
    </html>
    """

    admin_emails = [email for name, email in getattr(settings, "ADMINS", [])]

    if not admin_emails:
        return False

    return send_mail(subject=subject, message=message, recipient_list=admin_emails, html_message=html_message)


def send_disk_usage_warning_email(disk_info, threshold=90, hostname=None):
    """
    Send an email notification when disk usage exceeds threshold.

    Args:
        disk_info (list): List of dicts with 'mount', 'total', 'used', 'free', 'percent' keys
        threshold (int): Percentage threshold that triggered the warning
        hostname (str, optional): Hostname of the server

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    import datetime

    from django.conf import settings

    subject = f"[BattyCoda ALERT] Disk usage exceeds {threshold}%"

    if hostname is None:
        import socket

        hostname = socket.gethostname()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build plain text message
    disk_lines = []
    for disk in disk_info:
        disk_lines.append(
            f"  {disk['mount']}: {disk['percent']}% used ({disk['used']} / {disk['total']}, {disk['free']} free)"
        )
    disk_text = "\n".join(disk_lines)

    message = (
        f"BattyCoda Disk Usage Warning\n"
        f"=============================\n\n"
        f"Server: {hostname}\n"
        f"Time: {timestamp}\n"
        f"Threshold: {threshold}%\n\n"
        f"Disks exceeding threshold:\n"
        f"{disk_text}\n\n"
        f"Please free up disk space to avoid service disruption.\n"
    )

    # Build HTML message
    disk_rows = ""
    for disk in disk_info:
        color = "#dc3545" if disk["percent"] >= 95 else "#ffc107"
        disk_rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{disk["mount"]}</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: {color}; font-weight: bold;">{disk["percent"]}%</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{disk["used"]} / {disk["total"]}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{disk["free"]}</td>
            </tr>
        """

    html_message = f"""
    <html>
    <body>
        <h2 style="color: #ffc107;">BattyCoda Disk Usage Warning</h2>
        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Server</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{hostname}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Time</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{timestamp}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Threshold</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{threshold}%</td>
            </tr>
        </table>
        <h3>Disks Exceeding Threshold</h3>
        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr style="background: #f5f5f5;">
                <th style="padding: 8px; border: 1px solid #ddd;">Mount Point</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Usage</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Used / Total</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Free</th>
            </tr>
            {disk_rows}
        </table>
        <p style="color: #dc3545; font-weight: bold;">Please free up disk space to avoid service disruption.</p>
    </body>
    </html>
    """

    admin_emails = [email for name, email in getattr(settings, "ADMINS", [])]

    if not admin_emails:
        return False

    return send_mail(subject=subject, message=message, recipient_list=admin_emails, html_message=html_message)


def send_backup_failure_email(error_message, bucket_name=None, hostname=None):
    """
    Send an email notification when database backup to S3 fails.

    Args:
        error_message (str): The error message describing the failure
        bucket_name (str, optional): S3 bucket name that was targeted
        hostname (str, optional): Hostname of the server

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    import datetime

    from django.conf import settings

    subject = "[BattyCoda ALERT] Database backup failed"

    if hostname is None:
        import socket

        hostname = socket.gethostname()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bucket_text = bucket_name if bucket_name else "unknown"

    message = (
        f"BattyCoda Database Backup Failure\n"
        f"==================================\n\n"
        f"Server: {hostname}\n"
        f"Time: {timestamp}\n"
        f"Target Bucket: {bucket_text}\n\n"
        f"Error:\n{error_message}\n\n"
        f"The backup task has exhausted all retries.\n"
        f"Please investigate and run a manual backup if needed:\n"
        f"  python manage.py backup_database\n"
    )

    html_message = f"""
    <html>
    <body>
        <h2 style="color: #dc3545;">BattyCoda Database Backup Failure</h2>
        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Server</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{hostname}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Time</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{timestamp}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Target Bucket</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{bucket_text}</td>
            </tr>
        </table>
        <h3>Error Details</h3>
        <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; color: #dc3545;">{error_message}</pre>
        <p>The backup task has exhausted all retries.</p>
        <p>Please investigate and run a manual backup if needed:</p>
        <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">python manage.py backup_database</pre>
    </body>
    </html>
    """

    admin_emails = [email for name, email in getattr(settings, "ADMINS", [])]

    if not admin_emails:
        return False

    return send_mail(subject=subject, message=message, recipient_list=admin_emails, html_message=html_message)


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
    from django.conf import settings

    subject = "Reset Your BattyCoda Password"

    # Format expiry time
    expiry_str = expires_at.strftime("%Y-%m-%d %H:%M")

    # Create reset link URL using the domain name from settings
    domain = settings.DOMAIN_NAME if hasattr(settings, "DOMAIN_NAME") else "localhost"
    reset_link = f"https://{domain}/accounts/reset-password/{token}/"

    # Create plain text message
    message = (
        f"Hello {user.username},\n\n"
        f"You have requested to reset your password for your BattyCoda account.\n\n"
        f"Click the following link to reset your password:\n"
        f"{reset_link}\n\n"
        f"This link will expire on {expiry_str}.\n\n"
        f"If you did not request this password reset, please ignore this email."
    )

    # Create HTML message
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

    # Send the email
    return send_mail(subject=subject, message=message, recipient_list=[user.email], html_message=html_message)
