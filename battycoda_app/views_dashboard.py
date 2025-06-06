"""
Dashboard view for the BattyCoda application.
"""

from django.db import models
from django.shortcuts import redirect, render

from .models.detection import DetectionRun
from .models.organization import Project, Species
from .models.recording import Recording, Segmentation
from .models.task import Task, TaskBatch

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

        # Get available batches for task selection dropdown
        available_batches = []
        batches_query = TaskBatch.objects.all()
        
        # Filter batches based on user access
        if profile.group:
            batches_query = batches_query.filter(
                models.Q(group=profile.group) | models.Q(created_by=request.user)
            )
        else:
            batches_query = batches_query.filter(created_by=request.user)
        
        # Only include batches that have pending tasks
        for batch in batches_query.order_by("-created_at"):
            pending_tasks_count = batch.tasks.filter(is_done=False).count()
            if pending_tasks_count > 0:
                # Calculate progress percentage
                total_tasks = batch.tasks.count()
                completed_tasks = total_tasks - pending_tasks_count
                progress_percentage = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
                
                # Add computed fields to the batch object
                batch.pending_tasks_count = pending_tasks_count
                batch.progress_percentage = progress_percentage
                
                available_batches.append(batch)
        
        # Limit to top 10 batches to avoid dropdown getting too long
        context["available_batches"] = available_batches[:10]
        
        # Get information about what the "Smart Next Task" would do
        next_task_info = _get_next_task_info(request.user, profile)
        context["next_task_info"] = next_task_info

        return render(request, "dashboard.html", context)
    else:
        return redirect("battycoda_app:landing")


def _get_next_task_info(user, profile):
    """Helper method to determine what the next task assignment would be"""
    # This mirrors the logic from views_task_navigation.py
    tasks_query = Task.objects.filter(is_done=False)
    
    # Filter by group or user
    if profile.group:
        tasks_query = tasks_query.filter(group=profile.group)
    else:
        tasks_query = tasks_query.filter(created_by=user)
    
    # Check if there are any tasks available
    if not tasks_query.exists():
        return {"message": "No tasks available"}
    
    # Try to find the most recently completed task to check its batch
    recent_tasks = Task.objects.filter(is_done=True)
    if profile.group:
        recent_tasks = recent_tasks.filter(group=profile.group)
    else:
        recent_tasks = recent_tasks.filter(created_by=user)
    
    recent_task = recent_tasks.order_by("-updated_at").first()
    
    # Check if we would continue from the same batch
    if recent_task and recent_task.batch:
        same_batch_tasks = tasks_query.filter(batch=recent_task.batch)
        if same_batch_tasks.exists():
            return {
                "message": f"Continue from '{recent_task.batch.name}' batch",
                "batch_name": recent_task.batch.name,
                "batch_id": recent_task.batch.id
            }
    
    # Otherwise, get the next task from oldest batch
    next_task = tasks_query.order_by("created_at").first()
    if next_task and next_task.batch:
        return {
            "message": f"Start '{next_task.batch.name}' batch",
            "batch_name": next_task.batch.name,
            "batch_id": next_task.batch.id
        }
    
    return {"message": "Next available task"}
