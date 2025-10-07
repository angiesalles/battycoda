"""Classification tasks package."""
from .dummy_classifier import run_dummy_classifier
from .run_classification import run_call_detection

__all__ = [
    'run_call_detection',
    'run_dummy_classifier',
]
