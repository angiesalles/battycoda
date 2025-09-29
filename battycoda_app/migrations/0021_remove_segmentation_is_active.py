# Generated manually to remove is_active field from Segmentation model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('battycoda_app', '0020_rename_detection_run_to_classification_run'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='segmentation',
            name='is_active',
        ),
    ]