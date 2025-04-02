"""
Utility functions for species management.
"""

import os
import time
import traceback

from django.core.files import File

# Set up logging

def available_species():
    """
    Get a list of available default species

    Returns:
        list: List of default species names
    """
    try:
        # Import directly from the default_species module
        from battycoda_app.default_species import DEFAULT_SPECIES

        return [species["name"] for species in DEFAULT_SPECIES]
    except Exception as e:

        return []

def setup_system_species():
    """
    Verify that system-wide species (Eptesicus fuscus and Carollia perspicillata) exist
    This function is a no-op now, as system species are created through migrations
    
    Returns:
        list: List of system Species objects
    """
    from battycoda_app.models.organization import Species
    
    # System species should already be created via migrations,
    # so we just return the existing ones
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
    from battycoda_app.models.organization import Species
    from battycoda_app.models.organization import Call

    # Add a delay to ensure user creation transaction is complete
    time.sleep(1)

    # Get the user's group
    group = user.profile.group
    if not group:
        return []

    created_species = []
    
    # First ensure system species exist
    setup_system_species()

    # Create Saccopteryx bilineata for this user's group
    species_name = "Saccopteryx bilineata"
    
    # Skip if species already exists for this group
    if not Species.objects.filter(name=species_name, group=group).exists():
        # Create the species with its normal name
        species = Species.objects.create(
            name=species_name, 
            description="Saccopteryx bilineata, known as the greater sac-winged bat, is a bat species in the family Emballonuridae.", 
            created_by=user, 
            group=group
        )
        
        # Add call types from Saccopteryx.txt file
        call_file_path = "/app/data/species_images/Saccopteryx.txt"
        
        try:
            with open(call_file_path, "r", encoding="utf-8") as f:
                for line in f:
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
                        
                    Call.objects.create(
                        species=species, 
                        short_name=short_name.strip(), 
                        long_name=long_name.strip() if long_name else None
                    )
        except FileNotFoundError:
            # If file not found, don't create any calls
            pass
            
        # Try to add the species image if it exists
        _add_species_image_by_name(species, "Saccopteryx.jpg")
        
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
    # Use explicit paths for Docker container
    image_path = f"/app/data/species_images/{image_filename}"
    
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                species.image.save(image_filename, File(img_file), save=True)
            return True
        except Exception:
            return False
            
    return False

def _add_species_image(species, species_data):
    """Helper function to add an image to a species

    Args:
        species: The Species object to add the image to
        species_data: Dictionary containing image information

    Returns:
        bool: True if image was added successfully, False otherwise
    """
    # Use explicit paths for Docker container
    image_paths = [
        f"/app/data/species_images/{species_data['image_file']}",
    ]

    image_found = False
    for image_path in image_paths:

        if os.path.exists(image_path):

            with open(image_path, "rb") as img_file:
                species.image.save(species_data["image_file"], File(img_file), save=True)

            image_found = True
            break

    return image_found

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

    # Parse call types from the text file
    call_paths = [
        f"/app/data/species_images/{species_data['call_file']}",
    ]

    call_file_found = False
    for call_path in call_paths:

        if os.path.exists(call_path):

            call_count = 0

            with open(call_path, "r", encoding="utf-8") as f:
                file_content = f.read()

                # Process each line
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
                        # If no separator, use whole line as short_name and leave long_name empty
                        short_name = line
                        long_name = ""

                    short_name = short_name.strip()
                    long_name = long_name.strip()

                    # Create the call
                    Call.objects.create(
                        species=species, short_name=short_name, long_name=long_name if long_name else None
                    )
                    call_count += 1

            call_file_found = True
            break

    return call_file_found
