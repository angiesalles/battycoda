# Generated by Django 5.1.7 on 2025-03-18 14:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('battycoda_app', '0005_project_alter_task_project_alter_taskbatch_project_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='species',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='species_images/'),
        ),
        migrations.CreateModel(
            name='Call',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=50)),
                ('long_name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('species', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calls', to='battycoda_app.species')),
            ],
            options={
                'ordering': ['short_name'],
                'unique_together': {('species', 'short_name')},
            },
        ),
    ]
