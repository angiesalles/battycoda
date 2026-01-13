import logging
from celery import shared_task
from django.core.management import call_command
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task
def process_audio_file(file_path):
    """
    Process an uploaded audio file

    This is a placeholder task that can be expanded for audio processing
    """

    # TODO: Implement actual audio processing
    return True

@shared_task(bind=True)
def calculate_audio_duration(self, recording_id, retry_count=0):
    """
    Calculate and update the duration and sample rate for a recording.
    
    This task is extremely persistent and will NEVER give up:
    - Retries indefinitely with exponential backoff for any error
    - No maximum retry limit
    - Will keep retrying even if the recording doesn't exist (it might be created later)
    - Will keep retrying if the file is missing
    """
    import os
    import logging
    import time
    from datetime import datetime

    import soundfile as sf
    from django.db.utils import OperationalError

    from .models.recording import Recording
    
    logger = logging.getLogger(__name__)
    
    # Calculate retry delay with exponential backoff, capped at 1 hour
    # 1st retry: 4s, 2nd: 8s, 3rd: 16s... up to 1 hour max
    retry_delay = min(4 * (2 ** retry_count), 3600)
    
    # Log attempt with timestamp for tracking long-running retries
    logger.info(f"[{datetime.now().isoformat()}] Attempt #{retry_count+1} to calculate audio info for recording {recording_id}")

    try:
        # Try to get the recording from the database
        try:
            recording = Recording.objects.get(id=recording_id)
            logger.info(f"Found recording {recording_id}: {recording.name}")
        except Recording.DoesNotExist:
            # Recording doesn't exist yet - retry
            logger.warning(f"Recording {recording_id} does not exist yet, will retry in {retry_delay}s")
            self.retry(countdown=retry_delay, kwargs={'retry_count': retry_count + 1})
            return
        except OperationalError as db_error:
            # Database connection issue - retry
            logger.warning(f"Database error for recording {recording_id}, will retry in {retry_delay}s: {str(db_error)}")
            self.retry(countdown=retry_delay, kwargs={'retry_count': retry_count + 1})
            return

        # Skip if both duration and sample rate are already set
        if recording.duration and recording.sample_rate:
            logger.info(f"Recording {recording_id} already has duration and sample rate set")
            return True

        # Always set file_ready to True to ensure processing continues
        if not recording.file_ready:
            logger.info(f"Setting file_ready=True for recording {recording_id}")
            recording.file_ready = True
            try:
                recording.save(update_fields=["file_ready"])
            except Exception as save_error:
                logger.warning(f"Could not update file_ready: {str(save_error)}, will retry")
                self.retry(countdown=retry_delay, kwargs={'retry_count': retry_count + 1})
                return

        # Check if file exists and retry if not
        if not os.path.exists(recording.wav_file.path):
            logger.warning(f"File missing for recording {recording_id}: {recording.wav_file.path}, will retry in {retry_delay}s")
            self.retry(countdown=retry_delay, kwargs={'retry_count': retry_count + 1})
            return

        # Try to extract audio information from file
        try:
            info = sf.info(recording.wav_file.path)
            duration = info.duration
            sample_rate = info.samplerate
        except Exception as audio_error:
            # If file exists but can't be read, perhaps it's corrupted or still being written
            logger.warning(f"Error reading audio file for recording {recording_id}, will retry in {retry_delay}s: {str(audio_error)}")
            self.retry(countdown=retry_delay, kwargs={'retry_count': retry_count + 1})
            return
        
        logger.info(f"Audio info for recording {recording_id}: duration={duration}s, sample_rate={sample_rate}Hz")

        # Update the recording
        update_fields = []

        # Only update duration if it's not already set
        if not recording.duration:
            recording.duration = duration
            update_fields.append("duration")

        # Only update sample_rate if it's not already set
        if not recording.sample_rate:
            recording.sample_rate = sample_rate
            update_fields.append("sample_rate")

        # Use update_fields to avoid triggering save signal again
        if update_fields:
            try:
                recording.save(update_fields=update_fields)
                logger.info(f"Successfully updated recording {recording_id} with duration {duration}s and sample rate {sample_rate}Hz")
            except Exception as save_error:
                logger.warning(f"Error saving audio info: {str(save_error)}, will retry")
                self.retry(countdown=retry_delay, kwargs={'retry_count': retry_count + 1})
                return

        return True

    except Exception as e:
        # Catch any other exceptions and retry
        logger.error(f"Unexpected error processing recording {recording_id}: {str(e)}")
        self.retry(countdown=retry_delay, kwargs={'retry_count': retry_count + 1})
        return

@shared_task(bind=True, max_retries=3)
def backup_database_to_s3(self, bucket_name=None, prefix=None):
    """
    Celery task to backup the database to S3.
    Sends email notification to admins if all retries are exhausted.
    """
    from .email_utils import send_backup_failure_email

    # Use settings defaults if not provided
    bucket_name = bucket_name or getattr(settings, 'DATABASE_BACKUP_BUCKET', 'backup-battycoda')
    prefix = prefix or getattr(settings, 'DATABASE_BACKUP_PREFIX', 'database-backups/')

    try:
        logger.info(f"Starting database backup to S3 bucket: {bucket_name}")

        # Call the Django management command
        call_command('backup_database', bucket=bucket_name, prefix=prefix)

        logger.info("Database backup completed successfully")
        return "Database backup completed successfully"

    except Exception as exc:
        logger.error(f"Database backup failed (attempt {self.request.retries + 1}/{self.max_retries + 1}): {str(exc)}")

        # Check if we've exhausted all retries
        if self.request.retries >= self.max_retries:
            logger.error("Database backup failed after all retries, sending alert email")
            send_backup_failure_email(
                error_message=str(exc),
                bucket_name=bucket_name
            )
            raise  # Re-raise to mark task as failed

        # Retry the task with exponential backoff
        retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=retry_delay)


# Cache for tracking last alert time to avoid spamming
_last_disk_alert_time = None


@shared_task
def check_disk_usage(threshold=90, cooldown_hours=4):
    """
    Check disk usage and send email alert if any disk exceeds threshold.

    Args:
        threshold (int): Percentage threshold to trigger alert (default: 90)
        cooldown_hours (int): Hours to wait between alerts (default: 4)

    Returns:
        dict: Status information about the check
    """
    import shutil
    import datetime

    global _last_disk_alert_time

    from .email_utils import send_disk_usage_warning_email

    def format_bytes(bytes_val):
        """Format bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"

    # Define mount points to check
    mount_points = ['/', '/home']

    disks_over_threshold = []
    all_disk_info = []

    for mount in mount_points:
        try:
            usage = shutil.disk_usage(mount)
            percent = (usage.used / usage.total) * 100

            disk_info = {
                'mount': mount,
                'total': format_bytes(usage.total),
                'used': format_bytes(usage.used),
                'free': format_bytes(usage.free),
                'percent': round(percent, 1)
            }
            all_disk_info.append(disk_info)

            if percent >= threshold:
                disks_over_threshold.append(disk_info)
                logger.warning(f"Disk {mount} usage is {percent:.1f}% (threshold: {threshold}%)")
            else:
                logger.info(f"Disk {mount} usage is {percent:.1f}% (OK)")

        except (OSError, FileNotFoundError) as e:
            logger.error(f"Could not check disk usage for {mount}: {e}")

    # Send alert if any disk exceeds threshold
    if disks_over_threshold:
        now = datetime.datetime.now()

        # Check cooldown to avoid spamming
        should_send = True
        if _last_disk_alert_time:
            time_since_last = now - _last_disk_alert_time
            if time_since_last.total_seconds() < cooldown_hours * 3600:
                should_send = False
                logger.info(
                    f"Disk alert suppressed (cooldown: {cooldown_hours}h, "
                    f"last alert: {_last_disk_alert_time.isoformat()})"
                )

        if should_send:
            success = send_disk_usage_warning_email(
                disk_info=disks_over_threshold,
                threshold=threshold
            )
            if success:
                _last_disk_alert_time = now
                logger.info(f"Disk usage alert sent for {len(disks_over_threshold)} disk(s)")
            else:
                logger.error("Failed to send disk usage alert email")

            return {
                'status': 'alert_sent' if success else 'alert_failed',
                'disks_over_threshold': disks_over_threshold,
                'all_disks': all_disk_info
            }
        else:
            return {
                'status': 'alert_suppressed',
                'disks_over_threshold': disks_over_threshold,
                'all_disks': all_disk_info
            }

    return {
        'status': 'ok',
        'all_disks': all_disk_info
    }