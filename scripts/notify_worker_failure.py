#!/usr/bin/env python
"""
Script to send email notification when a systemd service fails.
Called by systemd via OnFailure directive.

Usage:
    ./notify_worker_failure.py <service_name> [failure_reason]

Example:
    ./notify_worker_failure.py battycoda-celery.service oom-kill
"""

import os
import sys

# Add the project directory to the path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from battycoda_app.email_utils import send_worker_failure_email


def main():
    if len(sys.argv) < 2:
        print("Usage: notify_worker_failure.py <service_name> [failure_reason]")
        sys.exit(1)

    service_name = sys.argv[1]
    failure_reason = sys.argv[2] if len(sys.argv) > 2 else None

    # Try to get failure reason from systemd if not provided
    if not failure_reason:
        try:
            import subprocess

            result = subprocess.run(
                ["systemctl", "show", service_name, "--property=Result"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if "=" in output:
                    failure_reason = output.split("=", 1)[1]
        except Exception:
            pass

    success = send_worker_failure_email(service_name=service_name, failure_reason=failure_reason)

    if success:
        print(f"Failure notification sent for {service_name}")
        sys.exit(0)
    else:
        print(f"Failed to send notification for {service_name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
