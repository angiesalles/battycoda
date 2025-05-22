"""
BattyCoda Models Package

This package contains all the application models organized into logical modules:
- user.py: User profiles, groups, and authentication models
- organization.py: Projects, species, and organizational models
- recording.py: Recording, segments, and segmentation models
- task.py: Task and task batch models
- detection.py: Detection and classification models
- notification.py: User notification models
- clustering.py: Unsupervised clustering models
"""

# Import all models for Django model registration
from .user import Group, UserProfile
from .organization import Project, Species, Call
from .recording import Recording, Segment, Segmentation, SegmentationAlgorithm
from .task import Task, TaskBatch
from .detection import (
    Classifier, 
    DetectionRun, 
    DetectionResult, 
    CallProbability,
    ClassifierTrainingJob
)
from .notification import UserNotification as Notification

# Optional import for clustering models - will not fail if module doesn't exist yet
try:
    from .clustering import (
        ClusteringAlgorithm,
        ClusteringRun,
        Cluster,
        SegmentCluster,
        ClusterCallMapping
    )
except ImportError:
    # Clustering module not yet installed/activated
    pass
