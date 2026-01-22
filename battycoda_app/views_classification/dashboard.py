"""Classification dashboard views."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import redirect, render

from battycoda_app.models import Project
from battycoda_app.models.classification import ClassificationRun, Classifier


@login_required
def classification_home_view(request):
    """Display a list of classification runs with a button to start a new one."""
    try:
        profile = request.user.profile

        from battycoda_app.models.classification import ClassifierTrainingJob

        if profile.group:
            if profile.is_current_group_admin:
                runs = ClassificationRun.objects.filter(group=profile.group).order_by("-created_at")
                classifiers = Classifier.objects.filter(
                    models.Q(group=profile.group) | models.Q(group__isnull=True)
                ).order_by("-created_at")
                training_jobs = ClassifierTrainingJob.objects.filter(group=profile.group).order_by("-created_at")
            else:
                runs = ClassificationRun.objects.filter(group=profile.group, created_by=request.user).order_by(
                    "-created_at"
                )
                classifiers = Classifier.objects.filter(
                    models.Q(group=profile.group, created_by=request.user) | models.Q(group__isnull=True)
                ).order_by("-created_at")
                training_jobs = ClassifierTrainingJob.objects.filter(
                    group=profile.group, created_by=request.user
                ).order_by("-created_at")
        else:
            runs = ClassificationRun.objects.filter(created_by=request.user).order_by("-created_at")
            classifiers = Classifier.objects.filter(
                models.Q(created_by=request.user) | models.Q(group__isnull=True)
            ).order_by("-created_at")
            training_jobs = ClassifierTrainingJob.objects.filter(created_by=request.user).order_by("-created_at")

        valid_runs = []
        for run in runs:
            try:
                _ = run.segmentation.recording.name
                valid_runs.append(run)
            except (AttributeError, Exception):
                continue

        project_id = request.GET.get("project")
        selected_project_id = None
        if project_id:
            try:
                project_id = int(project_id)
                valid_runs = [run for run in valid_runs if run.segmentation.recording.project_id == project_id]
                selected_project_id = project_id
            except (ValueError, TypeError):
                pass

        if profile.group:
            available_projects = Project.objects.filter(group=profile.group).order_by("name")
        else:
            available_projects = Project.objects.filter(created_by=request.user).order_by("name")

        context = {
            "runs": valid_runs,
            "classifiers": classifiers,
            "training_jobs": training_jobs,
            "available_projects": available_projects,
            "selected_project_id": selected_project_id,
        }

        return render(request, "classification/dashboard.html", context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return render(request, "classification/dashboard.html", {"runs": [], "classifiers": []})


@login_required
def classification_run_list_view(request):
    """Display list of all classification runs - redirects to main automation view."""
    return redirect("battycoda_app:classification_home")
