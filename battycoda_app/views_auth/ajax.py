"""AJAX endpoints for authentication."""

import json
import re

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def check_username(request):
    """
    AJAX endpoint to check if a username is valid and available
    Returns:
        - exists: True/False if the username exists
        - valid: True/False if the username is valid format
        - message: Error message if any
    """
    if request.method == "POST":
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
                username = data.get("username", "")
                email = data.get("email", "")
            else:
                username = request.POST.get("username", "")
                email = request.POST.get("email", "")

            response = {"exists": False, "valid": True, "message": "", "email_exists": False}

            if not username:
                response["valid"] = False
                response["message"] = "Username cannot be empty."
                return JsonResponse(response)

            if "@" in username:
                response["valid"] = False
                response["message"] = "Username cannot contain the @ symbol."
                return JsonResponse(response)

            if not re.match(r"^[\w.-]+$", username):
                response["valid"] = False
                response["message"] = "Username can only contain letters, numbers, and the characters ._-"
                return JsonResponse(response)

            user_exists = User.objects.filter(username=username).exists()
            if user_exists:
                response["exists"] = True
                response["message"] = "This username is already taken."

            if email:
                email_exists = User.objects.filter(email=email).exists()
                if email_exists:
                    response["email_exists"] = True
                    response["email_message"] = "This email is already in use."

            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def check_email(request):
    """
    AJAX endpoint to check if an email is already in use
    Returns:
        - exists: True/False if the email exists
        - message: Error message if any
    """
    if request.method == "POST":
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
                email = data.get("email", "")
            else:
                email = request.POST.get("email", "")

            response = {"exists": False, "message": ""}

            if not email:
                response["exists"] = False
                return JsonResponse(response)

            email_exists = User.objects.filter(email=email).exists()
            if email_exists:
                response["exists"] = True
                response["message"] = "This email is already in use."

            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)
