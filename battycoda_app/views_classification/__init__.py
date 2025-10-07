"""Classification views package."""
from .batch_operations import (classify_unclassified_segments_view,
                                create_classification_for_species_view)
from .dashboard import classification_home_view, detection_run_list_view
from .run_creation import (create_detection_run_view,
                            delete_detection_run_view)

__all__ = [
    'classification_home_view',
    'classify_unclassified_segments_view',
    'create_classification_for_species_view',
    'create_detection_run_view',
    'delete_detection_run_view',
    'detection_run_list_view',
]