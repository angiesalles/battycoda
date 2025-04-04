"""Management views for detection runs.

Provides views for creating, listing, and managing detection runs.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from battycoda_app.models.detection import CallProbability, Classifier, DetectionResult, DetectionRun
from battycoda_app.models.recording import Segmentation

@login_required
def automation_home_view(request):
    """Display a list of classification runs with a button to start a new one."""
    try:
        profile = request.user.profile
        
        # Import classifier training job model
        from battycoda_app.models.detection import ClassifierTrainingJob

        # Get all detection runs, classifiers, and training jobs for user's groups
        if profile.group:
            if profile.is_admin:
                # Admin can see all group items
                runs = DetectionRun.objects.filter(group=profile.group).order_by("-created_at")
                classifiers = Classifier.objects.filter(
                    models.Q(group=profile.group) | models.Q(group__isnull=True)
                ).order_by("-created_at")
                training_jobs = ClassifierTrainingJob.objects.filter(group=profile.group).order_by("-created_at")
            else:
                # Regular users see only their own items plus global items
                runs = DetectionRun.objects.filter(group=profile.group, created_by=request.user).order_by("-created_at")
                classifiers = Classifier.objects.filter(
                    models.Q(group=profile.group, created_by=request.user) | models.Q(group__isnull=True)
                ).order_by("-created_at")
                training_jobs = ClassifierTrainingJob.objects.filter(
                    group=profile.group, created_by=request.user
                ).order_by("-created_at")
        else:
            # No group - only see personal items plus global items
            runs = DetectionRun.objects.filter(created_by=request.user).order_by("-created_at")
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
            
        context = {
            "runs": valid_runs,
            "classifiers": classifiers,
            "training_jobs": training_jobs,
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
            run = DetectionRun.objects.create(
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
        if profile.is_admin:
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
            "name": f"{segmentation.recording.name} - {segmentation.algorithm.name if segmentation.algorithm else 'Custom'}",
            "type_name": "Segmentation",
            "count": segmentation.segments.count(),
            "created_at": segmentation.created_at,
            "detail_url": f"/recordings/{segmentation.recording.id}/",
            "action_url": f"/automation/runs/create/{segmentation.id}/",
        })

    context = {
        "title": "Create Classification Run",
        "list_title": "Available Segmentations",
        "action_text": "Create Run",
        "action_icon": "bolt",
        "parent_url": "battycoda_app:automation_home",
        "parent_name": "Automation",
        "th1": "Recording",
        "th2": "Algorithm",
        "th3": "Segments",
        "show_count": True,
        "empty_message": "No segmentations available. You need to create segmentations first.",
        "create_url": "battycoda_app:batch_segmentation",
        "items": items,
    }

    return render(request, "automation/select_entity.html", context)

@login_required
def delete_detection_run_view(request, run_id):
    """Delete a classification run."""
    # Get the detection run by ID
    run = get_object_or_404(DetectionRun, id=run_id)

    # Check if the user has permission
    profile = request.user.profile
    if run.created_by != request.user and (not profile.group or run.group != profile.group):
        messages.error(request, "You don't have permission to delete this classification run.")
        return redirect("battycoda_app:automation_home")

    if request.method == "POST":
        # Delete all related results first
        CallProbability.objects.filter(detection_result__detection_run=run).delete()
        DetectionResult.objects.filter(detection_run=run).delete()

        # Store name for confirmation message
        run_name = run.name

        # Now delete the run itself
        run.delete()

        messages.success(request, f"Classification run '{run_name}' has been deleted.")
        return redirect("battycoda_app:automation_home")

    # For GET requests, show confirmation page
    return render(request, "automation/delete_run.html", {"run": run})
