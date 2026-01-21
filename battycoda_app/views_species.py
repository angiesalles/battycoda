import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import SpeciesForm
from .models.classification import Classifier
from .models.organization import Call, Species
from .models.recording import Recording
from .models.task import Task, TaskBatch


def _sync_calls_from_json(species, call_types_json, allow_delete=True):
    """
    Sync call types for a species from JSON data.

    Handles both create (no existing calls) and edit (existing calls to sync) cases.
    - Adds new calls
    - Updates existing calls if long_name changed
    - Deletes calls no longer in the list (only if allow_delete=True)

    Args:
        species: Species instance to sync calls for
        call_types_json: JSON string of call types, e.g. '[{"short_name": "A", "long_name": "Call A"}]'
                        Empty string or "[]" will delete all existing calls (if allow_delete=True).
        allow_delete: If False, calls can only be added/updated, not deleted. This is used when
                     the species has classifiers - deletion would break existing classification results.

    Returns:
        None
    """
    call_types_json = (call_types_json or "").strip()

    # Empty or "[]" means delete all calls (only if allowed)
    if not call_types_json or call_types_json == "[]":
        if allow_delete:
            Call.objects.filter(species=species).delete()
        return

    try:
        new_call_types = json.loads(call_types_json)
    except json.JSONDecodeError:
        return

    # Get existing calls indexed by short_name
    existing_calls = {call.short_name: call for call in Call.objects.filter(species=species)}
    seen_short_names = set()

    for call_data in new_call_types:
        short_name = call_data.get("short_name", "").strip()
        long_name = call_data.get("long_name", "").strip()

        if not short_name:
            continue

        seen_short_names.add(short_name)

        if short_name in existing_calls:
            # Update existing call if long_name changed
            existing_call = existing_calls[short_name]
            if existing_call.long_name != long_name:
                existing_call.long_name = long_name
                existing_call.save()
        else:
            # Create new call
            Call.objects.create(species=species, short_name=short_name, long_name=long_name)

    # Delete calls no longer in the list (only if allowed)
    if allow_delete:
        for short_name, call in existing_calls.items():
            if short_name not in seen_short_names:
                call.delete()


@login_required
def species_list_view(request):
    """Display list of species, including system species"""
    # Get the user's profile
    profile = request.user.profile

    # Get system species with task counts filtered by user's group
    system_species = Species.objects.filter(is_system=True).annotate(
        group_task_count=Count("tasks", filter=Q(tasks__group=profile.group))
    )

    # Get group species if the user is in a group
    if profile.group:
        group_species = Species.objects.filter(group=profile.group).annotate(
            group_task_count=Count("tasks", filter=Q(tasks__group=profile.group))
        )
        # Combine system and group species
        species_list = list(system_species) + list(group_species)
    else:
        # If no group is assigned, just show system species
        species_list = system_species

    context = {
        "species_list": species_list,
        "system_species_count": system_species.count(),
    }

    return render(request, "species/species_list.html", context)


@login_required
def species_detail_view(request, species_id):
    """Display detail of a species"""
    species = get_object_or_404(Species, id=species_id)

    # Get user's profile and group
    profile = request.user.profile
    user_group = profile.group

    # Get tasks for this species - limited to user's group
    tasks_list = Task.objects.filter(species=species, group=user_group).order_by("-created_at")

    # Paginate tasks
    tasks_paginator = Paginator(tasks_list, 50)
    tasks_page_number = request.GET.get("tasks_page", 1)
    tasks_page = tasks_paginator.get_page(tasks_page_number)

    # Get batches for this species - limited to user's group
    batches_list = TaskBatch.objects.filter(species=species, group=user_group).order_by("-created_at")

    # Paginate batches
    batches_paginator = Paginator(batches_list, 50)
    batches_page_number = request.GET.get("batches_page", 1)
    batches_page = batches_paginator.get_page(batches_page_number)

    # Get calls for this species
    calls = Call.objects.filter(species=species)

    context = {
        "species": species,
        "tasks_page": tasks_page,
        "tasks_total": tasks_list.count(),
        "batches_page": batches_page,
        "batches_total": batches_list.count(),
        "calls": calls,
    }

    return render(request, "species/species_detail.html", context)


@login_required
def create_species_view(request):
    """Handle creation of a species with image upload and call types"""
    if request.method == "POST":
        form = SpeciesForm(request.POST, request.FILES)

        if form.is_valid():
            # Save species
            species = form.save(commit=False)
            species.created_by = request.user

            # Always set group to user's active group
            species.group = request.user.profile.group
            species.save()

            # Process call types from JSON
            _sync_calls_from_json(species, request.POST.get("call_types_json", ""))

            messages.success(request, "Species created successfully.")
            return redirect("battycoda_app:species_detail", species_id=species.id)
    else:
        form = SpeciesForm()

    # Get all species in the user's group for client-side validation
    existing_species_names = []
    if request.user.profile and request.user.profile.group:
        existing_species_names = list(
            Species.objects.filter(group=request.user.profile.group).values_list("name", flat=True)
        )

    context = {
        "form": form,
        "existing_species_names": existing_species_names,
    }

    return render(request, "species/create_species.html", context)


@login_required
def edit_species_view(request, species_id):
    """Handle editing of a species with unified call types management"""
    species = get_object_or_404(Species, id=species_id)

    # Prevent editing of system species
    if species.is_system:
        messages.error(request, "System species cannot be edited. They are available to all users.")
        return redirect("battycoda_app:species_detail", species_id=species.id)

    # Check if user has permission to edit this species
    profile = request.user.profile
    if species.group != profile.group:
        messages.error(request, "You don't have permission to edit this species.")
        return redirect("battycoda_app:species_list")

    # Check permissions for modifying call types
    can_add_calls = species.can_add_calls()
    can_delete_calls = species.can_delete_calls()
    has_classifiers = not can_delete_calls and not species.is_system

    if request.method == "POST":
        form = SpeciesForm(request.POST, request.FILES, instance=species)

        if form.is_valid():
            with transaction.atomic():
                # Save species basic info
                species = form.save()

                # Process call types from JSON - allow adding if can_add_calls, deletion only if can_delete_calls
                if can_add_calls:
                    _sync_calls_from_json(species, request.POST.get("call_types_json", ""), allow_delete=can_delete_calls)

            messages.success(request, "Species updated successfully.")
            return redirect("battycoda_app:species_detail", species_id=species.id)
    else:
        form = SpeciesForm(instance=species)

    # Get calls for this species (as JSON string for template)
    calls = Call.objects.filter(species=species)
    existing_calls_list = [{"short_name": c.short_name, "long_name": c.long_name or ""} for c in calls]
    existing_calls_json = json.dumps(existing_calls_list)

    context = {
        "form": form,
        "species": species,
        "calls": calls,
        "existing_calls_json": existing_calls_json,
        "can_modify": can_add_calls and can_delete_calls,  # Full modification (legacy)
        "can_add_calls": can_add_calls,
        "can_delete_calls": can_delete_calls,
        "has_classifiers": has_classifiers,
    }

    return render(request, "species/edit_species.html", context)


@login_required
def delete_species_view(request, species_id):
    """Delete a species and its associated data"""
    species = get_object_or_404(Species, id=species_id)

    # Prevent deletion of system species
    if species.is_system:
        messages.error(request, "System species cannot be deleted. They are available to all users.")
        return redirect("battycoda_app:species_detail", species_id=species.id)

    # Check if the user has permission to delete this species
    profile = request.user.profile
    if species.created_by != request.user and (
        not profile.group or species.group != profile.group or not profile.is_current_group_admin
    ):
        messages.error(request, "You don't have permission to delete this species.")
        return redirect("battycoda_app:species_list")

    # Get counts of related objects for context
    task_count = Task.objects.filter(species=species).count()
    batch_count = TaskBatch.objects.filter(species=species).count()
    call_count = Call.objects.filter(species=species).count()
    recording_count = Recording.objects.filter(species=species).count()

    # Check if this species has classifiers
    classifier_count = Classifier.objects.filter(species=species).count()

    # Check if deletion is allowed (no tasks, batches, recordings, or classifiers associated)
    has_dependencies = task_count > 0 or batch_count > 0 or recording_count > 0 or classifier_count > 0

    if request.method == "POST":
        if has_dependencies:
            messages.error(
                request,
                "Cannot delete species with associated tasks, batches, recordings, or classifiers. "
                "Please remove these dependencies first.",
            )
            return redirect("battycoda_app:delete_species", species_id=species.id)

        try:
            with transaction.atomic():
                # Store name for the success message
                species_name = species.name

                # Delete the species (this will cascade to calls)
                species.delete()

                messages.success(request, f"Successfully deleted species: {species_name}")
                return redirect("battycoda_app:species_list")
        except Exception as e:
            messages.error(request, f"Failed to delete species: {str(e)}")

    context = {
        "species": species,
        "task_count": task_count,
        "batch_count": batch_count,
        "call_count": call_count,
        "recording_count": recording_count,
        "classifier_count": classifier_count,
    }

    return render(request, "species/delete_species.html", context)


@login_required
@require_POST
def parse_calls_file_view(request):
    """Parse a calls file and return the extracted call types as JSON.
    This endpoint is called asynchronously when a user selects a file to upload.
    It parses the file and returns the call types so they can be added to the form
    before the main form is submitted."""
    if "calls_file" not in request.FILES:
        return JsonResponse({"success": False, "error": "No file provided"})

    calls_file = request.FILES["calls_file"]

    try:
        # Read the content of the file
        file_content = calls_file.read().decode("utf-8")

        # Parse the content and extract call types
        calls = []

        # Process each line
        for line in file_content.splitlines():
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            if "," in line:
                short_name, long_name = line.split(",", 1)
            elif "|" in line:
                short_name, long_name = line.split("|", 1)
            elif "\t" in line:
                short_name, long_name = line.split("\t", 1)
            else:
                # If no separator, use whole line as short_name and leave long_name empty
                short_name = line
                long_name = ""

            short_name = short_name.strip()
            long_name = long_name.strip()

            # Add to calls list
            calls.append({"short_name": short_name, "long_name": long_name})

        # Return JSON response with parsed calls
        return JsonResponse({"success": True, "calls": calls})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
