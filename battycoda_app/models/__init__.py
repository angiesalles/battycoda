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

# Import all models for Django model registration
from .user import Group, GroupInvitation, GroupMembership, UserProfile
from .organization import Project, Species, Call
from .recording import Recording
from .segmentation import Segment, Segmentation, SegmentationAlgorithm
from .task import Task, TaskBatch
from .classification import (
    Classifier, 
    ClassificationRun, 
    ClassificationResult, 
    CallProbability,
    ClassifierTrainingJob
)
from .notification import UserNotification as Notification
from .spectrogram import SpectrogramJob

# Optional import for clustering models - will not fail if module doesn't exist yet
try:
    from .clustering import (
        ClusteringAlgorithm,
        ClusteringRun,
        ClusteringRunSegmentation,
        Cluster,
        SegmentCluster,
        ClusterCallMapping
    )
except ImportError:
    # Clustering module not yet installed/activated
    pass
