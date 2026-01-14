import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .forms import SpeciesEditForm, SpeciesForm
from .models.organization import Call, Species
from .models.recording import Recording
from .models.task import Task, TaskBatch

# Set up logging


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
            call_types_json = request.POST.get("call_types_json", "[]")

            # If the JSON is empty or whitespace, use an empty list
            call_types_json = call_types_json.strip()
            if call_types_json and call_types_json != "[]":
                call_types = json.loads(call_types_json)

                for call_data in call_types:
                    # Create the call
                    short_name = call_data.get("short_name", "").strip()
                    long_name = call_data.get("long_name", "").strip()

                    if short_name:
                        # Check for duplicates
                        if not Call.objects.filter(species=species, short_name=short_name).exists():
                            call = Call(species=species, short_name=short_name, long_name=long_name)
                            call.save()
                        # Skip duplicates silently
                    # Skip calls with empty short_name silently

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
    """Handle editing of a species"""
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

    # Get calls for this species
    calls = Call.objects.filter(species=species)

    if request.method == "POST":
        form = SpeciesEditForm(request.POST, request.FILES, instance=species)

        if form.is_valid():
            # Save species (basic info only)
            species = form.save()
            messages.success(request, "Species updated successfully.")
            return redirect("battycoda_app:species_detail", species_id=species.id)
    else:
        form = SpeciesEditForm(instance=species)

    # Get calls again to ensure they're in the context
    calls = Call.objects.filter(species=species)

    # Check if this species has classifiers (which would prevent modifying call types)
    can_modify_calls = species.can_modify_calls()

    context = {
        "form": form,
        "species": species,
        "calls": calls,  # Explicitly add calls to context
        "can_modify": can_modify_calls,
        "has_classifiers": not can_modify_calls,
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
    from .models.classification import Classifier

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
def add_call_view(request, species_id):
    """Add a new call to a species and return the updated calls list HTML"""
    species = get_object_or_404(Species, id=species_id)

    # Prevent modifying system species
    if species.is_system:
        return JsonResponse(
            {"success": False, "error": "System species cannot be modified. They are available to all users."}
        )

    # Check if user has permission to edit this species
    profile = request.user.profile
    if species.group != profile.group:
        return JsonResponse({"success": False, "error": "You don't have permission to modify this species."})

    # Check if species has classifiers (which would prevent modifying call types)
    if not species.can_modify_calls():
        return JsonResponse(
            {
                "success": False,
                "error": "Cannot modify call types for this species because it is used by one or more classifiers. "
                "Classifiers are tied to the call types of their species.",
            }
        )

    # Get the call data from the request
    try:
        data = json.loads(request.body)
        short_name = data.get("short_name", "").strip()
        long_name = data.get("long_name", "").strip()

        if not short_name:
            return JsonResponse({"success": False, "error": "Short name is required."})

        # Check if a call with this name already exists
        if Call.objects.filter(species=species, short_name=short_name).exists():
            return JsonResponse({"success": False, "error": f"A call with short name '{short_name}' already exists."})

        # Create the new call
        call = Call(species=species, short_name=short_name, long_name=long_name)
        call.save()

        # Get updated list of calls
        calls = Call.objects.filter(species=species)

        # Render the updated calls table HTML
        calls_html = render_to_string(
            "species/includes/calls_table.html", {"calls": calls, "can_modify": species.can_modify_calls()}
        )

        return JsonResponse(
            {"success": True, "calls_html": calls_html, "message": f"Call '{short_name}' added successfully."}
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def delete_call_view(request, species_id, call_id):
    """Delete a call from a species and return the updated calls list HTML"""
    species = get_object_or_404(Species, id=species_id)
    call = get_object_or_404(Call, id=call_id, species=species)

    # Prevent modifying system species
    if species.is_system:
        return JsonResponse(
            {"success": False, "error": "System species cannot be modified. They are available to all users."}
        )

    # Check if user has permission to edit this species
    profile = request.user.profile
    if species.group != profile.group:
        return JsonResponse({"success": False, "error": "You don't have permission to modify this species."})

    # Check if call can be deleted (species must not have classifiers)
    if not call.can_be_deleted():
        return JsonResponse(
            {
                "success": False,
                "error": "Cannot delete call types for this species because it is used by one or more classifiers. "
                "Classifiers are tied to the call types of their species.",
            }
        )

    try:
        # Delete the call
        call_short_name = call.short_name
        call.delete()

        # Get updated list of calls
        calls = Call.objects.filter(species=species)

        # Render the updated calls table HTML
        calls_html = render_to_string(
            "species/includes/calls_table.html", {"calls": calls, "can_modify": species.can_modify_calls()}
        )

        return JsonResponse(
            {"success": True, "calls_html": calls_html, "message": f"Call '{call_short_name}' deleted successfully."}
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


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
