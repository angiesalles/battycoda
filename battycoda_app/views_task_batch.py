import hashlib
import os
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models.organization import Project
from .models.task import Task, TaskBatch
from .utils_modules.task_export_utils import generate_tasks_csv


def user_can_access_batch(user, batch):
    """Check if user has permission to access a task batch.

    Returns True if user created the batch OR user is in the same group.
    """
    if batch.created_by == user:
        return True
    profile = user.profile
    return profile.group and batch.group == profile.group


@login_required
def task_batch_list_view(request):
    """Display list of all task batches with pagination and project filtering"""
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

    # Apply project filter if provided
    project_id = request.GET.get("project")
    if project_id:
        try:
            project_id = int(project_id)
            batches_list = batches_list.filter(project_id=project_id)
        except (ValueError, TypeError):
            pass  # Invalid project ID, ignore filter

    # Get available projects for the filter dropdown
    if profile.group:
        available_projects = Project.objects.filter(group=profile.group).order_by("name")
    else:
        available_projects = Project.objects.filter(created_by=request.user).order_by("name")

    # Set up pagination - 20 batches per page
    paginator = Paginator(batches_list, 20)
    page = request.GET.get("page")

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
        "available_projects": available_projects,
        "selected_project_id": int(project_id) if project_id else None,
    }

    return render(request, "tasks/batch_list.html", context)


@login_required
def task_batch_detail_view(request, batch_id):
    """Display details of a specific task batch"""
    # Get the batch by ID
    batch = get_object_or_404(TaskBatch, id=batch_id)

    if not user_can_access_batch(request.user, batch):
        messages.error(request, "You don't have permission to view this batch.")
        return redirect("battycoda_app:task_batch_list")

    tasks = Task.objects.filter(batch=batch).order_by("id")

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

    if not user_can_access_batch(request.user, batch):
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


@login_required
def task_batch_review_view(request, batch_id):
    """Interface for reviewing and relabeling tasks in a batch by call type"""
    # Get the batch by ID
    batch = get_object_or_404(TaskBatch, id=batch_id)

    if not user_can_access_batch(request.user, batch):
        messages.error(request, "You don't have permission to view this batch.")
        return redirect("battycoda_app:task_batch_list")

    # Get selected call type from query parameter
    selected_call_type = request.GET.get("call_type", "all")

    # Get all tasks in the batch
    tasks = Task.objects.filter(batch=batch).order_by("id")

    # Filter tasks by call type if specified
    if selected_call_type != "all":
        # Show tasks that have this label (annotated) or classification_result (unannotated)
        tasks = tasks.filter(
            models.Q(label=selected_call_type)
            | models.Q(label__isnull=True, classification_result=selected_call_type)
            | models.Q(label="", classification_result=selected_call_type)
        )

    # Get all available call types from the species
    species = batch.species
    available_call_types = ["all"]  # Start with 'all' option

    # Add call types from species
    if species:
        call_types_from_species = list(species.calls.values_list("short_name", flat=True))
        available_call_types.extend(call_types_from_species)

    # Add any additional call types found in the tasks (efficient query for just these columns)
    task_call_types = set()
    for label, classification_result in batch.tasks.values_list("label", "classification_result"):
        if label:
            task_call_types.add(label)
        if classification_result:
            task_call_types.add(classification_result)

    # Add any call types not already in the list
    for call_type in task_call_types:
        if call_type not in available_call_types:
            available_call_types.append(call_type)

    # Remove None values and sort
    available_call_types = [ct for ct in available_call_types if ct]
    available_call_types.sort()

    # Get spectrogram URLs for each task
    tasks_with_spectrograms = []
    for task in tasks:
        # Get file path
        if task.batch and task.batch.wav_file:
            full_path = task.batch.wav_file.path
            os_path = full_path
        else:
            full_path = os.path.join(
                "home", request.user.username, task.species.name, task.project.name, task.wav_file_name
            )
            os_path = full_path

        # Create hash
        file_hash = hashlib.md5(os_path.encode()).hexdigest()

        # Create spectrogram URL for channel 0, detailed view
        spectrogram_url = f"/spectrogram/?wav_path={full_path}&call=0&channel=0&numcalls=1&hash={file_hash}&overview=0&contrast=4.0&onset={task.onset}&offset={task.offset}"

        # Get the display label (what the user sees in the UI)
        display_label = task.label if task.label else task.classification_result

        tasks_with_spectrograms.append(
            {
                "task": task,
                "spectrogram_url": spectrogram_url,
                "display_label": display_label,
                "confidence": task.confidence,
                "annotation_url": reverse("battycoda_app:annotate_task", args=[task.id]),
            }
        )

    context = {
        "batch": batch,
        "tasks_with_spectrograms": tasks_with_spectrograms,
        "available_call_types": available_call_types,
        "selected_call_type": selected_call_type,
        "species": species,
        "all_call_types_for_dropdown": available_call_types[1:],  # Exclude 'all' for relabeling dropdown
    }

    return render(request, "tasks/batch_review.html", context)


@login_required
def relabel_task_ajax(request):
    """AJAX endpoint for relabeling a task"""
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        new_label = request.POST.get("new_label")

        if not task_id or not new_label:
            return JsonResponse({"success": False, "error": "Missing task_id or new_label"})

        try:
            task = get_object_or_404(Task, id=task_id)

            if not user_can_access_batch(request.user, task.batch):
                return JsonResponse({"success": False, "error": "Permission denied"})

            # Update the task
            task.label = new_label
            task.annotated_by = request.user
            task.annotated_at = timezone.now()
            task.is_done = True
            task.status = "done"
            task.save()

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})
