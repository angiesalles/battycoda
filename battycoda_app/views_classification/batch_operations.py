"""Batch classification operations views."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from battycoda_app.audio.task_modules.queue_processor import queue_classification_run
from battycoda_app.models import Segment
from battycoda_app.models.classification import ClassificationRun, Classifier
from battycoda_app.models.organization import Species

logger = logging.getLogger(__name__)


def _get_segment_filter(profile, species=None, project_id=None, unclassified_only=False):
    """Build permission-aware segment filter dict.

    Args:
        profile: UserProfile instance
        species: Optional Species to filter by
        project_id: Optional project ID to filter by
        unclassified_only: If True, filter to segments without classification results

    Returns:
        Dict of filter kwargs for Segment.objects.filter()
    """
    segment_filter = {}

    if species:
        segment_filter["recording__species"] = species

    # Permission-based filtering
    if profile.group and profile.is_current_group_admin:
        segment_filter["recording__group"] = profile.group
    else:
        segment_filter["recording__created_by"] = profile.user

    if project_id:
        segment_filter["recording__project_id"] = project_id

    if unclassified_only:
        segment_filter["classification_results__isnull"] = True

    return segment_filter


def _get_species_filter(profile, project_id=None):
    """Build permission-aware species filter dict.

    Args:
        profile: UserProfile instance
        project_id: Optional project ID to filter by

    Returns:
        Dict of filter kwargs for Species.objects.filter()
    """
    species_filter = {"recordings__segments__isnull": False}

    if profile.group and profile.is_current_group_admin:
        species_filter["recordings__group"] = profile.group
    else:
        species_filter["recordings__created_by"] = profile.user

    if project_id:
        species_filter["recordings__project_id"] = project_id

    return species_filter


def _redirect_with_project(request: HttpRequest, url_name: str, project_id=None):
    """Redirect to URL, preserving project filter if present."""
    url = reverse(url_name)
    if project_id:
        url += f"?project={project_id}"
    return redirect(url)


def _parse_project_id(request: HttpRequest):
    """Parse and validate project_id from request GET params."""
    project_id = request.GET.get("project")
    if project_id:
        try:
            return int(project_id)
        except (ValueError, TypeError):
            pass
    return None


@login_required
def classify_unclassified_segments_view(request):
    """Display species with unclassified segments for batch classification."""
    profile = request.user.profile
    project_id = _parse_project_id(request)

    species_filter = _get_species_filter(profile, project_id)
    species_list = Species.objects.filter(**species_filter).distinct()

    items = []
    for species in species_list:
        segment_filter = _get_segment_filter(profile, species, project_id, unclassified_only=True)
        unclassified_count = Segment.objects.filter(**segment_filter).count()

        if unclassified_count > 0:
            action_url = reverse("battycoda_app:create_classification_for_species", args=[species.id])
            if project_id:
                action_url += f"?project={project_id}"

            items.append(
                {
                    "name": species.name,
                    "type_name": "Bat Species",
                    "count": unclassified_count,
                    "created_at": species.created_at,
                    "detail_url": reverse("battycoda_app:species_detail", args=[species.id]),
                    "action_url": action_url,
                }
            )

    context = {
        "title": "Classify Unclassified Segments",
        "list_title": "Species with Unclassified Segments",
        "parent_url": "battycoda_app:classification_home",
        "parent_name": "Classification",
        "th1": "Species",
        "th2": "Type",
        "th3": "Unclassified Segments",
        "show_count": True,
        "action_text": "Classify",
        "action_icon": "tag",
        "empty_message": "No species with unclassified segments found.",
        "items": items,
    }

    return render(request, "classification/select_entity.html", context)


@login_required
def create_classification_for_species_view(request, species_id):
    """Create classification run for unclassified segments of a specific species."""
    species = get_object_or_404(Species, id=species_id)
    profile = request.user.profile
    project_id = _parse_project_id(request)

    # Check user has permission to access segments for this species
    permission_filter = _get_segment_filter(profile, species, project_id)
    if not Segment.objects.filter(**permission_filter).exists():
        is_admin = profile.group and profile.is_current_group_admin
        msg = (
            "No segments for this species in your group"
            if is_admin
            else "You don't have permission to classify segments for this species"
        )
        if project_id:
            msg += " in the selected project"
        messages.error(request, msg + ".")
        return _redirect_with_project(request, "battycoda_app:classify_unclassified_segments", project_id)

    if request.method == "POST":
        classifier_id = request.POST.get("classifier_id")
        run_name = (
            request.POST.get("name")
            or f"Auto-classification for {species.name} - {timezone.now().strftime('%Y-%m-%d')}"
        )

        if not classifier_id:
            messages.error(request, "Please select a classifier.")
            return redirect("battycoda_app:create_classification_for_species", species_id=species_id)

        classifier = get_object_or_404(Classifier, id=classifier_id)

        if classifier.species and classifier.species != species:
            messages.error(
                request, f"Selected classifier is trained for {classifier.species.name}, not {species.name}."
            )
            return redirect("battycoda_app:create_classification_for_species", species_id=species_id)

        segment_filter = _get_segment_filter(profile, species, project_id, unclassified_only=True)
        segments = Segment.objects.filter(**segment_filter)

        if not segments.exists():
            msg = "No unclassified segments found for this species"
            if project_id:
                msg += " in the selected project"
            messages.error(request, msg + ".")
            return _redirect_with_project(request, "battycoda_app:classify_unclassified_segments", project_id)

        # Group segments by recording+segmentation to create one run per segmentation
        recording_segmentation_map = {}
        for segment in segments:
            key = (segment.recording.id, segment.segmentation.id)
            if key not in recording_segmentation_map:
                recording_segmentation_map[key] = segment.segmentation

        run_count = 0
        for segmentation in recording_segmentation_map.values():
            try:
                run = ClassificationRun.objects.create(
                    name=f"{run_name} - {segmentation.recording.name}",
                    segmentation=segmentation,
                    created_by=request.user,
                    group=profile.group,
                    algorithm_type=classifier.response_format,
                    classifier=classifier,
                    status="queued",
                    progress=0.0,
                )
                queue_classification_run.delay(run.id)
                run_count += 1
            except Exception:
                logger.exception(
                    "Failed to create classification run for segmentation %s (recording: %s)",
                    segmentation.id,
                    segmentation.recording.name,
                )
                # Continue with other segmentations rather than failing entirely

        if run_count == 0:
            messages.error(request, "Failed to create any classification runs. Check logs for details.")
            return _redirect_with_project(request, "battycoda_app:classify_unclassified_segments", project_id)

        messages.success(
            request,
            f"Created {run_count} classification runs for {segments.count()} segments across {run_count} recordings. "
            f"Runs have been queued and will be processed sequentially to prevent resource conflicts.",
        )
        return _redirect_with_project(request, "battycoda_app:classification_home", project_id)

    # GET request: show classifier selection form
    if profile.group:
        classifiers = (
            Classifier.objects.filter(is_active=True)
            .filter(models.Q(group=profile.group) | models.Q(group__isnull=True))
            .filter(models.Q(species=species) | models.Q(species__isnull=True))
            .order_by("name")
        )
    else:
        classifiers = (
            Classifier.objects.filter(is_active=True, group__isnull=True)
            .filter(models.Q(species=species) | models.Q(species__isnull=True))
            .order_by("name")
        )

    segment_filter = _get_segment_filter(profile, species, project_id, unclassified_only=True)
    unclassified_count = Segment.objects.filter(**segment_filter).count()

    context = {
        "species": species,
        "classifiers": classifiers,
        "unclassified_count": unclassified_count,
        "default_classifier": classifiers.filter(name="R-direct Classifier").first(),
    }

    return render(request, "classification/create_species_classification.html", context)
