"""
Views for managing task batches - delete, bulk operations, etc.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models.task import Task, TaskBatch


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_task_batch_view(request, batch_id):
    """Delete a task batch and all its associated tasks"""
    batch = get_object_or_404(TaskBatch, id=batch_id)
    
    # Check permission - user must be the creator or group admin
    profile = request.user.profile
    if batch.created_by != request.user and (not profile.group or batch.group != profile.group or not profile.is_current_group_admin):
        messages.error(request, "You don't have permission to delete this batch.")
        return redirect("battycoda_app:task_batch_list")
    
    batch_name = batch.name
    task_count = Task.objects.filter(batch=batch).count()
    
    try:
        with transaction.atomic():
            # Delete all tasks in the batch first
            Task.objects.filter(batch=batch).delete()
            
            # Delete the batch itself
            batch.delete()
            
        messages.success(request, f"Successfully deleted batch '{batch_name}' and {task_count} associated tasks.")
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f"Batch '{batch_name}' deleted successfully."})
            
    except Exception as e:
        messages.error(request, f"Error deleting batch: {str(e)}")
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Preserve project filter when redirecting
    redirect_url = reverse("battycoda_app:task_batch_list")
    project_id = request.GET.get('project')
    if project_id:
        redirect_url += f"?project={project_id}"
    
    return redirect(redirect_url)