"""User profile management views."""

import json
import random

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import UserProfileForm
from ..models.user import UserProfile


@login_required
def edit_profile_view(request):
    """Edit user profile settings"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        if request.POST.get("remove_profile_image") == "1" and profile.profile_image:
            profile.profile_image.delete(save=False)
            profile.profile_image = None
            profile.save()
            messages.success(request, "Profile image removed successfully!")
            return redirect("battycoda_app:edit_profile")

        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            if "profile_image" in request.FILES:
                if profile.profile_image:
                    profile.profile_image.delete(save=False)

                profile.profile_image = request.FILES["profile_image"]

            form.save()

            email = request.POST.get("email")
            if email and email != request.user.email:
                request.user.email = email
                request.user.save()

            messages.success(request, "Profile updated successfully!")
            return redirect("battycoda_app:edit_profile")
    else:
        form = UserProfileForm(instance=profile, user=request.user)

    context = {"form": form, "user": request.user, "profile": profile, "random": random.randint(1, 1000000)}

    return render(request, "auth/edit_profile.html", context)


@login_required
@require_POST
def generate_api_key_view(request):
    """Generate a new API key for the user"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    new_key = profile.generate_api_key()

    messages.success(request, f"New API key generated: {new_key}")
    return redirect("battycoda_app:edit_profile")


@login_required
@require_POST
def update_theme_preference(request):
    """Update user theme preference via AJAX"""
    try:
        data = json.loads(request.body)
        theme = data.get("theme")

        valid_themes = dict(UserProfile.THEME_CHOICES).keys()
        if theme not in valid_themes:
            return JsonResponse({"success": False, "error": "Invalid theme name"}, status=400)

        profile = request.user.profile
        profile.theme = theme
        profile.save(update_fields=["theme"])

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def update_profile_ajax(request):
    """Handle profile updates via AJAX for email and profile image"""
    try:
        profile = request.user.profile
        action = request.POST.get("action")

        if action == "update_email":
            email = request.POST.get("email")
            if not email:
                return JsonResponse({"success": False, "error": "Email is required"})

            from django.core.exceptions import ValidationError
            from django.core.validators import validate_email

            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({"success": False, "error": "Please enter a valid email address"})

            request.user.email = email
            request.user.save(update_fields=["email"])

            return JsonResponse({"success": True, "message": "Email updated successfully"})

        elif action == "upload_image":
            if "profile_image" not in request.FILES:
                return JsonResponse({"success": False, "error": "No image file provided"})

            image_file = request.FILES["profile_image"]

            # Check image type by magic bytes (imghdr is deprecated in Python 3.11+)
            header = image_file.read(8)
            image_file.seek(0)  # Reset file position for saving
            is_valid_image = (
                header[:3] == b"\xff\xd8\xff"  # JPEG
                or header[:8] == b"\x89PNG\r\n\x1a\n"  # PNG
                or header[:6] in (b"GIF87a", b"GIF89a")  # GIF
            )
            if not is_valid_image:
                return JsonResponse(
                    {"success": False, "error": "Invalid image format. Please upload a JPEG, PNG, or GIF."}
                )

            if profile.profile_image:
                profile.profile_image.delete(save=False)

            profile.profile_image = image_file
            profile.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Profile image uploaded successfully",
                    "image_url": profile.profile_image.url,
                    "has_image": bool(profile.profile_image),
                }
            )

        elif action == "remove_image":
            if not profile.profile_image:
                return JsonResponse({"success": False, "error": "No profile image to remove"})

            profile.profile_image.delete(save=False)
            profile.profile_image = None
            profile.save()

            return JsonResponse({"success": True, "message": "Profile image removed successfully", "has_image": False})

        elif action == "update_management_features":
            enabled = request.POST.get("enabled") == "true"
            profile.management_features_enabled = enabled
            profile.save(update_fields=["management_features_enabled"])

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Management features {'enabled' if enabled else 'disabled'} successfully",
                    "enabled": enabled,
                }
            )

        else:
            return JsonResponse({"success": False, "error": "Invalid action"})

    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse({"success": False, "error": f"An error occurred: {str(e)}"}, status=500)


@login_required
def hijack_user_view(request, user_id):
    """Custom view for hijacking a user."""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to impersonate users.")
        return redirect("/")

    user = get_object_or_404(User, id=user_id)

    if "hijack_history" not in request.session:
        request.session["hijack_history"] = []

    request.session["hijack_history"].append(request.user.id)

    login(request, user)

    messages.success(
        request,
        f"You are now impersonating {user.username}. Use the release button at the top to return to your account.",
    )

    return redirect("/")


@login_required
def release_hijacked_user_view(request):
    """Custom view for releasing a hijacked user."""
    if "hijack_history" not in request.session or not request.session["hijack_history"]:
        messages.error(request, "No user impersonation in progress.")
        return redirect("/")

    original_user_id = request.session["hijack_history"].pop()

    if not request.session["hijack_history"]:
        del request.session["hijack_history"]

    original_user = get_object_or_404(User, id=original_user_id)

    login(request, original_user)

    messages.success(request, "You have been returned to your account.")

    return redirect("/admin/auth/user/")
