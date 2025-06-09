"""
API views for BattyCoda.
"""
from django.db import models
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Recording, Project, Task, TaskBatch
from .models.organization import Species
from .models.recording import Segmentation, SegmentationAlgorithm
from .serializers import (
    RecordingSerializer,
    SpeciesSerializer,
    ProjectSerializer,
    TaskBatchSerializer,
    TaskSerializer,
    SegmentationSerializer,
    SegmentationAlgorithmSerializer,
)


class RecordingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing recordings.
    """
    queryset = Recording.objects.all()
    serializer_class = RecordingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter by user's group
        user_group = self.request.user.profile.group
        if user_group:
            return Recording.objects.filter(group=user_group)
        return Recording.objects.filter(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def segmentations(self, request, pk=None):
        """
        Get all segmentations for a specific recording.
        """
        recording = self.get_object()
        segmentations = recording.segmentations.all().order_by('-created_at')
        serializer = SegmentationSerializer(segmentations, many=True, context={'request': request})
        return Response(serializer.data)


class SpeciesViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing species.
    """
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter by user's group
        user_group = self.request.user.profile.group
        if user_group:
            return Species.objects.filter(group=user_group)
        return Species.objects.filter(created_by=self.request.user)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing projects.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter by user's group
        user_group = self.request.user.profile.group
        if user_group:
            return Project.objects.filter(group=user_group)
        return Project.objects.filter(created_by=self.request.user)


class TaskBatchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task batches.
    """
    queryset = TaskBatch.objects.all()
    serializer_class = TaskBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter by user's group
        user_group = self.request.user.profile.group
        if user_group:
            return TaskBatch.objects.filter(group=user_group)
        return TaskBatch.objects.filter(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """
        Export task batch data.
        """
        task_batch = self.get_object()
        # TODO: Implement export logic
        return Response({'message': f'Export for task batch {task_batch.name} not yet implemented'})


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing tasks (read-only).
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter by user's group
        user_group = self.request.user.profile.group
        if user_group:
            return Task.objects.filter(batch__group=user_group)
        return Task.objects.filter(batch__created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def annotate(self, request, pk=None):
        """
        Submit annotation for a task.
        """
        task = self.get_object()
        # TODO: Implement annotation logic
        return Response({'message': f'Annotation for task {task.id} not yet implemented'})


class SegmentationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing segmentations.
    """
    queryset = Segmentation.objects.all()
    serializer_class = SegmentationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter by user's group permissions
        user_group = self.request.user.profile.group
        if user_group:
            if self.request.user.profile.is_current_group_admin:
                # Admin sees all segmentations in their group
                return Segmentation.objects.filter(recording__group=user_group).order_by('-created_at')
            else:
                # Regular user only sees their own segmentations
                return Segmentation.objects.filter(created_by=self.request.user).order_by('-created_at')
        return Segmentation.objects.filter(created_by=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # Set the user who created this segmentation
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def duplicates(self, request):
        """
        Find duplicate segmentations (same recording, algorithm, and parameters).
        """
        from django.db.models import Count
        
        # Get all segmentations accessible to the user
        segmentations = self.get_queryset()
        
        # Find groups with potential duplicates
        duplicate_groups = []
        
        # Group by recording, algorithm, and parameters
        processed_combinations = set()
        
        for seg in segmentations:
            # Create a unique key for this combination
            key = (
                seg.recording_id,
                seg.algorithm_id,
                seg.min_duration_ms,
                seg.smooth_window,
                seg.threshold_factor
            )
            
            if key in processed_combinations:
                continue
            
            processed_combinations.add(key)
            
            # Find all segmentations with this same combination
            matching_segmentations = segmentations.filter(
                recording_id=seg.recording_id,
                algorithm_id=seg.algorithm_id,
                min_duration_ms=seg.min_duration_ms,
                smooth_window=seg.smooth_window,
                threshold_factor=seg.threshold_factor
            ).order_by('-created_at')
            
            if matching_segmentations.count() > 1:
                # We have duplicates
                group_data = {
                    'recording_name': seg.recording.name,
                    'recording_id': seg.recording_id,
                    'algorithm_name': seg.algorithm.name if seg.algorithm else 'Manual',
                    'algorithm_id': seg.algorithm_id,
                    'parameters': {
                        'min_duration_ms': seg.min_duration_ms,
                        'smooth_window': seg.smooth_window,
                        'threshold_factor': seg.threshold_factor
                    },
                    'duplicates': SegmentationSerializer(matching_segmentations, many=True, context={'request': request}).data
                }
                duplicate_groups.append(group_data)
        
        return Response({
            'duplicate_groups': duplicate_groups,
            'total_groups': len(duplicate_groups),
            'total_duplicates': sum(len(group['duplicates']) - 1 for group in duplicate_groups)  # -1 because we keep the newest
        })


class SegmentationAlgorithmViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing segmentation algorithms.
    """
    queryset = SegmentationAlgorithm.objects.filter(is_active=True)
    serializer_class = SegmentationAlgorithmSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter by user's group - show algorithms available to their group or global ones
        user_group = self.request.user.profile.group
        if user_group:
            return SegmentationAlgorithm.objects.filter(
                is_active=True
            ).filter(
                models.Q(group=user_group) | models.Q(group__isnull=True)
            )
        return SegmentationAlgorithm.objects.filter(is_active=True, group__isnull=True)