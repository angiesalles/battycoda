"""
Migration to add unsupervised clustering models to BattyCoda.
This provides a parallel system for clustering audio segments without requiring species associations.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('battycoda_app', '0004_add_file_ready_flag'),  # Update this to your latest migration
        ('auth', '0012_alter_user_first_name_max_length'),  # Default Django auth
    ]

    operations = [
        migrations.CreateModel(
            name='ClusteringAlgorithm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the clustering algorithm', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Description of how the algorithm works', null=True)),
                ('algorithm_type', models.CharField(choices=[('kmeans', 'K-Means Clustering'), ('dbscan', 'DBSCAN Density-Based Clustering'), ('hierarchical', 'Hierarchical Clustering'), ('gaussian_mixture', 'Gaussian Mixture Model'), ('spectral', 'Spectral Clustering'), ('custom', 'Custom Algorithm')], help_text='Type of clustering algorithm to use', max_length=50)),
                ('parameters', models.JSONField(blank=True, help_text="JSON with algorithm parameters (e.g., {'n_clusters': 5, 'random_state': 42})", null=True)),
                ('celery_task', models.CharField(default='battycoda_app.audio.task_modules.clustering_tasks.run_clustering', help_text='Fully qualified Celery task name to execute this algorithm', max_length=255)),
                ('service_url', models.CharField(blank=True, help_text='URL of the external service, if applicable', max_length=255, null=True)),
                ('endpoint', models.CharField(blank=True, help_text='Endpoint path for the service', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this algorithm is currently active')),
                ('created_by', models.ForeignKey(help_text='User who created this algorithm', on_delete=django.db.models.deletion.CASCADE, related_name='created_clustering_algorithms', to='auth.user')),
                ('group', models.ForeignKey(blank=True, help_text="Group that owns this algorithm. If null, it's available to all groups", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clustering_algorithms', to='battycoda_app.group')),
            ],
            options={
                'verbose_name': 'Clustering Algorithm',
                'verbose_name_plural': 'Clustering Algorithms',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ClusteringRun',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name for this clustering run', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Description of this clustering run', null=True)),
                ('runtime_parameters', models.JSONField(blank=True, help_text='JSON with runtime parameters that override algorithm defaults', null=True)),
                ('n_clusters', models.IntegerField(blank=True, help_text='Number of clusters to create (for algorithms that need this specified)', null=True)),
                ('feature_extraction_method', models.CharField(default='mfcc', help_text='Method used to extract features from audio (e.g., mfcc, spectrogram)', max_length=100)),
                ('feature_parameters', models.JSONField(blank=True, help_text='JSON with parameters for feature extraction', null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', help_text='Current status of the clustering run', max_length=20)),
                ('progress', models.FloatField(default=0.0, help_text='Progress percentage from 0-100')),
                ('error_message', models.TextField(blank=True, help_text='Error message if the run failed', null=True)),
                ('task_id', models.CharField(blank=True, help_text='Celery task ID for this clustering run', max_length=100, null=True)),
                ('num_segments_processed', models.IntegerField(default=0, help_text='Number of segments processed in this run')),
                ('num_clusters_created', models.IntegerField(default=0, help_text='Number of clusters created in this run')),
                ('silhouette_score', models.FloatField(blank=True, help_text='Silhouette score for clustering quality (-1 to 1, higher is better)', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('algorithm', models.ForeignKey(help_text='The clustering algorithm used for this run', on_delete=django.db.models.deletion.CASCADE, related_name='clustering_runs', to='battycoda_app.clusteringalgorithm')),
                ('created_by', models.ForeignKey(help_text='User who created this clustering run', on_delete=django.db.models.deletion.CASCADE, related_name='clustering_runs', to='auth.user')),
                ('group', models.ForeignKey(help_text='Group that owns this clustering run', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='clustering_runs', to='battycoda_app.group')),
                ('segmentation', models.ForeignKey(help_text='The segmentation containing segments to cluster', on_delete=django.db.models.deletion.CASCADE, related_name='clustering_runs', to='battycoda_app.segmentation')),
            ],
            options={
                'verbose_name': 'Clustering Run',
                'verbose_name_plural': 'Clustering Runs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Cluster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cluster_id', models.IntegerField(help_text='Internal numeric ID of the cluster (0, 1, 2...)')),
                ('label', models.CharField(blank=True, help_text='Expert-assigned label for this cluster', max_length=255, null=True)),
                ('description', models.TextField(blank=True, help_text='Description of the acoustic pattern in this cluster', null=True)),
                ('is_labeled', models.BooleanField(default=False, help_text='Whether an expert has assigned a label to this cluster')),
                ('size', models.IntegerField(default=0, help_text='Number of segments in this cluster')),
                ('coherence', models.FloatField(blank=True, help_text='Measure of cluster coherence (higher is more coherent)', null=True)),
                ('vis_x', models.FloatField(blank=True, help_text='X-coordinate for 2D visualization', null=True)),
                ('vis_y', models.FloatField(blank=True, help_text='Y-coordinate for 2D visualization', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('clustering_run', models.ForeignKey(help_text='The clustering run that created this cluster', on_delete=django.db.models.deletion.CASCADE, related_name='clusters', to='battycoda_app.clusteringrun')),
                ('representative_segment', models.ForeignKey(blank=True, help_text='Segment that best represents this cluster', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='representing_clusters', to='battycoda_app.segment')),
            ],
            options={
                'verbose_name': 'Cluster',
                'verbose_name_plural': 'Clusters',
                'ordering': ['clustering_run', 'cluster_id'],
                'unique_together': {('clustering_run', 'cluster_id')},
            },
        ),
        migrations.CreateModel(
            name='SegmentCluster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('confidence', models.FloatField(default=1.0, help_text="Confidence score (0-1) for this segment's membership in the cluster")),
                ('distance_to_center', models.FloatField(blank=True, help_text='Distance of this segment to the cluster center', null=True)),
                ('cluster', models.ForeignKey(help_text='The cluster this segment belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='members', to='battycoda_app.cluster')),
                ('segment', models.ForeignKey(help_text='The segment that belongs to a cluster', on_delete=django.db.models.deletion.CASCADE, related_name='segment_clusters', to='battycoda_app.segment')),
            ],
            options={
                'verbose_name': 'Segment Cluster Membership',
                'verbose_name_plural': 'Segment Cluster Memberships',
                'ordering': ['-confidence'],
                'unique_together': {('segment', 'cluster')},
            },
        ),
        migrations.CreateModel(
            name='ClusterCallMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('confidence', models.FloatField(help_text='Confidence score (0-1) for the mapping between cluster and call type')),
                ('notes', models.TextField(blank=True, help_text='Notes about this mapping', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('call', models.ForeignKey(help_text='The call type this cluster is mapped to', on_delete=django.db.models.deletion.CASCADE, related_name='cluster_mappings', to='battycoda_app.call')),
                ('cluster', models.ForeignKey(help_text='The cluster being mapped to a call type', on_delete=django.db.models.deletion.CASCADE, related_name='call_mappings', to='battycoda_app.cluster')),
                ('created_by', models.ForeignKey(help_text='User who created this mapping', on_delete=django.db.models.deletion.CASCADE, related_name='cluster_mappings', to='auth.user')),
            ],
            options={
                'verbose_name': 'Cluster-Call Mapping',
                'verbose_name_plural': 'Cluster-Call Mappings',
                'ordering': ['-confidence'],
                'unique_together': {('cluster', 'call')},
            },
        ),
    ]