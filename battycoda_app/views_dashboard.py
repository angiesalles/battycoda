"""
Dashboard view for the BattyCoda application.
"""

from django.db import models
from django.shortcuts import redirect, render

from .models.classification import ClassificationRun
from .models.organization import Project, Species
from .models import Recording, Segmentation
from .models.task import Task, TaskBatch
from .models.user import GroupInvitation

# Set up logging

def index(request):
    """Root URL - show dashboard if logged in, or login page if not"""
    if request.user.is_authenticated:
        # Get user profile
        profile = request.user.profile

        # Initialize context dictionary
        context = {}
        
        # Check for pending invitations for this user
        if request.user.email:
            from django.utils import timezone
            pending_invitations = GroupInvitation.objects.filter(
                email=request.user.email,
                accepted=False,
                expires_at__gt=timezone.now()
            ).select_related('group', 'invited_by')
            context["pending_invitations"] = pending_invitations

        # Get pending tasks for this user to work on
        pending_tasks_query = Task.objects.filter(is_done=False)
        if profile.group:
            pending_tasks_query = pending_tasks_query.filter(group=profile.group)
        else:
            pending_tasks_query = pending_tasks_query.filter(created_by=request.user)
        
        pending_tasks = pending_tasks_query.select_related(
            'batch', 'species', 'project'
        ).order_by('created_at')[:10]
        context["pending_tasks"] = pending_tasks
        
        # Get recently completed tasks by this user
        recent_completed_tasks = Task.objects.filter(
            is_done=True,
            annotated_by=request.user
        ).select_related('batch', 'species', 'project').order_by('-annotated_at')[:5]
        context["recent_completed_tasks"] = recent_completed_tasks
        
        # Get task batches that need work
        task_batches_needing_work = []
        if profile.group:
            batches_query = TaskBatch.objects.filter(group=profile.group)
        else:
            batches_query = TaskBatch.objects.filter(created_by=request.user)
            
        for batch in batches_query.order_by("-created_at")[:10]:
            pending_count = batch.tasks.filter(is_done=False).count()
            if pending_count > 0:
                total_count = batch.tasks.count()
                progress = int((total_count - pending_count) / total_count * 100) if total_count > 0 else 0
                
                batch.pending_count = pending_count
                batch.total_count = total_count
                batch.progress = progress
                task_batches_needing_work.append(batch)
        
        context["task_batches_needing_work"] = task_batches_needing_work[:5]
        
        # Get user's work statistics
        context["my_pending_tasks"] = pending_tasks_query.count()
        context["my_completed_tasks"] = Task.objects.filter(annotated_by=request.user, is_done=True).count()
        context["my_total_annotations"] = Task.objects.filter(annotated_by=request.user).exclude(annotated_at__isnull=True).count()
        
        # Get recent activity from other users in the group (if user is in a group)
        if profile.group:
            recent_group_activity = Task.objects.filter(
                group=profile.group,
                is_done=True,
                annotated_at__isnull=False
            ).exclude(annotated_by=request.user).select_related(
                'annotated_by', 'batch', 'species'
            ).order_by('-annotated_at')[:5]
            context["recent_group_activity"] = recent_group_activity

        # Get available batches for task selection dropdown
        available_batches = []
        batches_query = TaskBatch.objects.select_related('species', 'project')
        
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
