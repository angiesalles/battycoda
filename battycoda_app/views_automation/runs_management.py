"""Management views for detection runs.

Provides views for creating, listing, and managing detection runs.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from battycoda_app.models.classification import CallProbability, Classifier, ClassificationResult, ClassificationRun
from battycoda_app.models.recording import Segmentation, Segment
from battycoda_app.models.organization import Project, Species

@login_required
def automation_home_view(request):
    """Display a list of classification runs with a button to start a new one."""
    try:
        profile = request.user.profile
        
        # Import classifier training job model
        from battycoda_app.models.classification import ClassifierTrainingJob

        # Get all detection runs, classifiers, and training jobs for user's groups
        if profile.group:
            if profile.is_current_group_admin:
                # Admin can see all group items
                runs = ClassificationRun.objects.filter(group=profile.group).order_by("-created_at")
                classifiers = Classifier.objects.filter(
                    models.Q(group=profile.group) | models.Q(group__isnull=True)
                ).order_by("-created_at")
                training_jobs = ClassifierTrainingJob.objects.filter(group=profile.group).order_by("-created_at")
            else:
                # Regular users see only their own items plus global items
                runs = ClassificationRun.objects.filter(group=profile.group, created_by=request.user).order_by("-created_at")
                classifiers = Classifier.objects.filter(
                    models.Q(group=profile.group, created_by=request.user) | models.Q(group__isnull=True)
                ).order_by("-created_at")
                training_jobs = ClassifierTrainingJob.objects.filter(
                    group=profile.group, created_by=request.user
                ).order_by("-created_at")
        else:
            # No group - only see personal items plus global items
            runs = ClassificationRun.objects.filter(created_by=request.user).order_by("-created_at")
            classifiers = Classifier.objects.filter(
                models.Q(created_by=request.user) | models.Q(group__isnull=True)
            ).order_by("-created_at")
            training_jobs = ClassifierTrainingJob.objects.filter(created_by=request.user).order_by("-created_at")

        # Filter out runs that might have problematic data due to the migration
        valid_runs = []
        for run in runs:
            try:
                # Test if we can access required properties without errors
                _ = run.segmentation.recording.name
                valid_runs.append(run)
            except (AttributeError, Exception):
                # Skip this run if it causes errors
                continue

        # Apply project filter if provided
        project_id = request.GET.get('project')
        selected_project_id = None
        if project_id:
            try:
                project_id = int(project_id)
                valid_runs = [run for run in valid_runs if run.segmentation.recording.project_id == project_id]
                selected_project_id = project_id
            except (ValueError, TypeError):
                pass

        # Get available projects for the filter dropdown
        if profile.group:
            available_projects = Project.objects.filter(group=profile.group).order_by('name')
        else:
            available_projects = Project.objects.filter(created_by=request.user).order_by('name')
            
        context = {
            "runs": valid_runs,
            "classifiers": classifiers,
            "training_jobs": training_jobs,
            "available_projects": available_projects,
            "selected_project_id": selected_project_id,
        }

        return render(request, "automation/dashboard.html", context)
    except Exception as e:

        messages.error(request, f"An error occurred: {str(e)}")
        # Provide a fallback response
        return render(request, "automation/dashboard.html", {"runs": [], "classifiers": []})

@login_required
def detection_run_list_view(request):
    """Display list of all detection runs - redirects to main automation view."""
    # We've combined this view with the main automation view
    return redirect("battycoda_app:automation_home")

@login_required
def create_detection_run_view(request, segmentation_id=None):
    """Create a new classification run for a specific segmentation."""
    if request.method == "POST":
        segmentation_id = request.POST.get("segmentation_id") or segmentation_id
        name = request.POST.get("name")
        # Note: algorithm_type is not used here as classifier.response_format is used instead
        classifier_id = request.POST.get("classifier_id")

        if not segmentation_id:
            messages.error(request, "Segmentation ID is required")
            return redirect("battycoda_app:recording_list")

        # Get the segmentation
        segmentation = get_object_or_404(Segmentation, id=segmentation_id)

        # Check if user has permission
        profile = request.user.profile
        if segmentation.created_by != request.user and (
            not profile.group or segmentation.recording.group != profile.group
        ):
            messages.error(request, "You don't have permission to create a classification run for this segmentation.")
            return redirect("battycoda_app:recording_list")

        # Get the classifier
        classifier = None
        if classifier_id:
            classifier = get_object_or_404(Classifier, id=classifier_id)
        else:
            # Try to get the default R-direct classifier
            try:
                classifier = Classifier.objects.get(name="R-direct Classifier")

            except Classifier.DoesNotExist:
                messages.error(request, "Default classifier not found. Please select a classifier.")
                return redirect("battycoda_app:create_detection_run", segmentation_id=segmentation_id)
                
        # Check if classifier species matches the recording species
        if classifier.species and segmentation.recording.species != classifier.species:
            error_message = (
                f"The selected classifier ({classifier.name}) is trained for {classifier.species.name}, "
                f"but the recording is for {segmentation.recording.species.name}. "
                f"Please select a classifier that matches the recording's species."
            )
            messages.error(request, error_message)
            return redirect("battycoda_app:create_detection_run", segmentation_id=segmentation_id)

        # Create the detection run
        try:
            run = ClassificationRun.objects.create(
                name=name or f"Classification for {segmentation.recording.name}",
                segmentation=segmentation,
                created_by=request.user,
                group=profile.group,
                algorithm_type=classifier.response_format,  # Use the classifier's response format
                classifier=classifier,
                status="pending",
                progress=0.0,
            )

            # Launch the appropriate Celery task based on the classifier
            if classifier.name == "Dummy Classifier":
                # Use the dummy classifier task directly
                from battycoda_app.audio.task_modules.classification_tasks import run_dummy_classifier

                run_dummy_classifier.delay(run.id)
            else:
                # For other classifiers, use the standard task
                from battycoda_app.audio.task_modules.classification_tasks import run_call_detection

                run_call_detection.delay(run.id)

            # If AJAX request
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True, "run_id": run.id})

            messages.success(request, "Classification run created successfully. Processing will begin shortly.")
            return redirect("battycoda_app:detection_run_detail", run_id=run.id)

        except Exception as e:

            # If AJAX request
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": str(e)})

            messages.error(request, f"Error creating classification run: {str(e)}")
            return redirect("battycoda_app:recording_detail", recording_id=segmentation.recording.id)

    # For GET requests, show the form
    if segmentation_id:
        segmentation = get_object_or_404(Segmentation, id=segmentation_id)

        # Check if user has permission
        profile = request.user.profile
        if segmentation.created_by != request.user and (
            not profile.group or segmentation.recording.group != profile.group
        ):
            messages.error(request, "You don't have permission to create a classification run for this segmentation.")
            return redirect("battycoda_app:recording_list")

        # Get recording species
        recording_species = segmentation.recording.species
        
        # Get all classifiers first (for debugging)
        all_classifiers = Classifier.objects.filter(is_active=True)
        
        # Log all classifiers and their species
        print(f"DEBUG: All classifiers: {len(all_classifiers)}")
        for c in all_classifiers:
            print(f"DEBUG: Classifier: {c.name}, Species: {c.species.name if c.species else 'None'}")
        
        print(f"DEBUG: Recording species: {recording_species.name}")
            
        # Get available classifiers (group's classifiers and global classifiers)
        # Filter by matching species or null species (like dummy classifier)
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
            
        # Log filtered classifiers
        print(f"DEBUG: Filtered classifiers: {len(classifiers)}")
        for c in classifiers:
            print(f"DEBUG: Filtered classifier: {c.name}, Species: {c.species.name if c.species else 'None'}")

        # If no classifiers are available, show a message and redirect
        if not classifiers.exists():
            messages.error(
                request, 
                f"No classifiers available for {recording_species.name}. Please contact an administrator."
            )
            return redirect("battycoda_app:recording_detail", recording_id=segmentation.recording.id)

        context = {
            "segmentation": segmentation,
            "classifiers": classifiers,
            "recording_species": recording_species,
            "default_classifier": classifiers.filter(name="R-direct Classifier").first(),
        }

        return render(request, "automation/create_run.html", context)

    # If no segmentation_id provided, show list of available segmentations
    profile = request.user.profile

    # Filter segmentations by group if the user is in a group
    if profile.group:
        if profile.is_current_group_admin:
            # Admin sees all segmentations in their group
            segmentations = Segmentation.objects.filter(recording__group=profile.group, status="completed").order_by(
                "-created_at"
            )
        else:
            # Regular user only sees their own segmentations
            segmentations = Segmentation.objects.filter(created_by=request.user, status="completed").order_by(
                "-created_at"
            )
    else:
        # Fallback to showing only user's segmentations if no group is assigned
        segmentations = Segmentation.objects.filter(created_by=request.user, status="completed").order_by("-created_at")

    # Format data for the select_entity template
    items = []
    for segmentation in segmentations:
        items.append({
            "name": f"Segmentation #{segmentation.id} - {segmentation.recording.name}",
            "type_name": "Segmentation Run",
            "count": segmentation.segments.count(),
            "created_at": segmentation.created_at,
            "detail_url": f"/recordings/{segmentation.recording.id}/segment/?segmentation_id={segmentation.id}",
            "action_url": f"/automation/runs/create/{segmentation.id}/",
        })

    context = {
        "title": "Create Classification Run",
        "list_title": "Available Segmentation Runs",
        "action_text": "Create Run",
        "action_icon": "bolt",
        "parent_url": "battycoda_app:automation_home",
        "parent_name": "Automation",
        "th1": "Segmentation Run",
        "th2": "Type",
        "th3": "Segments",
        "show_count": True,
        "empty_message": "No segmentation runs available. You need to create segmentation runs first.",
        "create_url": "battycoda_app:batch_segmentation",
        "items": items,
    }

    return render(request, "automation/select_entity.html", context)

@login_required
def delete_detection_run_view(request, run_id):
    """Delete a classification run."""
    # Get the detection run by ID
    run = get_object_or_404(ClassificationRun, id=run_id)

    # Check if the user has permission
    profile = request.user.profile
    if run.created_by != request.user and (not profile.group or run.group != profile.group):
        messages.error(request, "You don't have permission to delete this classification run.")
        return redirect("battycoda_app:automation_home")

    if request.method == "POST":
        # Delete all related results first
        CallProbability.objects.filter(detection_result__classification_run=run).delete()
        ClassificationResult.objects.filter(classification_run=run).delete()

        # Store name for confirmation message
        run_name = run.name

        # Now delete the run itself
        run.delete()

        messages.success(request, f"Classification run '{run_name}' has been deleted.")
        return redirect("battycoda_app:automation_home")

    # For GET requests, show confirmation page
    return render(request, "automation/delete_run.html", {"run": run})


@login_required
def classify_unclassified_segments_view(request):
    """Display species with unclassified segments for batch classification."""
    profile = request.user.profile
    
    # Apply project filter if provided
    project_id = request.GET.get('project')
    project_filter = {}
    if project_id:
        try:
            project_id = int(project_id)
            project_filter['recordings__project_id'] = project_id
        except (ValueError, TypeError):
            project_id = None
    
    # Get all species with segments that don't have detection results
    if profile.group:
        if profile.is_current_group_admin:
            # Admin sees all species in their group
            species_list = Species.objects.filter(
                recordings__segments__isnull=False,
                recordings__group=profile.group,
                **project_filter
            ).distinct()
        else:
            # Regular user sees only species for their own recordings
            species_list = Species.objects.filter(
                recordings__segments__isnull=False,
                recordings__created_by=request.user,
                **project_filter
            ).distinct()
    else:
        # User with no group sees only their own species
        species_list = Species.objects.filter(
            recordings__segments__isnull=False,
            recordings__created_by=request.user,
            **project_filter
        ).distinct()
    
    items = []
    for species in species_list:
        if profile.group and profile.is_current_group_admin:
            # Count unclassified segments for this species within the group (and project if filtered)
            segment_filter = {
                'recording__species': species,
                'recording__group': profile.group,
                'detection_results__isnull': True
            }
            if project_id:
                segment_filter['recording__project_id'] = project_id
            unclassified_count = Segment.objects.filter(**segment_filter).count()
        else:
            # Count unclassified segments for this species created by the user (and project if filtered)
            segment_filter = {
                'recording__species': species,
                'recording__created_by': request.user,
                'detection_results__isnull': True
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
        'parent_url': 'battycoda_app:automation_home',
        'parent_name': 'Automation',
        'th1': 'Species',
        'th2': 'Type',
        'th3': 'Unclassified Segments',
        'show_count': True,
        'action_text': 'Classify',
        'action_icon': 'tag',
        'empty_message': 'No species with unclassified segments found.',
        'items': items
    }
    
    return render(request, "automation/select_entity.html", context)


@login_required
def create_classification_for_species_view(request, species_id):
    """Create classification run for unclassified segments of a specific species."""
    species = get_object_or_404(Species, id=species_id)
    profile = request.user.profile
    
    # Apply project filter if provided
    project_id = request.GET.get('project')
    project_filter = {}
    if project_id:
        try:
            project_id = int(project_id)
            project_filter['recording__project_id'] = project_id
        except (ValueError, TypeError):
            project_id = None
    
    # Check permissions
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
    
    # For POST request, create the classification run
    if request.method == "POST":
        classifier_id = request.POST.get('classifier_id')
        run_name = request.POST.get('name') or f"Auto-classification for {species.name} - {timezone.now().strftime('%Y-%m-%d')}"
        
        if not classifier_id:
            messages.error(request, "Please select a classifier.")
            return redirect('battycoda_app:create_classification_for_species', species_id=species_id)
            
        classifier = get_object_or_404(Classifier, id=classifier_id)
        
        # Check if classifier is compatible with species
        if classifier.species and classifier.species != species:
            messages.error(request, f"Selected classifier is trained for {classifier.species.name}, not {species.name}.")
            return redirect('battycoda_app:create_classification_for_species', species_id=species_id)

        # Get unclassified segments
        if profile.group and profile.is_current_group_admin:
            segment_filter = {
                'recording__species': species,
                'recording__group': profile.group,
                'detection_results__isnull': True
            }
            if project_id:
                segment_filter['recording__project_id'] = project_id
            segments = Segment.objects.filter(**segment_filter)
        else:
            segment_filter = {
                'recording__species': species,
                'recording__created_by': request.user,
                'detection_results__isnull': True
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
            # Group segments by recording/segmentation to create detection runs
            recording_segmentation_map = {}
            
            # Identify the segmentations we need to process
            for segment in segments:
                key = (segment.recording.id, segment.segmentation.id)
                if key not in recording_segmentation_map:
                    recording_segmentation_map[key] = segment.segmentation
            
            # Create a detection run for each segmentation
            run_count = 0
            for segmentation in recording_segmentation_map.values():
                # Create the detection run with "queued" status
                run = ClassificationRun.objects.create(
                    name=f"{run_name} - {segmentation.recording.name}",
                    segmentation=segmentation,
                    created_by=request.user,
                    group=profile.group,
                    algorithm_type=classifier.response_format,
                    classifier=classifier,
                    status="queued",  # Start in queued status
                    progress=0.0,
                )
                
                # Queue the run for processing instead of launching immediately
                from battycoda_app.audio.task_modules.queue_processor import queue_classification_run
                queue_classification_run.delay(run.id)
                run_count += 1
            
            messages.success(
                request, 
                f"Created {run_count} classification runs for {segments.count()} segments across {run_count} recordings. "
                f"Runs have been queued and will be processed sequentially to prevent resource conflicts."
            )
            redirect_url = 'battycoda_app:automation_home'
            if project_id:
                redirect_url += f'?project={project_id}'
            return redirect(redirect_url)
            
        except Exception as e:
            messages.error(request, f"Error creating classification runs: {str(e)}")
            redirect_url = 'battycoda_app:classify_unclassified_segments'
            if project_id:
                redirect_url += f'?project={project_id}'
            return redirect(redirect_url)
    
    # For GET request, show form with available classifiers
    # Get compatible classifiers (based on species or null species)
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
    
    # Get count of unclassified segments
    if profile.group and profile.is_current_group_admin:
        count_filter = {
            'recording__species': species,
            'recording__group': profile.group,
            'detection_results__isnull': True
        }
        if project_id:
            count_filter['recording__project_id'] = project_id
        unclassified_count = Segment.objects.filter(**count_filter).count()
    else:
        count_filter = {
            'recording__species': species,
            'recording__created_by': request.user,
            'detection_results__isnull': True
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
    
    return render(request, 'automation/create_species_classification.html', context)
