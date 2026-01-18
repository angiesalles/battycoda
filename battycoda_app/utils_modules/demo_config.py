"""
Configuration and prerequisite checking for demo data creation.
"""

import os


def get_sample_file_paths():
    """Get paths to sample audio files used for demo data.

    Returns:
        dict: Dictionary with 'wav' and 'pickle' keys containing lists of possible paths
    """
    from django.conf import settings

    sample_audio_dir = os.path.join(settings.BASE_DIR, "data", "sample_audio")
    return {
        "wav": [os.path.join(sample_audio_dir, "bat1_angie_19.wav")],
        "pickle": [
            os.path.join(sample_audio_dir, "bat1_angie_19.wav.pickle"),
        ],
    }


def find_existing_file(paths):
    """Find the first existing file from a list of paths.

    Args:
        paths: List of file paths to check

    Returns:
        str or None: The first existing path, or None if none exist
    """
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def check_demo_prerequisites(user, group):
    """Check prerequisites for creating a demo task batch.

    Args:
        user: The User object
        group: The Group object

    Returns:
        tuple: (project, species, sample_files) or (None, None, None) if prerequisites not met
               sample_files is a tuple of (wav_path, pickle_path)
    """
    from battycoda_app.models.organization import Project, Species

    # Find the user's demo project
    project = Project.objects.filter(group=group, name__contains="Demo Project").first()
    if not project:
        return None, None, None

    # Find the Carollia species - first try in the user's group, then look for system species
    species = Species.objects.filter(group=group, name__icontains="Carollia").first()
    if not species:
        # Try system species
        species = Species.objects.filter(is_system=True, name__icontains="Carollia").first()
    if not species:
        return None, None, None

    # Get sample file paths
    sample_paths = get_sample_file_paths()

    # Find the sample WAV file
    wav_path = find_existing_file(sample_paths["wav"])
    if not wav_path:
        return None, None, None

    # Find the sample pickle file
    pickle_path = find_existing_file(sample_paths["pickle"])
    if not pickle_path:
        return None, None, None

    return project, species, (wav_path, pickle_path)
