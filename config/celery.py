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
    "battycoda_app.audio.task_modules.training_tasks"
])

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
