"""
API URL configuration for BattyCoda.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    RecordingViewSet,
    SpeciesViewSet,
    ProjectViewSet,
    TaskBatchViewSet,
    TaskViewSet,
    SegmentationViewSet,
    SegmentationAlgorithmViewSet,
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'recordings', RecordingViewSet)
router.register(r'species', SpeciesViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'task-batches', TaskBatchViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'segmentations', SegmentationViewSet)
router.register(r'segmentation-algorithms', SegmentationAlgorithmViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]