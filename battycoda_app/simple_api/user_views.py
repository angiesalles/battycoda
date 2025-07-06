"""
User management API views.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .auth import api_key_required


@require_http_methods(["GET"])
@api_key_required
def simple_user_info(request):
    """Get basic user info including API key status"""
    user = request.api_user
    
    return JsonResponse({
        'success': True,
        'user': {
            'username': user.username,
            'email': user.email,
            'group_name': user.profile.group.name if user.profile.group else None,
            'is_group_admin': user.profile.is_current_group_admin,
            'api_key_active': bool(user.profile.api_key)
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def simple_generate_api_key(request):
    """Generate a new API key for the user"""
    user = request.api_user
    new_key = user.profile.generate_api_key()
    
    return JsonResponse({
        'success': True,
        'message': 'New API key generated successfully',
        'api_key': new_key
    })