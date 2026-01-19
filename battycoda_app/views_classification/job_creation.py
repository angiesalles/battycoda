"""Views for creating classifier training jobs.

This module provides views for creating new classifier training jobs from task batches.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from battycoda_app.models.classification import Classifier, ClassifierTrainingJob
from battycoda_app.models.task import TaskBatch


@login_required
def classifier_list_view(request):
    """Redirect to classification dashboard with classifiers tab active."""
    from django.urls import reverse

    url = reverse("battycoda_app:classification_home")
    return redirect(f"{url}?tab=classifiers")


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
        if task_batch.created_by != request.user and (not profile.group or task_batch.group != profile.group):
            messages.error(request, "You don't have permission to create a classifier from this task batch.")
            return redirect("battycoda_app:task_batch_list")

        # Check if the batch has enough labeled tasks
        labeled_task_count = task_batch.tasks.filter(is_done=True, label__isnull=False).count()
        if labeled_task_count < 5:  # Arbitrary minimum for training
            messages.error(
                request,
                f"This batch only has {labeled_task_count} labeled tasks. At least 5 labeled tasks are required for training.",
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

            messages.success(request, "Classifier training job created successfully. Training will begin shortly.")
            return redirect("battycoda_app:classifier_training_job_detail", job_id=job.id)

        except Exception as e:
            messages.error(request, f"Error creating classifier training job: {str(e)}")
            return redirect("battycoda_app:task_batch_detail", batch_id=batch_id)

    # For GET requests, show the form
    if batch_id:
        task_batch = get_object_or_404(TaskBatch, id=batch_id)

        # Check if user has permission
        profile = request.user.profile
        if task_batch.created_by != request.user and (not profile.group or task_batch.group != profile.group):
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
            task_batches = TaskBatch.objects.filter(group=profile.group, created_by=request.user).order_by(
                "-created_at"
            )
    else:
        # Fallback to showing only user's task batches if no group is assigned
        task_batches = TaskBatch.objects.filter(created_by=request.user).order_by("-created_at")

    # Format data for the select_entity template
    items = []
    for batch in task_batches:
        labeled_count = batch.tasks.filter(is_done=True, label__isnull=False).count()
        total_count = batch.tasks.count()

        items.append(
            {
                "name": batch.name,
                "type_name": "Task Batch",
                "count": total_count,
                "labeled_count": labeled_count,  # Custom field for labeled tasks
                "created_at": batch.created_at,
                "detail_url": f"/tasks/batches/{batch.id}/",
                "action_url": f"/classification/classifiers/create/{batch.id}/",
                "disabled": labeled_count < 5,  # Disable if not enough labeled tasks
            }
        )

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
