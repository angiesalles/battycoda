"""
Authentication utilities for Simple API.
"""
from django.http import JsonResponse
from ..models.user import UserProfile


def get_user_from_api_key(api_key):
    """Get user from API key, return None if invalid"""
    if not api_key:
        return None
    try:
        profile = UserProfile.objects.get(api_key=api_key)
        return profile.user
    except UserProfile.DoesNotExist:
        return None


def api_key_required(view_func):
    """Decorator to require valid API key"""
    def wrapper(request, *args, **kwargs):
        # Handle both GET and POST, and handle list values from QueryDict
        api_key = request.GET.get('api_key') or request.POST.get('api_key')
        
        # Django QueryDict.get() returns the last value, but just in case it's a list
        if isinstance(api_key, list):
            api_key = api_key[0] if api_key else None
            
        user = get_user_from_api_key(api_key)
        if not user:
            return JsonResponse({'error': 'Invalid or missing API key'}, status=401)
        request.api_user = user
        return view_func(request, *args, **kwargs)
    return wrapper