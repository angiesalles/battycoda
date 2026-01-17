"""
Admin alert email functions for BattyCoda.

This module contains email functions for system monitoring and alerts:
- Worker failure notifications
- Disk usage warnings
- Backup failure notifications

All alerts are sent to addresses configured in settings.ADMINS.
"""

import datetime
import socket

from django.conf import settings
from django.template.loader import render_to_string

from .email_utils import send_mail


def _get_hostname(hostname=None):
    """Get hostname, using provided value or system hostname."""
    return hostname if hostname is not None else socket.gethostname()


def _get_timestamp():
    """Get current timestamp formatted for display."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _get_admin_emails():
    """Get list of admin email addresses from settings."""
    return [email for name, email in getattr(settings, "ADMINS", [])]


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
    admin_emails = _get_admin_emails()
    if not admin_emails:
        return False

    hostname = _get_hostname(hostname)
    timestamp = _get_timestamp()
    reason_text = failure_reason if failure_reason else "Unknown"

    subject = f"[BattyCoda ALERT] Worker {service_name} failed"

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

    html_message = render_to_string(
        "emails/worker_failure.html",
        {
            "service_name": service_name,
            "hostname": hostname,
            "timestamp": timestamp,
            "failure_reason": reason_text,
        },
    )

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
    admin_emails = _get_admin_emails()
    if not admin_emails:
        return False

    hostname = _get_hostname(hostname)
    timestamp = _get_timestamp()

    subject = f"[BattyCoda ALERT] Disk usage exceeds {threshold}%"

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

    html_message = render_to_string(
        "emails/disk_usage_warning.html",
        {
            "hostname": hostname,
            "timestamp": timestamp,
            "threshold": threshold,
            "disks": disk_info,
        },
    )

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
    admin_emails = _get_admin_emails()
    if not admin_emails:
        return False

    hostname = _get_hostname(hostname)
    timestamp = _get_timestamp()
    bucket_text = bucket_name if bucket_name else "unknown"

    subject = "[BattyCoda ALERT] Database backup failed"

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

    html_message = render_to_string(
        "emails/backup_failure.html",
        {
            "hostname": hostname,
            "timestamp": timestamp,
            "bucket_name": bucket_text,
            "error_message": error_message,
        },
    )

    return send_mail(subject=subject, message=message, recipient_list=admin_emails, html_message=html_message)
