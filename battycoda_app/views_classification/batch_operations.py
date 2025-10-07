"""Batch classification operations views."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from battycoda_app.models import Segment
from battycoda_app.models.classification import Classifier, ClassificationRun
from battycoda_app.models.organization import Species


@login_required
def classify_unclassified_segments_view(request):
    """Display species with unclassified segments for batch classification."""
    profile = request.user.profile

    project_id = request.GET.get('project')
    project_filter = {}
    if project_id:
        try:
            project_id = int(project_id)
            project_filter['recordings__project_id'] = project_id
        except (ValueError, TypeError):
            project_id = None

    if profile.group:
        if profile.is_current_group_admin:
            species_list = Species.objects.filter(
                recordings__segments__isnull=False,
                recordings__group=profile.group,
                **project_filter
            ).distinct()
        else:
            species_list = Species.objects.filter(
                recordings__segments__isnull=False,
                recordings__created_by=request.user,
                **project_filter
            ).distinct()
    else:
        species_list = Species.objects.filter(
            recordings__segments__isnull=False,
            recordings__created_by=request.user,
            **project_filter
        ).distinct()

    items = []
    for species in species_list:
        if profile.group and profile.is_current_group_admin:
            segment_filter = {
                'recording__species': species,
                'recording__group': profile.group,
                'classification_results__isnull': True
            }
            if project_id:
                segment_filter['recording__project_id'] = project_id
            unclassified_count = Segment.objects.filter(**segment_filter).count()
        else:
            segment_filter = {
                'recording__species': species,
                'recording__created_by': request.user,
                'classification_results__isnull': True
            }
            if project_id:
                segment_filter['recording__project_id'] = project_id
            unclassified_count = Segment.objects.filter(**segment_filter).count()

        if unclassified_count > 0:
            action_url = reverse('battycoda_app:create_classification_for_species', args=[species.id])
            if project_id:
                action_url += f'?project={project_id}'

            items.append({
                'name': species.name,
                'type_name': 'Bat Species',
                'count': unclassified_count,
                'created_at': species.created_at,
                'detail_url': reverse('battycoda_app:species_detail', args=[species.id]),
                'action_url': action_url
            })

    context = {
        'title': 'Classify Unclassified Segments',
        'list_title': 'Species with Unclassified Segments',
        'parent_url': 'battycoda_app:classification_home',
        'parent_name': 'Classification',
        'th1': 'Species',
        'th2': 'Type',
        'th3': 'Unclassified Segments',
        'show_count': True,
        'action_text': 'Classify',
        'action_icon': 'tag',
        'empty_message': 'No species with unclassified segments found.',
        'items': items
    }

    return render(request, "classification/select_entity.html", context)


@login_required
def create_classification_for_species_view(request, species_id):
    """Create classification run for unclassified segments of a specific species."""
    species = get_object_or_404(Species, id=species_id)
    profile = request.user.profile

    project_id = request.GET.get('project')
    project_filter = {}
    if project_id:
        try:
            project_id = int(project_id)
            project_filter['recording__project_id'] = project_id
        except (ValueError, TypeError):
            project_id = None

    if profile.group and profile.is_current_group_admin:
        permission_filter = {
            'recording__species': species,
            'recording__group': profile.group,
            **project_filter
        }
        if not Segment.objects.filter(**permission_filter).exists():
            messages.error(request, "No segments for this species in your group" +
                         (f" and selected project" if project_id else "") + ".")
            redirect_url = 'battycoda_app:classify_unclassified_segments'
            if project_id:
                redirect_url += f'?project={project_id}'
            return redirect(redirect_url)
    else:
        permission_filter = {
            'recording__species': species,
            'recording__created_by': request.user,
            **project_filter
        }
        if not Segment.objects.filter(**permission_filter).exists():
            messages.error(request, "You don't have permission to classify segments for this species" +
                         (f" in the selected project" if project_id else "") + ".")
            redirect_url = 'battycoda_app:classify_unclassified_segments'
            if project_id:
                redirect_url += f'?project={project_id}'
            return redirect(redirect_url)

    if request.method == "POST":
        classifier_id = request.POST.get('classifier_id')
        run_name = request.POST.get('name') or f"Auto-classification for {species.name} - {timezone.now().strftime('%Y-%m-%d')}"

        if not classifier_id:
            messages.error(request, "Please select a classifier.")
            return redirect('battycoda_app:create_classification_for_species', species_id=species_id)

        classifier = get_object_or_404(Classifier, id=classifier_id)

        if classifier.species and classifier.species != species:
            messages.error(request, f"Selected classifier is trained for {classifier.species.name}, not {species.name}.")
            return redirect('battycoda_app:create_classification_for_species', species_id=species_id)

        if profile.group and profile.is_current_group_admin:
            segment_filter = {
                'recording__species': species,
                'recording__group': profile.group,
                'classification_results__isnull': True
            }
            if project_id:
                segment_filter['recording__project_id'] = project_id
            segments = Segment.objects.filter(**segment_filter)
        else:
            segment_filter = {
                'recording__species': species,
                'recording__created_by': request.user,
                'classification_results__isnull': True
            }
            if project_id:
                segment_filter['recording__project_id'] = project_id
            segments = Segment.objects.filter(**segment_filter)

        if not segments.exists():
            messages.error(request, "No unclassified segments found for this species" +
                         (f" in the selected project" if project_id else "") + ".")
            redirect_url = 'battycoda_app:classify_unclassified_segments'
            if project_id:
                redirect_url += f'?project={project_id}'
            return redirect(redirect_url)

        try:
            recording_segmentation_map = {}

            for segment in segments:
                key = (segment.recording.id, segment.segmentation.id)
                if key not in recording_segmentation_map:
                    recording_segmentation_map[key] = segment.segmentation

            run_count = 0
            for segmentation in recording_segmentation_map.values():
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

                from battycoda_app.audio.task_modules.queue_processor import queue_classification_run
                queue_classification_run.delay(run.id)
                run_count += 1

            messages.success(
                request,
                f"Created {run_count} classification runs for {segments.count()} segments across {run_count} recordings. "
                f"Runs have been queued and will be processed sequentially to prevent resource conflicts."
            )
            redirect_url = 'battycoda_app:classification_home'
            if project_id:
                redirect_url += f'?project={project_id}'
            return redirect(redirect_url)

        except Exception as e:
            messages.error(request, f"Error creating classification runs: {str(e)}")
            redirect_url = 'battycoda_app:classify_unclassified_segments'
            if project_id:
                redirect_url += f'?project={project_id}'
            return redirect(redirect_url)

    if profile.group:
        classifiers = (
            Classifier.objects.filter(is_active=True)
            .filter(models.Q(group=profile.group) | models.Q(group__isnull=True))
            .filter(models.Q(species=species) | models.Q(species__isnull=True))
            .order_by('name')
        )
    else:
        classifiers = (
            Classifier.objects.filter(is_active=True, group__isnull=True)
            .filter(models.Q(species=species) | models.Q(species__isnull=True))
            .order_by('name')
        )

    if profile.group and profile.is_current_group_admin:
        count_filter = {
            'recording__species': species,
            'recording__group': profile.group,
            'classification_results__isnull': True
        }
        if project_id:
            count_filter['recording__project_id'] = project_id
        unclassified_count = Segment.objects.filter(**count_filter).count()
    else:
        count_filter = {
            'recording__species': species,
            'recording__created_by': request.user,
            'classification_results__isnull': True
        }
        if project_id:
            count_filter['recording__project_id'] = project_id
        unclassified_count = Segment.objects.filter(**count_filter).count()

    context = {
        'species': species,
        'classifiers': classifiers,
        'unclassified_count': unclassified_count,
        'default_classifier': classifiers.filter(name="R-direct Classifier").first(),
    }

    return render(request, 'classification/create_species_classification.html', context)
