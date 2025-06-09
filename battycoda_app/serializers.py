"""
Serializers for BattyCoda API.
"""
from rest_framework import serializers
from .models import Recording, Project, Task, TaskBatch
from .models.organization import Species
from .models.recording import Segmentation, SegmentationAlgorithm


class SpeciesSerializer(serializers.ModelSerializer):
    """
    Serializer for Species model.
    """
    class Meta:
        model = Species
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Project model.
    """
    species = SpeciesSerializer(read_only=True)
    species_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'species', 'species_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class RecordingSerializer(serializers.ModelSerializer):
    """
    Serializer for Recording model.
    """
    project = ProjectSerializer(read_only=True)
    project_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    # File URLs for API access
    wav_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Recording
        fields = [
            'id', 'name', 'description', 'location', 'recorded_date', 
            'duration', 'sample_rate', 'project', 'project_id',
            'wav_file_url', 'created_at'
        ]
        read_only_fields = ['id', 'duration', 'sample_rate', 'created_at']

    def get_wav_file_url(self, obj):
        if obj.wav_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.wav_file.url)
        return None


class TaskBatchSerializer(serializers.ModelSerializer):
    """
    Serializer for TaskBatch model.
    """
    species = SpeciesSerializer(read_only=True)
    species_id = serializers.IntegerField(write_only=True)
    
    # Computed fields
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    pending_tasks = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = TaskBatch
        fields = [
            'id', 'name', 'description', 'species', 'species_id',
            'total_tasks', 'completed_tasks', 'pending_tasks', 'progress_percentage',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_total_tasks(self, obj):
        return obj.tasks.count()

    def get_completed_tasks(self, obj):
        return obj.tasks.filter(status='completed').count()

    def get_pending_tasks(self, obj):
        return obj.tasks.filter(status='pending').count()

    def get_progress_percentage(self, obj):
        total = self.get_total_tasks(obj)
        if total == 0:
            return 0
        completed = self.get_completed_tasks(obj)
        return round((completed / total) * 100, 1)


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.
    """
    batch = TaskBatchSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'batch', 'status', 'onset', 'offset', 'label', 'notes', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SegmentationAlgorithmSerializer(serializers.ModelSerializer):
    """
    Serializer for SegmentationAlgorithm model.
    """
    class Meta:
        model = SegmentationAlgorithm
        fields = [
            'id', 'name', 'description', 'algorithm_type', 
            'default_min_duration_ms', 'default_smooth_window', 'default_threshold_factor'
        ]
        read_only_fields = ['id']


class SegmentationSerializer(serializers.ModelSerializer):
    """
    Serializer for Segmentation model.
    """
    recording = RecordingSerializer(read_only=True)
    recording_id = serializers.IntegerField(write_only=True)
    algorithm = SegmentationAlgorithmSerializer(read_only=True)
    algorithm_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    segments_count = serializers.SerializerMethodField()

    class Meta:
        model = Segmentation
        fields = [
            'id', 'recording', 'recording_id', 'name', 'is_active', 
            'algorithm', 'algorithm_id', 'status', 'progress',
            'min_duration_ms', 'smooth_window', 'threshold_factor',
            'segments_created', 'segments_count', 'manually_edited',
            'created_by_username', 'created_at', 'updated_at', 'error_message'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'task_id', 'progress']

    def get_segments_count(self, obj):
        return obj.segments.count()