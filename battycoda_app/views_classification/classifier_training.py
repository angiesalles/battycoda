"""Views for training and managing classifiers.

This module provides views for creating, listing, and managing classifier training jobs.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from battycoda_app.models.classification import Classifier, ClassifierTrainingJob
from battycoda_app.models.task import TaskBatch


@login_required
def classifier_list_view(request):
    """Display a list of classifiers and training jobs."""
    try:
        profile = request.user.profile

        # Get all training jobs for user's groups
        if profile.group:
            if profile.is_current_group_admin:
                training_jobs = ClassifierTrainingJob.objects.filter(group=profile.group).order_by("-created_at")
                classifiers = Classifier.objects.filter(
                    models.Q(group=profile.group) | models.Q(group__isnull=True)
                ).order_by("-created_at")
            else:
                training_jobs = ClassifierTrainingJob.objects.filter(
                    group=profile.group, created_by=request.user
                ).order_by("-created_at")
                classifiers = Classifier.objects.filter(
                    models.Q(group=profile.group, created_by=request.user) | models.Q(group__isnull=True)
                ).order_by("-created_at")
        else:
            training_jobs = ClassifierTrainingJob.objects.filter(created_by=request.user).order_by("-created_at")
            classifiers = Classifier.objects.filter(
                models.Q(created_by=request.user) | models.Q(group__isnull=True)
            ).order_by("-created_at")

        context = {
            "training_jobs": training_jobs,
            "classifiers": classifiers,
        }

        return render(request, "classification/classifier_list.html", context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return render(request, "automation/classifier_list.html", {"training_jobs": [], "classifiers": []})


@login_required
def create_classifier_training_job_view(request, batch_id=None):
    """Create a new classifier training job from a task batch."""
    if request.method == "POST":
        batch_id = request.POST.get("batch_id") or batch_id
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        response_format = request.POST.get("response_format", "full_probability")
        algorithm_type = request.POST.get("algorithm_type", "knn")
        
        # Include algorithm_type in parameters
        parameters = {"algorithm_type": algorithm_type}
        
        if not batch_id:
            messages.error(request, "Task batch ID is required")
            return redirect("battycoda_app:task_batch_list")
            
        # Get the task batch
        task_batch = get_object_or_404(TaskBatch, id=batch_id)
        
        # Check if user has permission
        profile = request.user.profile
        if task_batch.created_by != request.user and (
            not profile.group or task_batch.group != profile.group
        ):
            messages.error(request, "You don't have permission to create a classifier from this task batch.")
            return redirect("battycoda_app:task_batch_list")
            
        # Check if the batch has enough labeled tasks
        labeled_task_count = task_batch.tasks.filter(is_done=True, label__isnull=False).count()
        if labeled_task_count < 5:  # Arbitrary minimum for training
            messages.error(
                request, 
                f"This batch only has {labeled_task_count} labeled tasks. At least 5 labeled tasks are required for training."
            )
            return redirect("battycoda_app:task_batch_detail", batch_id=batch_id)
            
        # Create the training job
        try:
            job = ClassifierTrainingJob.objects.create(
                name=name or f"Classifier training for {task_batch.name}",
                description=description,
                task_batch=task_batch,
                created_by=request.user,
                group=profile.group,
                response_format=response_format,
                parameters=parameters,
                status="pending",
                progress=0.0,
            )
            
            # Launch the training task
            from battycoda_app.audio.task_modules.training_tasks import train_classifier
            train_classifier.delay(job.id)
            
            messages.success(
                request, 
                "Classifier training job created successfully. Training will begin shortly."
            )
            return redirect("battycoda_app:classifier_training_job_detail", job_id=job.id)
            
        except Exception as e:
            messages.error(request, f"Error creating classifier training job: {str(e)}")
            return redirect("battycoda_app:task_batch_detail", batch_id=batch_id)
    
    # For GET requests, show the form
    if batch_id:
        task_batch = get_object_or_404(TaskBatch, id=batch_id)
        
        # Check if user has permission
        profile = request.user.profile
        if task_batch.created_by != request.user and (
            not profile.group or task_batch.group != profile.group
        ):
            messages.error(request, "You don't have permission to create a classifier from this task batch.")
            return redirect("battycoda_app:task_batch_list")
            
        # Check for labeled tasks
        labeled_tasks = task_batch.tasks.filter(is_done=True, label__isnull=False)
        labeled_task_count = labeled_tasks.count()
        
        context = {
            "task_batch": task_batch,
            "labeled_task_count": labeled_task_count,
            "response_format_choices": Classifier.RESPONSE_FORMAT_CHOICES,
        }
        
        return render(request, "classification/create_classifier.html", context)
        
    # If no batch_id provided, show list of available task batches
    profile = request.user.profile
    
    # Filter task batches by group if the user is in a group
    if profile.group:
        if profile.is_current_group_admin:
            # Admin sees all task batches in their group
            task_batches = TaskBatch.objects.filter(group=profile.group).order_by("-created_at")
        else:
            # Regular user only sees their own task batches
            task_batches = TaskBatch.objects.filter(group=profile.group, created_by=request.user).order_by("-created_at")
    else:
        # Fallback to showing only user's task batches if no group is assigned
        task_batches = TaskBatch.objects.filter(created_by=request.user).order_by("-created_at")
    
    # Format data for the select_entity template
    items = []
    for batch in task_batches:
        labeled_count = batch.tasks.filter(is_done=True, label__isnull=False).count()
        total_count = batch.tasks.count()
        
        items.append({
            "name": batch.name,
            "type_name": "Task Batch",
            "count": total_count,
            "labeled_count": labeled_count,  # Custom field for labeled tasks
            "created_at": batch.created_at,
            "detail_url": f"/tasks/batches/{batch.id}/",
            "action_url": f"/automation/classifiers/create/{batch.id}/",
            "disabled": labeled_count < 5,  # Disable if not enough labeled tasks
        })
    
    context = {
        "title": "Create Classifier",
        "list_title": "Available Task Batches",
        "action_text": "Create Classifier",
        "action_icon": "brain",
        "parent_url": "battycoda_app:classifier_list",
        "parent_name": "Classifiers",
        "th1": "Batch Name",
        "th2": "Species",
        "th3": "Labeled/Total Tasks",
        "show_count": True,
        "info_message": "Select a task batch to use for training a classifier. The task batch must have labeled tasks.",
        "empty_message": "No task batches available. You need to create and label task batches first.",
        "create_url": "battycoda_app:create_task_batch",
        "items": items,
    }
    
    return render(request, "classification/select_batch_for_classifier.html", context)


@login_required
def classifier_training_job_detail_view(request, job_id):
    """Display details about a classifier training job."""
    job = get_object_or_404(ClassifierTrainingJob, id=job_id)
    
    # Check if user has permission
    profile = request.user.profile
    if job.created_by != request.user and (not profile.group or job.group != profile.group):
        messages.error(request, "You don't have permission to view this classifier training job.")
        return redirect("battycoda_app:classifier_list")
    
    # Get labeled tasks from the batch
    labeled_tasks = job.task_batch.tasks.filter(is_done=True, label__isnull=False)
    
    # Get labels distribution
    label_counts = {}
    for task in labeled_tasks:
        if task.label not in label_counts:
            label_counts[task.label] = 0
        label_counts[task.label] += 1
    
    # Sort by count descending
    label_distribution = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)
    
    context = {
        "job": job,
        "task_batch": job.task_batch,
        "labeled_tasks": labeled_tasks,
        "label_distribution": label_distribution,
    }
    
    return render(request, "classification/classifier_job_detail.html", context)


@login_required
def classifier_training_job_status_view(request, job_id):
    """Return the current status of a classifier training job as JSON."""
    job = get_object_or_404(ClassifierTrainingJob, id=job_id)
    
    # Check if user has permission
    profile = request.user.profile
    if job.created_by != request.user and (not profile.group or job.group != profile.group):
        return JsonResponse({"success": False, "message": "Permission denied"})
    
    # Return basic status information for the job
    data = {
        "success": True,
        "status": job.status,
        "progress": job.progress,
        "error": job.error_message,
        "classifier_id": job.classifier.id if job.classifier else None,
    }
    
    return JsonResponse(data)


@login_required
def delete_classifier_training_job_view(request, job_id):
    """Delete a classifier training job."""
    job = get_object_or_404(ClassifierTrainingJob, id=job_id)
    
    # Check if user has permission
    profile = request.user.profile
    if job.created_by != request.user and (not profile.group or job.group != profile.group):
        messages.error(request, "You don't have permission to delete this classifier training job.")
        return redirect("battycoda_app:classifier_list")
    
    if request.method == "POST":
        # Check if we should also delete the resulting classifier
        delete_classifier = request.POST.get("delete_classifier") == "on"
        
        # Store classifier for potential deletion
        classifier = job.classifier
        
        # Store name for confirmation message
        job_name = job.name
        
        # Delete the job
        job.delete()
        
        # Also delete the classifier if requested and it exists
        if delete_classifier and classifier:
            classifier.delete()
            messages.success(
                request, 
                f"Classifier training job '{job_name}' and its associated classifier have been deleted."
            )
        else:
            messages.success(request, f"Classifier training job '{job_name}' has been deleted.")
            
        return redirect("battycoda_app:classifier_list")
    
    # For GET requests, show confirmation page
    return render(request, "classification/delete_classifier_job.html", {"job": job})