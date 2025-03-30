from django.db import migrations

def create_default_classifiers(apps, schema_editor):
    """
    Create default classifiers for the application.
    This is run as a data migration to ensure classifiers exist in a fresh database.
    """
    Classifier = apps.get_model('battycoda_app', 'Classifier')
    
    # Check if we already have classifiers to avoid duplicates
    if Classifier.objects.count() == 0:
        # Create the R-direct classifier
        Classifier.objects.create(
            name="R-direct Classifier",
            description="Uses R to process audio segments and classify bat calls based on spectral features.",
            response_format="full_probability",
            celery_task="battycoda_app.audio.task_modules.detection_tasks.run_call_detection",
            service_url="http://localhost:8000",
            endpoint="/classify",
            is_active=True
        )
        
        # Create the dummy classifier
        Classifier.objects.create(
            name="Dummy Classifier",
            description="A simple classifier that assigns equal probability to all call types. Used for testing and demo purposes.",
            response_format="full_probability",
            celery_task="battycoda_app.audio.task_modules.detection_tasks.run_dummy_classifier",
            is_active=True
        )

class Migration(migrations.Migration):
    dependencies = [
        ('battycoda_app', '0002_create_default_segmentation_algorithms'),
    ]

    operations = [
        migrations.RunPython(create_default_classifiers),
    ]