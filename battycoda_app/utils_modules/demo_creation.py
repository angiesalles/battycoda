"""
Functions for creating demo data objects (recordings, segmentations, classifications, tasks).
"""

from django.core.files import File
from django.db import transaction
from django.utils import timezone


def create_demo_recording(user, group, project, species, wav_path):
    """Create a demo recording for a user.

    Args:
        user: The User object
        group: The Group object
        project: The Project object
        species: The Species object
        wav_path: Path to the WAV file

    Returns:
        Recording: The created Recording object or None if creation failed
    """
    from battycoda_app.models.recording import Recording

    try:
        # Create the recording
        recording = Recording(
            name="Demo Bat Recording",
            description="Sample bat calls for demonstration and practice",
            created_by=user,
            species=species,
            project=project,
            group=group,
        )
        recording.save()

        # Attach the WAV file
        with open(wav_path, "rb") as wav_file:
            recording.wav_file.save("bat1_angie_19.wav", File(wav_file), save=True)

        return recording
    except Exception:
        return None


def create_demo_segmentation(user, recording, pickle_path):
    """Create demo segmentation for a recording.

    Args:
        user: The User object
        recording: The Recording object
        pickle_path: Path to the pickle file with segment data

    Returns:
        Segmentation: The created Segmentation object or None if creation failed
    """
    from battycoda_app.audio.utils import process_pickle_file
    from battycoda_app.models.segmentation import Segment, Segmentation

    try:
        # Open and process the pickle file
        with open(pickle_path, "rb") as f:
            onsets, offsets = process_pickle_file(f)

        # Create segments from the onset/offset pairs
        segments_created = 0

        # Create the segmentation object
        segmentation = Segmentation(
            recording=recording,
            status="completed",  # Already completed
            progress=100,
            created_by=user,
            manually_edited=False,
        )
        segmentation.save()

        with transaction.atomic():
            # Only use the first 10 entries to keep the demo manageable
            max_entries = min(10, len(onsets))

            # Create segments
            for i in range(max_entries):
                # Convert numpy types to Python native types if needed
                onset_value = float(onsets[i])
                offset_value = float(offsets[i])

                # Create and save the segment
                segment = Segment(
                    recording=recording,
                    name=f"Segment {i + 1}",
                    onset=onset_value,
                    offset=offset_value,
                    created_by=user,
                )
                segment.save()
                segments_created += 1

        return segmentation
    except Exception:
        return None


def run_demo_classification(user, group, segmentation):
    """Run the dummy classifier on demo segments.

    Args:
        user: The User object
        group: The Group object
        segmentation: The Segmentation object

    Returns:
        ClassificationRun: The created ClassificationRun object or None if creation failed
    """
    from battycoda_app.audio.task_modules.classification.dummy_classifier import run_dummy_classifier
    from battycoda_app.models.classification import ClassificationRun, Classifier

    try:
        # Find the dummy classifier
        dummy_classifier = Classifier.objects.get(name="Dummy Classifier")

        # Create a classification run
        classification_run = ClassificationRun.objects.create(
            name="Demo Classification Run",
            segmentation=segmentation,
            created_by=user,
            group=group,
            classifier=dummy_classifier,
            algorithm_type="full_probability",
            status="pending",
            progress=0,
        )

        # Run the dummy classifier directly (not through Celery)
        run_dummy_classifier(classification_run.id)

        # Make sure the run is marked as completed
        classification_run.refresh_from_db()
        if classification_run.status != "completed":
            classification_run.status = "completed"
            classification_run.progress = 100
            classification_run.save()

        return classification_run
    except Classifier.DoesNotExist:
        return None
    except Exception:
        return None


def create_task_batch_from_classification(user, group, project, species, recording, classification_run):
    """Create a task batch from a classification run.

    Args:
        user: The User object
        group: The Group object
        project: The Project object
        species: The Species object
        recording: The Recording object
        classification_run: The ClassificationRun object

    Returns:
        TaskBatch: The created TaskBatch object or None if creation failed
    """
    from battycoda_app.models.classification import CallProbability, ClassificationResult
    from battycoda_app.models.task import Task, TaskBatch

    try:
        # Create a unique batch name with timestamp
        batch_name = f"Demo Bat Calls ({timezone.now().strftime('%Y%m%d-%H%M%S')})"

        # Create the task batch
        batch = TaskBatch.objects.create(
            name=batch_name,
            description="Sample bat calls for demonstration and practice",
            created_by=user,
            wav_file_name=recording.wav_file.name,
            wav_file=recording.wav_file,
            species=species,
            project=project,
            group=group,
            classification_run=classification_run,  # Link to the classification run
        )

        # Create tasks for each classification result's segment
        tasks_created = 0
        with transaction.atomic():
            # Get all classification results from this run
            results = ClassificationResult.objects.filter(classification_run=classification_run)

            for result in results:
                segment = result.segment

                # Get the highest probability call type
                top_probability = (
                    CallProbability.objects.filter(classification_result=result).order_by("-probability").first()
                )

                # Create a task for this segment
                task = Task.objects.create(
                    wav_file_name=recording.wav_file.name,
                    onset=segment.onset,
                    offset=segment.offset,
                    species=species,
                    project=project,
                    batch=batch,
                    created_by=user,
                    group=group,
                    # Use the highest probability call type as the initial label
                    label=top_probability.call.short_name if top_probability else None,
                    status="pending",
                )

                # Link the task back to the segment
                segment.task = task
                segment.save()

                tasks_created += 1

        return batch
    except Exception:
        return None
