"""Classification run creation and management views."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from battycoda_app.models import Segmentation
from battycoda_app.models.classification import CallProbability, ClassificationResult, ClassificationRun, Classifier


@login_required
def create_detection_run_view(request, segmentation_id=None):
    """Create a new classification run for a specific segmentation."""
    if request.method == "POST":
        segmentation_id = request.POST.get("segmentation_id") or segmentation_id
        name = request.POST.get("name")
        classifier_id = request.POST.get("classifier_id")

        if not segmentation_id:
            messages.error(request, "Segmentation ID is required")
            return redirect("battycoda_app:recording_list")

        segmentation = get_object_or_404(Segmentation, id=segmentation_id)

        profile = request.user.profile
        if segmentation.created_by != request.user and (
            not profile.group or segmentation.recording.group != profile.group
        ):
            messages.error(request, "You don't have permission to create a classification run for this segmentation.")
            return redirect("battycoda_app:recording_list")

        classifier = None
        if classifier_id:
            classifier = get_object_or_404(Classifier, id=classifier_id)
        else:
            try:
                classifier = Classifier.objects.get(name="R-direct Classifier")

            except Classifier.DoesNotExist:
                messages.error(request, "Default classifier not found. Please select a classifier.")
                return redirect("battycoda_app:create_detection_run", segmentation_id=segmentation_id)

        if classifier.species and segmentation.recording.species != classifier.species:
            error_message = (
                f"The selected classifier ({classifier.name}) is trained for {classifier.species.name}, "
                f"but the recording is for {segmentation.recording.species.name}. "
                f"Please select a classifier that matches the recording's species."
            )
            messages.error(request, error_message)
            return redirect("battycoda_app:create_detection_run", segmentation_id=segmentation_id)

        try:
            run = ClassificationRun.objects.create(
                name=name or f"Classification for {segmentation.recording.name}",
                segmentation=segmentation,
                created_by=request.user,
                group=profile.group,
                algorithm_type=classifier.response_format,
                classifier=classifier,
                status="queued",
                progress=0.0,
            )

            # Queue the run for processing by the queue processor
            from battycoda_app.audio.task_modules.queue_processor import queue_classification_run

            queue_classification_run.delay(run.id)

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True, "run_id": run.id})

            messages.success(request, "Classification run created successfully. Processing will begin shortly.")
            return redirect("battycoda_app:detection_run_detail", run_id=run.id)

        except Exception as e:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": str(e)})

            messages.error(request, f"Error creating classification run: {str(e)}")
            return redirect("battycoda_app:recording_detail", recording_id=segmentation.recording.id)

    if segmentation_id:
        segmentation = get_object_or_404(Segmentation, id=segmentation_id)

        profile = request.user.profile
        if segmentation.created_by != request.user and (
            not profile.group or segmentation.recording.group != profile.group
        ):
            messages.error(request, "You don't have permission to create a classification run for this segmentation.")
            return redirect("battycoda_app:recording_list")

        recording_species = segmentation.recording.species

        if profile.group:
            classifiers = (
                Classifier.objects.filter(is_active=True)
                .filter(models.Q(group=profile.group) | models.Q(group__isnull=True))
                .filter(models.Q(species=recording_species) | models.Q(species__isnull=True))
                .order_by("name")
            )
        else:
            classifiers = (
                Classifier.objects.filter(is_active=True, group__isnull=True)
                .filter(models.Q(species=recording_species) | models.Q(species__isnull=True))
                .order_by("name")
            )

        if not classifiers.exists():
            messages.error(
                request, f"No classifiers available for {recording_species.name}. Please contact an administrator."
            )
            return redirect("battycoda_app:recording_detail", recording_id=segmentation.recording.id)

        context = {
            "segmentation": segmentation,
            "classifiers": classifiers,
            "recording_species": recording_species,
            "default_classifier": classifiers.filter(name="R-direct Classifier").first(),
        }

        return render(request, "classification/create_run.html", context)

    profile = request.user.profile

    if profile.group:
        if profile.is_current_group_admin:
            segmentations = Segmentation.objects.filter(
                recording__group=profile.group, recording__hidden=False, status="completed"
            ).order_by("-created_at")
        else:
            segmentations = Segmentation.objects.filter(
                created_by=request.user, recording__hidden=False, status="completed"
            ).order_by("-created_at")
    else:
        segmentations = Segmentation.objects.filter(
            created_by=request.user, recording__hidden=False, status="completed"
        ).order_by("-created_at")

    items = []
    for segmentation in segmentations:
        items.append(
            {
                "name": f"Segmentation #{segmentation.id} - {segmentation.recording.name}",
                "type_name": "Segmentation Run",
                "count": segmentation.segments.count(),
                "created_at": segmentation.created_at,
                "detail_url": f"/recordings/{segmentation.recording.id}/segment/?segmentation_id={segmentation.id}",
                "action_url": f"/classification/runs/create/{segmentation.id}/",
            }
        )

    context = {
        "title": "Create Classification Run",
        "list_title": "Available Segmentation Runs",
        "action_text": "Create Run",
        "action_icon": "bolt",
        "parent_url": "battycoda_app:classification_home",
        "parent_name": "Classification",
        "th1": "Segmentation Run",
        "th2": "Type",
        "th3": "Segments",
        "show_count": True,
        "empty_message": "No segmentation runs available. You need to create segmentation runs first.",
        "create_url": "battycoda_app:batch_segmentation",
        "items": items,
    }

    return render(request, "classification/select_entity.html", context)


@login_required
def delete_detection_run_view(request, run_id):
    """Delete a classification run."""
    run = get_object_or_404(ClassificationRun, id=run_id)

    profile = request.user.profile
    if run.created_by != request.user and (not profile.group or run.group != profile.group):
        messages.error(request, "You don't have permission to delete this classification run.")
        return redirect("battycoda_app:classification_home")

    if request.method == "POST":
        CallProbability.objects.filter(classification_result__classification_run=run).delete()
        ClassificationResult.objects.filter(classification_run=run).delete()

        run_name = run.name

        run.delete()

        messages.success(request, f"Classification run '{run_name}' has been deleted.")
        return redirect("battycoda_app:classification_home")

    return render(request, "classification/delete_run.html", {"run": run})
