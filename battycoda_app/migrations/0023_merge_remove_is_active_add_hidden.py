# Merge migration for removing is_active and adding hidden field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('battycoda_app', '0021_remove_segmentation_is_active'),
        ('battycoda_app', '0022_add_hidden_to_recording'),
    ]

    operations = [
        # No operations needed - this is just a merge migration
    ]