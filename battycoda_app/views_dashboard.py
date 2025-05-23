"""
Dashboard view for the BattyCoda application.
"""

from django.db import models
from django.shortcuts import redirect, render

from .models.detection import DetectionRun
from .models.organization import Project, Species
from .models.recording import Recording, Segmentation
from .models.task import TaskBatch

# Set up logging

def index(request):
    """Root URL - show dashboard if logged in, or login page if not"""
    if request.user.is_authenticated:
        # Get user profile
        profile = request.user.profile

        # Initialize context dictionary
        context = {}

        if profile.group:
            if profile.is_current_group_admin:
                # Admin sees all batches in their group
                recent_batches = TaskBatch.objects.filter(group=profile.group).order_by("-created_at")[:5]
            else:
                # Regular user only sees their own batches
                recent_batches = TaskBatch.objects.filter(created_by=request.user).order_by("-created_at")[:5]
        else:
            # Fallback to showing only user's batches if no group is assigned
            recent_batches = TaskBatch.objects.filter(created_by=request.user).order_by("-created_at")[:5]

        context["recent_batches"] = recent_batches

        # Get recent recordings
        if profile.group:
            if profile.is_current_group_admin:
                # Admin sees all recordings in their group
                recent_recordings = Recording.objects.filter(group=profile.group).order_by("-created_at")[:5]
            else:
                # Regular user only sees their own recordings
                recent_recordings = Recording.objects.filter(created_by=request.user).order_by("-created_at")[:5]
        else:
            # Fallback to showing only user's recordings if no group is assigned
            recent_recordings = Recording.objects.filter(created_by=request.user).order_by("-created_at")[:5]

        context["recent_recordings"] = recent_recordings

        # Get recent classification runs
        if profile.group:
            if profile.is_current_group_admin:
                # Admin sees all runs in their group
                recent_runs = DetectionRun.objects.filter(group=profile.group).order_by("-created_at")[:5]
            else:
                # Regular user only sees their own runs
                recent_runs = DetectionRun.objects.filter(created_by=request.user).order_by("-created_at")[:5]
        else:
            # Fallback to showing only user's runs if no group is assigned
            recent_runs = DetectionRun.objects.filter(created_by=request.user).order_by("-created_at")[:5]

        context["recent_runs"] = recent_runs

        # Get recent species, including system species
        if profile.group:
            # Include system species and group species
            recent_species = Species.objects.filter(
                models.Q(is_system=True) | models.Q(group=profile.group)
            ).order_by("-created_at")[:5]
        else:
            # Include system species and user's species
            recent_species = Species.objects.filter(
                models.Q(is_system=True) | models.Q(created_by=request.user)
            ).order_by("-created_at")[:5]

        context["recent_species"] = recent_species

        # Get recent projects
        if profile.group:
            recent_projects = Project.objects.filter(group=profile.group).order_by("-created_at")[:5]
        else:
            recent_projects = Project.objects.filter(created_by=request.user).order_by("-created_at")[:5]

        context["recent_projects"] = recent_projects
        
        # Get recent segmentations
        if profile.group:
            if profile.is_current_group_admin:
                # Admin sees all segmentations in their group
                recent_segmentations = Segmentation.objects.filter(recording__group=profile.group).order_by("-created_at")[:5]
            else:
                # Regular user only sees their own segmentations
                recent_segmentations = Segmentation.objects.filter(created_by=request.user).order_by("-created_at")[:5]
        else:
            # Fallback to showing only user's segmentations if no group is assigned
            recent_segmentations = Segmentation.objects.filter(created_by=request.user).order_by("-created_at")[:5]
            
        context["recent_segmentations"] = recent_segmentations

        # Get stats
        if profile.group:
            context["total_recordings"] = Recording.objects.filter(group=profile.group).count()
            context["total_batches"] = TaskBatch.objects.filter(group=profile.group).count()
            # Count system species plus group species
            context["total_species"] = Species.objects.filter(
                models.Q(is_system=True) | models.Q(group=profile.group)
            ).count()
            context["total_projects"] = Project.objects.filter(group=profile.group).count()

            # Get in-progress segmentations
            context["active_segmentations"] = Segmentation.objects.filter(
                recording__group=profile.group, status__in=["pending", "in_progress"]
            ).count()

            # Get in-progress classifications
            context["active_classifications"] = DetectionRun.objects.filter(
                group=profile.group, status__in=["pending", "in_progress"]
            ).count()
        else:
            context["total_recordings"] = Recording.objects.filter(created_by=request.user).count()
            context["total_batches"] = TaskBatch.objects.filter(created_by=request.user).count()
            # Count system species plus user-created species
            context["total_species"] = Species.objects.filter(
                models.Q(is_system=True) | models.Q(created_by=request.user)
            ).count()
            context["total_projects"] = Project.objects.filter(created_by=request.user).count()

            # Get in-progress segmentations
            context["active_segmentations"] = Segmentation.objects.filter(
                created_by=request.user, status__in=["pending", "in_progress"]
            ).count()

            # Get in-progress classifications
            context["active_classifications"] = DetectionRun.objects.filter(
                created_by=request.user, status__in=["pending", "in_progress"]
            ).count()

        return render(request, "dashboard.html", context)
    else:
        return redirect("battycoda_app:landing")
