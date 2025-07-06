import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("battycoda")

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
    "battycoda_app.audio.task_modules.classification_tasks",
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
}
app.conf.timezone = 'UTC'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
