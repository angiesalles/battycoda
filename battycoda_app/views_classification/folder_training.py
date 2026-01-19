"""Views for training classifiers from pre-labeled training data folders."""

import os

import soundfile as sf
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from battycoda_app.models.classification import ClassifierTrainingJob
from battycoda_app.models.organization import Call, Species


def _get_training_data_base():
    """Get the base path for training data folders."""
    return os.path.join(settings.BASE_DIR, "training_data")


def _validate_folder_name(folder_name):
    """
    Validate folder name to prevent path traversal attacks.

    Raises Http404 if the folder name is invalid.
    """
    if not folder_name:
        raise Http404("Folder name is required")

    # Reject path traversal attempts
    if ".." in folder_name or folder_name.startswith("/") or folder_name.startswith("\\"):
        raise Http404("Invalid folder name")

    # Reject names with path separators
    if "/" in folder_name or "\\" in folder_name:
        raise Http404("Invalid folder name")

    return folder_name


def _parse_label_from_filename(filename):
    """
    Parse label from a WAV filename.

    Expected format: NUMBER_LABEL.wav (e.g., 001_echolocation.wav)

    Returns:
        str or None: The label if successfully parsed, None otherwise
    """
    parts = filename.rsplit("_", 1)
    if len(parts) != 2:
        return None

    label = parts[1].replace(".wav", "").replace(".WAV", "")
    return label if label else None


def _extract_labels_from_folder(folder_path):
    """
    Extract unique labels from WAV files in a folder.

    Files must be named: NUMBER_LABEL.wav (e.g., 001_echolocation.wav)

    Returns:
        tuple: (wav_files, labels) where wav_files is list of filenames
               and labels is set of unique label strings
    """
    wav_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".wav")]
    labels = set()

    for wav_file in wav_files:
        label = _parse_label_from_filename(wav_file)
        if label:
            labels.add(label)

    return wav_files, labels


def _get_available_species(user):
    """Get species available to a user based on their group membership."""
    profile = user.profile
    if profile.group:
        return Species.objects.filter(models.Q(group=profile.group) | models.Q(is_system=True)).order_by("name")
    return Species.objects.filter(is_system=True).order_by("name")


def validate_training_folder(folder_path, species):
    """
    Validate training data folder and return validation results.

    Returns:
        tuple: (is_valid, errors, warnings, stats)
    """
    errors = []
    warnings = []
    stats = {
        "total_files": 0,
        "valid_files": 0,
        "files_by_label": {},
        "invalid_files": [],
        "unlabeled_files": [],
        "unreadable_files": [],
    }

    if not os.path.exists(folder_path):
        errors.append(f"Folder does not exist: {folder_path}")
        return False, errors, warnings, stats

    if not os.path.isdir(folder_path):
        errors.append(f"Path is not a directory: {folder_path}")
        return False, errors, warnings, stats

    all_files = os.listdir(folder_path)
    wav_files = [f for f in all_files if f.lower().endswith(".wav")]

    if len(wav_files) == 0:
        errors.append("No WAV files found in folder")
        return False, errors, warnings, stats

    stats["total_files"] = len(wav_files)

    non_wav_files = [f for f in all_files if not f.lower().endswith(".wav") and not f.startswith(".")]
    if non_wav_files:
        warnings.append(f"Found {len(non_wav_files)} non-WAV files in folder (will be ignored)")

    for wav_file in wav_files:
        file_path = os.path.join(folder_path, wav_file)

        label = _parse_label_from_filename(wav_file)
        if not label:
            stats["unlabeled_files"].append(wav_file)
            continue

        try:
            with sf.SoundFile(file_path) as audio_file:
                if audio_file.frames == 0:
                    stats["unreadable_files"].append(f"{wav_file} (empty file)")
                    continue
                if audio_file.samplerate <= 0:
                    stats["unreadable_files"].append(f"{wav_file} (invalid sample rate)")
                    continue
        except Exception as e:
            stats["unreadable_files"].append(f"{wav_file} ({str(e)})")
            continue

        if label not in stats["files_by_label"]:
            stats["files_by_label"][label] = 0
        stats["files_by_label"][label] += 1
        stats["valid_files"] += 1

    if stats["unlabeled_files"]:
        errors.append(
            f"Found {len(stats['unlabeled_files'])} files without proper labels (must be in format: NUMBER_LABEL.wav)"
        )

    if stats["unreadable_files"]:
        errors.append(f"Found {len(stats['unreadable_files'])} unreadable or invalid audio files")

    if stats["valid_files"] < 5:
        errors.append(f"Insufficient valid training files. Found {stats['valid_files']}, need at least 5")

    if len(stats["files_by_label"]) < 2:
        errors.append(f"Need at least 2 different call types for training. Found {len(stats['files_by_label'])}")

    species_calls = Call.objects.filter(species=species)
    if species_calls.exists():
        species_call_names = {call.short_name for call in species_calls}
        folder_labels = set(stats["files_by_label"].keys())

        missing_in_folder = species_call_names - folder_labels
        if missing_in_folder:
            warnings.append(
                f"Species has call types not present in training data: {', '.join(sorted(missing_in_folder))}"
            )

        extra_in_folder = folder_labels - species_call_names
        if extra_in_folder:
            errors.append(
                f"Training data contains call types not defined for this species: {', '.join(sorted(extra_in_folder))}"
            )

    min_samples_per_class = 2
    insufficient_classes = [label for label, count in stats["files_by_label"].items() if count < min_samples_per_class]
    if insufficient_classes:
        errors.append(
            f"Some call types have fewer than {min_samples_per_class} samples: {', '.join(insufficient_classes)}"
        )

    is_valid = len(errors) == 0
    return is_valid, errors, warnings, stats


@login_required
def select_training_folder_view(request):
    """Display list of available training data folders."""
    training_data_base = _get_training_data_base()

    if not os.path.exists(training_data_base):
        messages.error(request, "Training data directory does not exist")
        return redirect("battycoda_app:classifier_list")

    folders = []
    for item in os.listdir(training_data_base):
        item_path = os.path.join(training_data_base, item)
        if os.path.isdir(item_path):
            wav_files, labels = _extract_labels_from_folder(item_path)
            folders.append(
                {
                    "name": item,
                    "file_count": len(wav_files),
                    "label_count": len(labels),
                }
            )

    folders.sort(key=lambda x: x["name"])

    return render(
        request,
        "classification/select_training_folder.html",
        {
            "folders": folders,
            "training_data_base": training_data_base,
        },
    )


@login_required
def training_folder_details_view(request, folder_name):
    """Display folder details and validation results for a training data folder."""
    _validate_folder_name(folder_name)
    training_data_base = _get_training_data_base()
    folder_path = os.path.join(training_data_base, folder_name)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        messages.error(request, f"Training data folder '{folder_name}' does not exist")
        return redirect("battycoda_app:select_training_folder")

    wav_files, labels = _extract_labels_from_folder(folder_path)
    available_species = _get_available_species(request.user)

    selected_species_id = request.GET.get("species_id")
    validation_results = None

    if selected_species_id:
        try:
            selected_species = Species.objects.get(id=selected_species_id)
            is_valid, errors, warnings, stats = validate_training_folder(folder_path, selected_species)
            validation_results = {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "stats": stats,
                "species": selected_species,
            }
        except Species.DoesNotExist:
            pass

    return render(
        request,
        "classification/create_classifier_from_folder.html",
        {
            "folder_name": folder_name,
            "folder_path": folder_path,
            "file_count": len(wav_files),
            "label_count": len(labels),
            "labels": sorted(labels),
            "available_species": available_species,
            "selected_species_id": selected_species_id,
            "validation_results": validation_results,
        },
    )


@login_required
def create_training_job_view(request, folder_name):
    """Create a new classifier training job from a training data folder (POST only)."""
    _validate_folder_name(folder_name)
    if request.method != "POST":
        return redirect("battycoda_app:training_folder_details", folder_name=folder_name)

    training_data_base = _get_training_data_base()

    name = request.POST.get("name")
    description = request.POST.get("description", "")
    algorithm_type = request.POST.get("algorithm_type", "knn")
    species_id = request.POST.get("species_id")

    if not species_id:
        messages.error(request, "Species selection is required")
        return redirect("battycoda_app:training_folder_details", folder_name=folder_name)

    folder_path = os.path.join(training_data_base, folder_name)
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        messages.error(request, f"Training data folder '{folder_name}' does not exist")
        return redirect("battycoda_app:select_training_folder")

    species = get_object_or_404(Species, id=species_id)
    profile = request.user.profile

    if species.group and species.group != profile.group:
        messages.error(request, "You don't have permission to use this species")
        return redirect("battycoda_app:select_training_folder")

    is_valid, errors, warnings, stats = validate_training_folder(folder_path, species)

    if not is_valid:
        for error in errors:
            messages.error(request, error)
        return redirect("battycoda_app:training_folder_details", folder_name=folder_name)

    for warning in warnings:
        messages.warning(request, warning)

    parameters = {"algorithm_type": algorithm_type, "training_data_folder": folder_path}

    try:
        job = ClassifierTrainingJob.objects.create(
            name=name or f"Classifier from {folder_name}",
            description=description,
            task_batch=None,
            created_by=request.user,
            group=profile.group,
            response_format="full_probability",
            parameters=parameters,
            status="pending",
            progress=0.0,
        )

        from battycoda_app.audio.task_modules.training_tasks import train_classifier_from_folder

        train_classifier_from_folder.delay(job.id, species.id)

        messages.success(request, "Classifier training job created successfully. Training will begin shortly.")
        return redirect("battycoda_app:classifier_training_job_detail", job_id=job.id)

    except Exception as e:
        messages.error(request, f"Error creating classifier training job: {str(e)}")
        return redirect("battycoda_app:select_training_folder")


# Legacy view for backwards compatibility with existing URL patterns
@login_required
def create_classifier_from_folder_view(request, folder_name=None):
    """
    Legacy dispatcher that routes to the appropriate view.

    This maintains backwards compatibility with existing URL patterns.
    """
    if request.method == "POST":
        # POST always has folder_name from form or URL
        folder_name = request.POST.get("folder_name") or folder_name
        if not folder_name:
            messages.error(request, "Training data folder is required")
            return redirect("battycoda_app:select_training_folder")
        return create_training_job_view(request, folder_name)

    if folder_name:
        return training_folder_details_view(request, folder_name)

    return select_training_folder_view(request)
