"""
BattyCoda Models Package

This package contains all the application models organized into logical modules:
- user.py: User profiles, groups, and authentication models
- organization.py: Projects, species, and organizational models
- recording.py: Recording, segments, and segmentation models
- task.py: Task and task batch models
- classification.py: Detection and classification models
- notification.py: User notification models
- clustering.py: Unsupervised clustering models

IMPORTANT: Email Uniqueness Constraint
The built-in Django User model does not enforce email uniqueness by default.
A database-level unique constraint has been added to the auth_user.email field
via migration 0014_auto_20250716_1838.py to prevent duplicate email addresses.
All code that queries users by email should handle the uniqueness properly.
"""

from .classification import CallProbability, ClassificationResult, ClassificationRun, Classifier, ClassifierTrainingJob
from .notification import UserNotification as Notification
from .organization import Call, Project, Species
from .recording import Recording
from .segmentation import Segment, Segmentation, SegmentationAlgorithm
from .spectrogram import SpectrogramJob
from .task import Task, TaskBatch

# Import all models for Django model registration
from .user import Group, GroupInvitation, GroupMembership, UserProfile

# Optional import for clustering models - will not fail if module doesn't exist yet
try:
    from .clustering import (
        Cluster,
        ClusterCallMapping,
        ClusteringAlgorithm,
        ClusteringRun,
        ClusteringRunSegmentation,
        SegmentCluster,
    )
except ImportError:
    # Clustering module not yet installed/activated
    pass
