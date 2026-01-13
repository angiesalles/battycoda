"""
Management command to send email to all users.

Usage:
    # Send to all users with inline message
    python manage.py send_mass_email --subject "Important Update" --message "Hello, this is a message."

    # Send to all users from a file
    python manage.py send_mass_email --subject "Important Update" --message-file message.txt

    # Send HTML email (plain text auto-generated from HTML)
    python manage.py send_mass_email --subject "Update" --html-file email.html

    # Preview recipients without sending (dry run)
    python manage.py send_mass_email --subject "Test" --message "Test" --dry-run

    # Send only to users in a specific group
    python manage.py send_mass_email --subject "Update" --message "Hello" --group "Research Team"

    # Send only to active users (default)
    python manage.py send_mass_email --subject "Update" --message "Hello"

    # Include inactive users
    python manage.py send_mass_email --subject "Update" --message "Hello" --include-inactive
"""

import re
import time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from battycoda_app.email_utils import send_mail
from battycoda_app.models import Group


class Command(BaseCommand):
    help = "Send an email to all users (or a filtered subset)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--subject",
            required=True,
            help="Email subject line",
        )
        parser.add_argument(
            "--message",
            help="Plain text message body (inline)",
        )
        parser.add_argument(
            "--message-file",
            help="Path to file containing plain text message",
        )
        parser.add_argument(
            "--html-file",
            help="Path to file containing HTML message (plain text auto-generated if --message not provided)",
        )
        parser.add_argument(
            "--group",
            help="Only send to users in this group (by name)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview recipients without actually sending emails",
        )
        parser.add_argument(
            "--include-inactive",
            action="store_true",
            help="Include inactive users (by default only active users receive emails)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.1,
            help="Delay between emails in seconds (default: 0.1, helps avoid rate limits)",
        )

    def handle(self, *args, **options):
        subject = options["subject"]
        message = options.get("message")
        message_file = options.get("message_file")
        html_file = options.get("html_file")
        group_name = options.get("group")
        dry_run = options["dry_run"]
        include_inactive = options["include_inactive"]
        delay = options["delay"]

        # Validate that we have some message content
        if not message and not message_file and not html_file:
            raise CommandError("You must provide --message, --message-file, or --html-file")

        # Load message from file if specified
        if message_file:
            try:
                with open(message_file, "r") as f:
                    message = f.read()
            except FileNotFoundError:
                raise CommandError(f"Message file not found: {message_file}")

        # Load HTML from file if specified
        html_message = None
        if html_file:
            try:
                with open(html_file, "r") as f:
                    html_message = f.read()
            except FileNotFoundError:
                raise CommandError(f"HTML file not found: {html_file}")

            # If no plain text message provided, generate from HTML
            if not message:
                message = self.html_to_plain_text(html_message)

        # Build user queryset
        users = User.objects.filter(email__isnull=False).exclude(email="")

        if not include_inactive:
            users = users.filter(is_active=True)

        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                users = users.filter(group_memberships__group=group)
            except Group.DoesNotExist:
                raise CommandError(f"Group not found: {group_name}")

        users = users.distinct()
        user_list = list(users)

        if not user_list:
            self.stdout.write(self.style.WARNING("No users match the criteria."))
            return

        # Display summary
        self.stdout.write(f"\nSubject: {subject}")
        self.stdout.write(f"Recipients: {len(user_list)} user(s)")
        if group_name:
            self.stdout.write(f"Group filter: {group_name}")
        self.stdout.write(f"Include inactive: {include_inactive}")
        self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN - No emails will be sent ===\n"))
            self.stdout.write("Recipients:")
            for user in user_list:
                status = "" if user.is_active else " (inactive)"
                self.stdout.write(f"  - {user.email} ({user.username}){status}")
            self.stdout.write(f"\nMessage preview:\n{'-' * 40}")
            self.stdout.write(message[:500] + ("..." if len(message) > 500 else ""))
            self.stdout.write(f"{'-' * 40}")
            return

        # Confirm before sending
        self.stdout.write(self.style.WARNING(f"\nAbout to send {len(user_list)} email(s)."))
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            self.stdout.write(self.style.ERROR("Aborted."))
            return

        # Send emails
        success_count = 0
        fail_count = 0

        for i, user in enumerate(user_list, 1):
            try:
                result = send_mail(
                    subject=subject,
                    message=message,
                    recipient_list=[user.email],
                    html_message=html_message,
                )
                if result:
                    success_count += 1
                    self.stdout.write(f"[{i}/{len(user_list)}] Sent to {user.email}")
                else:
                    fail_count += 1
                    self.stdout.write(self.style.ERROR(f"[{i}/{len(user_list)}] Failed: {user.email}"))
            except Exception as e:
                fail_count += 1
                self.stdout.write(self.style.ERROR(f"[{i}/{len(user_list)}] Error sending to {user.email}: {e}"))

            # Rate limiting delay
            if delay > 0 and i < len(user_list):
                time.sleep(delay)

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Successfully sent: {success_count}"))
        if fail_count:
            self.stdout.write(self.style.ERROR(f"Failed: {fail_count}"))

    def html_to_plain_text(self, html):
        """Convert HTML to plain text by stripping tags and cleaning up whitespace."""
        # Remove style and script blocks
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Replace common block elements with newlines
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</h[1-6]>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)

        # Strip remaining tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode common HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')

        # Clean up whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        return text
