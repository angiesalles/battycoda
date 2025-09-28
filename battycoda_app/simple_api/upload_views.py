"""
File upload API views.
Legacy wrapper for backward compatibility.
"""
# Import the split functionality
from .recording_upload import upload_recording

# Keep the old function name for backward compatibility
simple_upload_recording = upload_recording