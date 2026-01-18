"""
Utility functions for creating demo data.

This module provides the main entry point for creating demo task batches.
Implementation details are split across:
- demo_config: Configuration and prerequisite checking
- demo_creation: Functions for creating demo objects
"""

import logging

from django.db import transaction

from .demo_config import check_demo_prerequisites
from .demo_creation import (
    create_demo_recording,
    create_demo_segmentation,
    create_task_batch_from_classification,
    run_demo_classification,
)

logger = logging.getLogger(__name__)


def create_demo_task_batch(user):
    """Create a demo task batch for a new user using sample files.

    This operation is atomic - if any step fails, all database changes
    are rolled back to prevent orphaned objects.

    Args:
        user: The User object to create the task batch for

    Returns:
        TaskBatch or None: The created TaskBatch object, or None if creation failed
    """
    # Get the user's group and profile
    profile = user.profile
    group = profile.group
    if not group:
        logger.warning("Cannot create demo task batch: user %s has no group", user.username)
        return None

    # Check prerequisites before starting transaction
    project, species, sample_files = check_demo_prerequisites(user, group)
    if not project or not species or not sample_files:
        logger.info("Demo prerequisites not met for user %s (missing project, species, or sample files)", user.username)
        return None

    wav_path, pickle_path = sample_files

    try:
        # Wrap all database operations in a transaction for atomic rollback
        with transaction.atomic():
            logger.info("Creating demo task batch for user %s", user.username)

            # Step 1: Create a demo recording
            recording = create_demo_recording(user, group, project, species, wav_path)

            # Step 2: Create segmentation and segments
            segmentation = create_demo_segmentation(user, recording, pickle_path)

            # Step 3: Run classification
            classification_run = run_demo_classification(user, group, segmentation)

            # Step 4: Create a task batch from the classification run
            batch = create_task_batch_from_classification(user, group, project, species, recording, classification_run)

            logger.info("Successfully created demo task batch id=%d for user %s", batch.id, user.username)
            return batch

    except Exception:
        logger.exception("Failed to create demo task batch for user %s", user.username)
        return None
