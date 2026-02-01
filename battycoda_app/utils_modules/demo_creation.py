"""
Functions for creating demo data objects (recordings, segmentations, classifications, tasks).

These functions raise exceptions on failure rather than returning None,
allowing the caller to handle errors appropriately and roll back transactions.
"""

import logging

from django.core.files import File
from django.utils import timezone

logger = logging.getLogger(__name__)


def create_demo_recording(user, group, project, species, wav_path):
    """Create a demo recording for a user.

    Args:
        user: The User object
        group: The Group object
        project: The Project object
        species: The Species object
        wav_path: Path to the WAV file

    Returns:
        Recording: The created Recording object

    Raises:
        Exception: If recording creation fails
    """
    from battycoda_app.models.recording import Recording

    logger.debug("Creating demo recording for user %s", user.username)

    # Create the recording
    # Set processing_status="ready" for demo data - it's pre-made and expected to work immediately
    recording = Recording(
        name="Demo Bat Recording",
        description="Sample bat calls for demonstration and practice",
        created_by=user,
        species=species,
        project=project,
        group=group,
        processing_status="ready",
    )
    recording.save()

    # Attach the WAV file
    with open(wav_path, "rb") as wav_file:
        recording.wav_file.save("bat1_angie_19.wav", File(wav_file), save=True)

    logger.debug("Created demo recording id=%d", recording.id)
    return recording


def create_demo_segmentation(user, recording, pickle_path):
    """Create demo segmentation for a recording.

    Args:
        user: The User object
        recording: The Recording object
        pickle_path: Path to the pickle file with segment data

    Returns:
        Segmentation: The created Segmentation object

    Raises:
        Exception: If segmentation creation fails
    """
    from battycoda_app.audio.utils import process_pickle_file
    from battycoda_app.models.segmentation import Segment, Segmentation

    logger.debug("Creating demo segmentation for recording id=%d", recording.id)

    # Open and process the pickle file
    with open(pickle_path, "rb") as f:
        onsets, offsets = process_pickle_file(f)

    # Create the segmentation object
    segmentation = Segmentation(
        recording=recording,
        status="completed",  # Already completed
        progress=100,
        created_by=user,
        manually_edited=False,
    )
    segmentation.save()

    # Only use the first 10 entries to keep the demo manageable
    max_entries = min(10, len(onsets))

    # Create segments
    for i in range(max_entries):
        # Convert numpy types to Python native types if needed
        onset_value = float(onsets[i])
        offset_value = float(offsets[i])

        # Create and save the segment
        Segment.objects.create(
            recording=recording,
            segmentation=segmentation,
            name=f"Segment {i + 1}",
            onset=onset_value,
            offset=offset_value,
            created_by=user,
        )

    logger.debug("Created demo segmentation id=%d with %d segments", segmentation.id, max_entries)
    return segmentation


def run_demo_classification(user, group, segmentation):
    """Run the dummy classifier on demo segments.

    Args:
        user: The User object
        group: The Group object
        segmentation: The Segmentation object

    Returns:
        ClassificationRun: The created ClassificationRun object

    Raises:
        Classifier.DoesNotExist: If the dummy classifier is not found
        Exception: If classification fails
    """
    from battycoda_app.audio.task_modules.classification.dummy_classifier import run_dummy_classifier
    from battycoda_app.models.classification import ClassificationRun, Classifier

    logger.debug("Running demo classification for segmentation id=%d", segmentation.id)

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

    logger.debug("Completed demo classification run id=%d", classification_run.id)
    return classification_run


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
        TaskBatch: The created TaskBatch object

    Raises:
        Exception: If task batch creation fails
    """
    from battycoda_app.models.classification import CallProbability, ClassificationResult
    from battycoda_app.models.task import Task, TaskBatch

    logger.debug("Creating task batch from classification run id=%d", classification_run.id)

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
        classification_run=classification_run,
    )

    # Get all classification results from this run
    results = ClassificationResult.objects.filter(classification_run=classification_run)
    task_count = 0

    for result in results:
        segment = result.segment

        # Get the highest probability call type
        top_probability = CallProbability.objects.filter(classification_result=result).order_by("-probability").first()

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
            label=top_probability.call.short_name if top_probability else None,
            status="pending",
        )

        # Link the task back to the segment
        segment.task = task
        segment.save()
        task_count += 1

    logger.debug("Created task batch id=%d with %d tasks", batch.id, task_count)
    return batch
