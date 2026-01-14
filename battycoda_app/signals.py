from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .audio.task_modules.spectrogram.hdf5_generation import generate_recording_spectrogram
from .models import (
    ClassificationRun,
    ClassifierTrainingJob,
    Notification,
    Recording,
    Segmentation,
    SpectrogramJob,
)
from .tasks import calculate_audio_duration

# NOTE: These signals are commented out because they duplicate functionality in models.py
# @receiver(post_save, sender=User)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_profile(sender, instance, **kwargs):
#     instance.profile.save()


@receiver(post_save, sender=Recording)
def trigger_audio_info_calculation(sender, instance, **kwargs):
    """
    Signal handler to asynchronously calculate audio duration and sample rate after a recording is saved

    Only triggers when the file_ready flag is set to True, ensuring the file is fully committed
    to disk before trying to access it.
    """
    # Skip if both duration and sample rate are already set
    if instance.duration and instance.sample_rate:
        return

    # Only process recordings where file_ready is True
    if not instance.file_ready:
        return

    # Trigger the Celery task
    calculate_audio_duration.delay(instance.id)


@receiver(post_save, sender=Recording)
def trigger_spectrogram_generation(sender, instance, **kwargs):
    """
    Signal handler to create a background job for generating HDF5 spectrogram when a recording is created
    """
    # Only process recordings where file_ready is True
    if not instance.file_ready:
        return

    # Skip if spectrogram job already exists for this recording
    if SpectrogramJob.objects.filter(recording=instance).exists():
        return

    # Create a job and trigger generation in the background
    job = SpectrogramJob.objects.create(
        recording=instance,
        name=f"Spectrogram for {instance.name}",
        status="pending",
        created_by=instance.created_by,
        group=instance.group,
    )

    # Trigger async task
    result = generate_recording_spectrogram.delay(instance.id)
    job.celery_task_id = result.id
    job.save()


@receiver(post_save, sender=Segmentation)
def segmentation_status_changed(sender, instance, **kwargs):
    """
    Signal handler to create notifications when segmentation status changes to completed or failed
    """
    # Skip notifications for segmentations created in the last minute with initial completed status
    # This avoids generating notifications for demo data during user creation
    created_just_now = instance.created_at > timezone.now() - timezone.timedelta(minutes=1)
    first_save = kwargs.get("created", False)

    # Only notify about real segmentation jobs, not demo data being created initially as completed
    if created_just_now and first_save and instance.status == "completed":
        return

    # Only create notifications for status transitions to completed or failed
    if instance.status == "completed":
        # Create success notification
        Notification.add_segmentation_notification(user=instance.created_by, segmentation=instance, success=True)
    elif instance.status == "failed":
        # Create failure notification
        Notification.add_segmentation_notification(user=instance.created_by, segmentation=instance, success=False)


@receiver(post_save, sender=ClassificationRun)
def classification_run_status_changed(sender, instance, **kwargs):
    """
    Signal handler to create notifications when classification run status changes to completed or failed
    """
    # Skip notifications for classification runs created in the last minute with initial completed status
    # This avoids generating notifications for demo data during user creation
    created_just_now = instance.created_at > timezone.now() - timezone.timedelta(minutes=1)
    first_save = kwargs.get("created", False)

    # Only notify about real classification runs, not demo data being created initially as completed
    if created_just_now and first_save and instance.status == "completed":
        return

    # Only create notifications for status transitions to completed or failed
    if instance.status == "completed":
        # Create success notification
        Notification.add_classification_notification(
            user=instance.created_by, classification_run=instance, success=True
        )
    elif instance.status == "failed":
        # Create failure notification
        Notification.add_classification_notification(
            user=instance.created_by, classification_run=instance, success=False
        )


@receiver(post_save, sender=ClassifierTrainingJob)
def training_job_status_changed(sender, instance, **kwargs):
    """
    Signal handler to create notifications when classifier training job status changes to completed or failed
    """
    # Skip notifications for training jobs created in the last minute with initial completed status
    # This avoids generating notifications for demo data during user creation
    created_just_now = instance.created_at > timezone.now() - timezone.timedelta(minutes=1)
    first_save = kwargs.get("created", False)

    # Only notify about real training jobs, not demo data being created initially as completed
    if created_just_now and first_save and instance.status == "completed":
        return

    # Only create notifications for status transitions to completed or failed
    if instance.status == "completed":
        # Create success notification
        Notification.add_training_notification(user=instance.created_by, training_job=instance, success=True)
    elif instance.status == "failed":
        # Create failure notification
        Notification.add_training_notification(user=instance.created_by, training_job=instance, success=False)
