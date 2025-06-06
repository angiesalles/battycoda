import pickle
import traceback
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

import numpy as np

from .audio.utils import process_pickle_file
from .forms import TaskBatchForm
from .models.recording import Recording, Segment
from .models.task import Task, TaskBatch
from .models.user import UserProfile
from .utils_modules.task_export_utils import generate_tasks_csv

# Set up logging

@login_required
def task_batch_list_view(request):
    """Display list of all task batches with pagination"""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    # Get user profile
    profile = request.user.profile

    # Filter batches by group if the user is in a group
    if profile.group:
        if profile.is_current_group_admin:
            # Admin sees all batches in their group
            batches_list = TaskBatch.objects.filter(group=profile.group).order_by("-created_at")
        else:
            # Regular user only sees their own batches
            batches_list = TaskBatch.objects.filter(created_by=request.user).order_by("-created_at")
    else:
        # Fallback to showing only user's batches if no group is assigned
        batches_list = TaskBatch.objects.filter(created_by=request.user).order_by("-created_at")
    
    # Set up pagination - 20 batches per page
    paginator = Paginator(batches_list, 20)
    page = request.GET.get('page')
    
    try:
        # Get the requested page
        batches = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        batches = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        batches = paginator.page(paginator.num_pages)

    context = {
        "batches": batches,
        "total_count": batches_list.count(),
    }

    return render(request, "tasks/batch_list.html", context)

@login_required
def task_batch_detail_view(request, batch_id):
    """Display details of a specific task batch"""
    # Get the batch by ID
    batch = get_object_or_404(TaskBatch, id=batch_id)

    # Check if the user has permission to view this batch
    # Either they created it or they're in the same group
    profile = request.user.profile
    if batch.created_by != request.user and (not profile.group or batch.group != profile.group):
        messages.error(request, "You don't have permission to view this batch.")
        return redirect("battycoda_app:task_batch_list")

    # Get tasks with ascending ID order
    tasks = Task.objects.filter(batch=batch).order_by("id")  # Ordering by ID in ascending order

    context = {
        "batch": batch,
        "tasks": tasks,
    }

    return render(request, "tasks/batch_detail.html", context)

@login_required
def export_task_batch_view(request, batch_id):
    """Export task batch results to CSV"""
    # Get the batch by ID
    batch = get_object_or_404(TaskBatch, id=batch_id)

    # Check if the user has permission to export this batch
    # Either they created it or they're in the same group
    profile = request.user.profile
    if batch.created_by != request.user and (not profile.group or batch.group != profile.group):
        messages.error(request, "You don't have permission to export this batch.")
        return redirect("battycoda_app:task_batch_list")

    # Get tasks with ascending ID order
    tasks = Task.objects.filter(batch=batch).order_by("id")

    # Generate CSV content using the utility function
    csv_content = generate_tasks_csv(tasks)

    # Create HTTP response
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"taskbatch_{batch.id}_{batch.name.replace(' ', '_')}_{timestamp}.csv"
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write(csv_content)

    return response

@login_required
def create_task_batch_view(request):
    """Direct creation of task batches now disabled - redirect to explanation"""
    # Create an informational message
    messages.info(
        request,
        "Task batches can now only be created from classification results. "
        "Please create a recording, segment it, run classification, and then create a task batch "
        "from the classification results for manual review.",
    )

    # Redirect to the task batch list
    return redirect("battycoda_app:task_batch_list")

@login_required
def check_taskbatch_name(request):
    """Check if a TaskBatch name already exists in the user's group."""
    if request.method == "GET":
        name = request.GET.get("name", "")
        group = request.user.profile.group
        
        if not name or not group:
            return JsonResponse({"exists": False})
        
        # Check if the name exists in the user's group
        exists = TaskBatch.objects.filter(name=name, group=group).exists()
        
        return JsonResponse({"exists": exists})
    
    return JsonResponse({"error": "Invalid request method"}, status=400)
