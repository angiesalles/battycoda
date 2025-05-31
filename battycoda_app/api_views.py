"""
API views for BattyCoda.
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Recording, Project, Task, TaskBatch
from .models.organization import Species
from .serializers import (
    RecordingSerializer,
    SpeciesSerializer,
    ProjectSerializer,
    TaskBatchSerializer,
    TaskSerializer,
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