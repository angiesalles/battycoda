"""
Backward compatibility shim for classification tasks.

This module provides backward compatibility by importing tasks from the new
classification package structure.
"""
from .classification import run_call_detection, run_dummy_classifier

__all__ = [
    'run_call_detection',
    'run_dummy_classifier',
]
