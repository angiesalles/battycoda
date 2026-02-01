"""Add processing_status field to Recording model.

New recordings start as 'processing' and become 'ready' when spectrogram is generated.
Existing recordings are backfilled as 'ready'.
"""

from django.db import migrations, models


def set_existing_recordings_ready(apps, schema_editor):
    """Backfill existing recordings as ready."""
    Recording = apps.get_model("battycoda_app", "Recording")
    Recording.objects.all().update(processing_status="ready")


class Migration(migrations.Migration):

    dependencies = [
        ("battycoda_app", "0030_alter_call_long_name_and_more"),
    ]

    operations = [
        # Add field with default for new recordings
        migrations.AddField(
            model_name="recording",
            name="processing_status",
            field=models.CharField(
                choices=[("processing", "Processing"), ("ready", "Ready")],
                default="processing",
                help_text="Processing status: 'processing' while spectrogram is being generated, 'ready' when complete",
                max_length=20,
            ),
        ),
        # Backfill existing recordings as ready
        migrations.RunPython(set_existing_recordings_ready, migrations.RunPython.noop),
    ]
