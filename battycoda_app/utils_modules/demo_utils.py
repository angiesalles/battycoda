"""
Utility functions for creating demo data.

This module provides the main entry point for creating demo task batches.
Implementation details are split across:
- demo_config: Configuration and prerequisite checking
- demo_creation: Functions for creating demo objects
"""

from .demo_config import check_demo_prerequisites
from .demo_creation import (
    create_demo_recording,
    create_demo_segmentation,
    create_task_batch_from_classification,
    run_demo_classification,
)


def create_demo_task_batch(user):
    """Create a demo task batch for a new user using sample files.

    Args:
        user: The User object to create the task batch for

    Returns:
        TaskBatch or None: The created TaskBatch object, or None if creation failed
    """
    # Get the user's group and profile
    profile = user.profile
    group = profile.group
    if not group:
        return None

    # Prerequisites: check for required resources
    try:
        # Find the user's demo project
        project, species, sample_files = check_demo_prerequisites(user, group)
        if not project or not species or not sample_files:
            return None

        # Extract sample file paths
        wav_path, pickle_path = sample_files

        # Step 1: Create a demo recording
        recording = create_demo_recording(user, group, project, species, wav_path)
        if not recording:
            return None

        # Step 2: Create segmentation and segments
        segmentation = create_demo_segmentation(user, recording, pickle_path)
        if not segmentation:
            return None

        # Step 3: Run classification
        classification_run = run_demo_classification(user, group, segmentation)
        if not classification_run:
            return None

        # Step 4: Create a task batch from the classification run
        batch = create_task_batch_from_classification(user, group, project, species, recording, classification_run)

        if batch:
            return batch

    except Exception as e:
        # Print the exception for debugging
        print(f"Error creating demo task batch: {str(e)}")
        import traceback

        traceback.print_exc()
        return None
