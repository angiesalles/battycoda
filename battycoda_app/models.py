"""
BattyCoda Models Module

Re-exports all model classes from the models package for backward compatibility.
"""

from battycoda_app.models.classification import CallProbability, Classifier, ClassificationResult, ClassificationRun

# Backwards compatibility aliases
ClassificationRun = ClassificationRun
ClassificationResult = ClassificationResult
from battycoda_app.models.organization import Call, Project, Species
from battycoda_app.models.recording import Recording, Segment, Segmentation, SegmentationAlgorithm
from battycoda_app.models.task import Task, TaskBatch

# Re-export all models from the models package
from battycoda_app.models.user import Group, GroupInvitation, GroupMembership, LoginCode, UserProfile

# For backwards compatibility, if any code directly imports from this file
__all__ = [
    # User models
    "Group",
    "GroupInvitation",
    "GroupMembership",
    "LoginCode",
    "UserProfile",
    # Organization models
    "Project",
    "Species",
    "Call",
    # Recording models
    "Recording",
    "Segment",
    "Segmentation",
    "SegmentationAlgorithm",
    # Task models
    "Task",
    "TaskBatch",
    # Classification models
    "Classifier",
    "ClassificationRun",
    "ClassificationResult", 
    "CallProbability",
    # Backwards compatibility aliases
    "ClassificationRun",
    "ClassificationResult",
]
