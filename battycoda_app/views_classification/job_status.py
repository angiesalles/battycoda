"""Views for classifier training job status, details, and management.

This module provides views for viewing, monitoring, and managing classifier training jobs.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from battycoda_app.models.classification import ClassifierTrainingJob


@login_required
def classifier_training_job_detail_view(request, job_id):
    """Display details about a classifier training job."""
    job = get_object_or_404(ClassifierTrainingJob, id=job_id)

    # Check if user has permission
    profile = request.user.profile
    if job.created_by != request.user and (not profile.group or job.group != profile.group):
        messages.error(request, "You don't have permission to view this classifier training job.")
        return redirect("battycoda_app:classifier_list")

    # Get labeled tasks from the batch (if training from batch)
    labeled_tasks = None
    label_distribution = []

    if job.task_batch:
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
                request, f"Classifier training job '{job_name}' and its associated classifier have been deleted."
            )
        else:
            messages.success(request, f"Classifier training job '{job_name}' has been deleted.")

        return redirect("battycoda_app:classifier_list")

    # For GET requests, show confirmation page
    return render(request, "classification/delete_classifier_job.html", {"job": job})
