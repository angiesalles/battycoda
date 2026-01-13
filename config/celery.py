import os

from celery import Celery
from celery.signals import beat_init, worker_ready, worker_shutdown

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("battycoda")


@beat_init.connect
def run_backup_on_beat_start(**kwargs):
    """Run database backup immediately when celery-beat starts."""
    from battycoda_app.tasks import backup_database_to_s3
    # Delay by 60 seconds to allow worker to fully start
    backup_database_to_s3.apply_async(countdown=60)


@worker_ready.connect
def start_memory_monitor_on_worker_ready(**kwargs):
    """Start memory monitor when Celery worker is ready."""
    from battycoda_app.celery_memory_monitor import start_memory_monitor
    start_memory_monitor()


@worker_shutdown.connect
def stop_memory_monitor_on_shutdown(**kwargs):
    """Stop memory monitor when Celery worker shuts down."""
    from battycoda_app.celery_memory_monitor import stop_memory_monitor
    stop_memory_monitor()

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks([
    "battycoda_app",
    "battycoda_app.audio",
    "battycoda_app.audio.task_modules.spectrogram_tasks",
    "battycoda_app.audio.task_modules.detection_tasks",
    "battycoda_app.audio.task_modules.segmentation_tasks",
    "battycoda_app.audio.task_modules.classification.run_classification",
    "battycoda_app.audio.task_modules.classification.dummy_classifier",
    "battycoda_app.audio.task_modules.training_tasks",
    "battycoda_app.audio.task_modules.clustering.tasks",
    "battycoda_app.audio.task_modules.queue_processor"
])

# Periodic task schedule for queue processing
app.conf.beat_schedule = {
    'process-classification-queue': {
        'task': 'battycoda_app.audio.task_modules.queue_processor.process_classification_queue',
        'schedule': 30.0,  # Run every 30 seconds
    },
    'weekly-database-backup': {
        'task': 'battycoda_app.tasks.backup_database_to_s3',
        'schedule': 604800.0,  # Run every week (7 days * 24 hours * 60 minutes * 60 seconds)
    },
    'check-disk-usage': {
        'task': 'battycoda_app.tasks.check_disk_usage',
        'schedule': 3600.0,  # Run every hour
    },
}
app.conf.timezone = 'UTC'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
