from django.db import migrations

def create_default_segmentation_algorithms(apps, schema_editor):
    """
    Create default segmentation algorithms for the application.
    This is run as a data migration to ensure algorithms exist in a fresh database.
    """
    SegmentationAlgorithm = apps.get_model('battycoda_app', 'SegmentationAlgorithm')
    
    # Check if we already have algorithms to avoid duplicates
    if SegmentationAlgorithm.objects.count() == 0:
        # Create threshold-based algorithm
        SegmentationAlgorithm.objects.create(
            name="Energy Threshold Detector",
            description="Simple energy-based detector that identifies bat calls based on signal energy.",
            algorithm_type="threshold",
            celery_task="battycoda_app.audio.task_modules.segmentation_tasks.auto_segment_recording_task",
            is_active=True,
            default_min_duration_ms=10,
            default_smooth_window=3,
            default_threshold_factor=0.5
        )
        
        # Create more advanced algorithm
        SegmentationAlgorithm.objects.create(
            name="Adaptive Energy Detector",
            description="Advanced energy-based detector that adapts to background noise levels and detects calls with better precision.",
            algorithm_type="energy",
            celery_task="battycoda_app.audio.task_modules.segmentation_tasks.auto_segment_recording_task",
            is_active=True,
            default_min_duration_ms=8,
            default_smooth_window=5,
            default_threshold_factor=0.4
        )

class Migration(migrations.Migration):
    dependencies = [
        ('battycoda_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_segmentation_algorithms),
    ]