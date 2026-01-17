"""
Utility functions for species management.
"""

import os
import time

from django.core.files import File

from .path_utils import get_species_images_path


def available_species():
    """
    Get a list of available default species

    Returns:
        list: List of default species names
    """
    try:
        from battycoda_app.default_species import DEFAULT_SPECIES

        return [species["name"] for species in DEFAULT_SPECIES]
    except ImportError:
        return []


def setup_system_species():
    """
    Verify that system-wide species (Eptesicus fuscus and Carollia perspicillata) exist
    This function is a no-op now, as system species are created through migrations

    Returns:
        list: List of system Species objects
    """
    from battycoda_app.models.organization import Species

    system_species = list(Species.objects.filter(is_system=True))

    return system_species


def import_default_species(user):
    """Import default species for a new user's group
    For each new user, only Saccopteryx bilineata is created for their group

    Args:
        user: The User object to import species for

    Returns:
        list: List of created Species objects
    """
    from battycoda_app.models.organization import Call, Species

    time.sleep(1)

    group = user.profile.group
    if not group:
        return []

    created_species = []

    setup_system_species()

    species_name = "Saccopteryx bilineata"

    if not Species.objects.filter(name=species_name, group=group).exists():
        species = Species.objects.create(
            name=species_name,
            description="Saccopteryx bilineata, known as the greater sac-winged bat, is a bat species in the family Emballonuridae. Figure and call types from Christian C. Voigt, Oliver Behr, Barbara Caspers, Otto von Helversen, Mirjam Knörnschild, Frieder Mayer, Martina Nagy, Songs, Scents, and Senses: Sexual Selection in the Greater Sac-Winged Bat, Saccopteryx bilineata, Journal of Mammalogy, Volume 89, Issue 6, 16 December 2008, Pages 1401–1410, https://doi.org/10.1644/08-MAMM-S-060.1",
            created_by=user,
            group=group,
        )

        saccopteryx_calls = [
            "Pup isolation call",
            "Maternal directive call",
            "Echolocation",
            "Bark",
            "Chatter",
            "Screech",
            "Whistle",
            "Courtship song",
            "Territorial song",
        ]

        for call_name in saccopteryx_calls:
            Call.objects.create(species=species, short_name=call_name.strip())

        _add_species_image_by_name(species, "Saccopteryx.png")

        created_species.append(species)

    return created_species


def _add_species_image_by_name(species, image_filename):
    """Helper function to add an image to a species by filename

    Args:
        species: The Species object to add the image to
        image_filename: Name of the image file in data/species_images

    Returns:
        bool: True if image was added successfully, False otherwise
    """
    image_path = os.path.join(get_species_images_path(), image_filename)

    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            species.image.save(image_filename, File(img_file), save=True)
        return True

    return False


def _add_species_image(species, species_data):
    """Helper function to add an image to a species

    Args:
        species: The Species object to add the image to
        species_data: Dictionary containing image information

    Returns:
        bool: True if image was added successfully, False otherwise
    """
    image_path = os.path.join(get_species_images_path(), species_data["image_file"])

    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            species.image.save(species_data["image_file"], File(img_file), save=True)
        return True

    return False


def _add_species_calls(species, species_data, user):
    """Helper function to add calls to a species

    Args:
        species: The Species object to add calls to
        species_data: Dictionary containing call information
        user: The User object that created the species

    Returns:
        bool: True if calls were added successfully, False otherwise
    """
    from battycoda_app.models.organization import Call

    call_path = os.path.join(get_species_images_path(), species_data["call_file"])

    if not os.path.exists(call_path):
        return False

    with open(call_path, "r", encoding="utf-8") as f:
        file_content = f.read()

        for line in file_content.splitlines():
            line = line.strip()
            if not line:
                continue

            if "," in line:
                short_name, long_name = line.split(",", 1)
            elif "|" in line:
                short_name, long_name = line.split("|", 1)
            elif "\t" in line:
                short_name, long_name = line.split("\t", 1)
            else:
                short_name = line
                long_name = ""

            short_name = short_name.strip()
            long_name = long_name.strip()

            Call.objects.create(
                species=species,
                short_name=short_name,
                long_name=long_name if long_name else None,
            )

    return True
