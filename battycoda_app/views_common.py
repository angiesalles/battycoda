"""
Common imports and utilities for views modules.

This module re-exports common Django imports and app models for use in view modules.
Files can use `from .views_common import *` to get all common imports.
"""

import mimetypes
import os
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import RecordingForm
from .models import Recording, Segment
from .models.user import UserProfile

# Default chunk size for streaming (1MB)
CHUNK_SIZE = 1024 * 1024

# Explicitly export all names for `from .views_common import *`
__all__ = [
    # Standard library
    "mimetypes",
    "os",
    "re",
    # Django
    "messages",
    "login_required",
    "Http404",
    "JsonResponse",
    "StreamingHttpResponse",
    "get_object_or_404",
    "redirect",
    "render",
    "reverse",
    # App models and forms
    "RecordingForm",
    "Recording",
    "Segment",
    "UserProfile",
    # Constants
    "CHUNK_SIZE",
]
