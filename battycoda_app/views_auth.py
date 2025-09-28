
import json
import random

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import UserLoginForm, UserProfileForm, UserRegisterForm
from .models.user import GroupInvitation, GroupMembership, UserProfile


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect("battycoda_app:index")

    # Check if there's an invitation token in the session
    invitation_token = request.session.get("invitation_token")

    if request.method == "POST":
        # Get credentials from form
        username_or_email = request.POST.get("username")
        password = request.POST.get("password")
        
        user = None
        
        # Try to authenticate with username
        user = authenticate(username=username_or_email, password=password)
        
        # If that fails and input has @ character, try as email
        if not user and '@' in username_or_email:
            # Find user by email first
            email_user = User.objects.filter(email=username_or_email).first()
            if email_user:
                # Then authenticate with the user's username
                user = authenticate(username=email_user.username, password=password)
        
        if user:
            login(request, user)
            
            # Set session to last for 1 year (365 days)
            request.session.set_expiry(31536000)  # 1 year in seconds

            # Update last login
            user.last_login = timezone.now()
            user.save()

            # Process invitation if there is one
            if invitation_token:
                process_invitation(request, user, invitation_token)

            # Check for next parameter
            next_page = request.GET.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = reverse("battycoda_app:index")

            return redirect(next_page)
        else:
            # Special case for login errors - display in form instead of toast
            login_error = "Invalid login credentials. Please check your username/email and password and try again."
            # Re-render form with username_or_email to maintain its value and the error message
            return render(request, "auth/login.html", {
                "form": UserLoginForm(), 
                "username_or_email": username_or_email,
                "login_error": login_error
            })
    else:
        form = UserLoginForm()

    return render(request, "auth/login.html", {"form": form})


def process_invitation(request, user, invitation_token):
    """Process a group invitation for a user"""
    try:
        invitation = GroupInvitation.objects.get(token=invitation_token)
        if not invitation.is_expired and not invitation.accepted:
            # The user was already added to the group in the create_user_profile signal
            # Mark invitation as accepted
            invitation.accepted = True
            invitation.save()

            # Clear the invitation token from session
            del request.session["invitation_token"]

            # Create a welcome notification specifically for invited users
            from .models.notification import UserNotification
            from django.urls import reverse
            
            dashboard_link = reverse('battycoda_app:index')
            
            UserNotification.add_notification(
                user=user,
                title="Welcome to BattyCoda!",
                message=(
                    f'You have been added to the group "{invitation.group.name}". '
                    f'You can explore existing projects and content created by your group.'
                ),
                notification_type="system",
                icon="s7-like",
                link=dashboard_link
            )

            messages.success(request, f'You have been added to the group "{invitation.group.name}".')
    except GroupInvitation.DoesNotExist:
        # If invitation doesn't exist, just continue with login
        pass


def login_with_token(request, token):
    """Handle user login via one-time token link"""
    from .models import LoginCode
    
    try:
        # Try to find a valid login code with the given token
        login_code = LoginCode.objects.get(
            token=token,
            used=False,
            expires_at__gt=timezone.now()
        )
        
        # Valid token found - log the user in
        user = login_code.user
        login(request, user)
        
        # Set session to last for 1 year (365 days)
        request.session.set_expiry(31536000)  # 1 year in seconds
        
        # Mark the code as used
        login_code.used = True
        login_code.save()
        
        # Update last login time
        user.last_login = timezone.now()
        user.save()
        
        # Check for invitation token in session
        invitation_token = request.session.get("invitation_token")
        if invitation_token:
            process_invitation(request, user, invitation_token)
        
        messages.success(request, "You have been logged in successfully.")
        
        # Redirect to the appropriate page
        next_page = request.GET.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = reverse("battycoda_app:index")
            
        return redirect(next_page)
        
    except LoginCode.DoesNotExist:
        # Invalid or expired token
        messages.error(request, "Invalid or expired login link. Please request a new login code.")
        return redirect("battycoda_app:login")

def register_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect("battycoda_app:index")

    # Check if there's an invitation token in the session
    invitation_token = request.session.get("invitation_token")
    invitation = None
    if invitation_token:
        try:
            invitation = GroupInvitation.objects.get(token=invitation_token)
            # Pre-fill email if it matches the invitation
            initial_email = invitation.email
        except GroupInvitation.DoesNotExist:
            invitation = None
            initial_email = ""
    else:
        initial_email = ""

    # Generate or get CAPTCHA values
    if request.method == "POST":
        # Get CAPTCHA values from POST data (hidden fields)
        captcha_num1 = int(request.POST.get('captcha_num1', 0))
        captcha_num2 = int(request.POST.get('captcha_num2', 0))
        
        # Pass CAPTCHA values to form for validation
        form = UserRegisterForm(request.POST, captcha_num1=captcha_num1, captcha_num2=captcha_num2)
        if form.is_valid():
            user = form.save()

            # If there's a valid invitation, process it
            if invitation and not invitation.is_expired and not invitation.accepted:
                # Get the user's profile
                profile = user.profile

                # Create group membership
                membership, created = GroupMembership.objects.get_or_create(
                    user=user,
                    group=invitation.group,
                    defaults={"is_admin": False},  # New members aren't admins by default
                )

                # Set the group from the invitation as active
                profile.group = invitation.group
                profile.save()

                # Mark invitation as accepted
                invitation.accepted = True
                invitation.save()

                # Clear the invitation token from session
                if "invitation_token" in request.session:
                    del request.session["invitation_token"]

                messages.success(
                    request,
                    f'Registration successful! You have been added to the group "{invitation.group.name}".',
                )
            else:
                messages.success(request, "Registration successful!")

            # Send welcome email
            from .email_utils import send_welcome_email
            send_welcome_email(user)
            
            # Log the user in automatically
            # Use the username from the form to authenticate
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')  # The first password field
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                
                # Set session to last for 1 year (365 days)
                request.session.set_expiry(31536000)  # 1 year in seconds
                
                # Update last login time
                user.last_login = timezone.now()
                user.save()
                
                # Redirect to dashboard
                return redirect("battycoda_app:index")
                
            # In case authentication fails (very unlikely), redirect to login page
            return redirect("battycoda_app:login")
        else:
            # Form validation failed - regenerate CAPTCHA for security
            captcha_num1 = random.randint(1, 20)
            captcha_num2 = random.randint(1, 20)
    else:
        # Generate new CAPTCHA values for GET request
        captcha_num1 = random.randint(1, 20)
        captcha_num2 = random.randint(1, 20)
        form = UserRegisterForm()

    # Pass CAPTCHA values to template
    context = {
        "form": form,
        "captcha_num1": captcha_num1,
        "captcha_num2": captcha_num2,
        "initial_email": initial_email,
        "invitation": invitation,
    }
    return render(request, "auth/register.html", context)

@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("battycoda_app:login")

@login_required
def profile_view(request):
    """Display user profile"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Get all groups the user is a member of through GroupMembership
    group_memberships = GroupMembership.objects.filter(user=request.user).select_related("group")

    context = {
        "user": request.user,
        "profile": profile,
        "group_memberships": group_memberships,
        "active_group": profile.group,  # The currently active group
    }

    return render(request, "auth/profile.html", context)

@login_required
def edit_profile_view(request):
    """Edit user profile settings"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Check if the user is removing their profile image
        if request.POST.get("remove_profile_image") == "1" and profile.profile_image:
            # Delete the image file from storage
            profile.profile_image.delete(save=False)
            # Clear the profile_image field
            profile.profile_image = None
            profile.save()
            messages.success(request, "Profile image removed successfully!")
            return redirect("battycoda_app:edit_profile")
            
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            # Handle profile image upload - using a simpler approach
            if 'profile_image' in request.FILES:
                # If there's an existing image, delete it first
                if profile.profile_image:
                    profile.profile_image.delete(save=False)
                
                # Assign the uploaded file directly
                profile.profile_image = request.FILES['profile_image']
                
            # Save the form
            form.save()

            # Update user email if provided
            email = request.POST.get("email")
            if email and email != request.user.email:
                request.user.email = email
                request.user.save()

            messages.success(request, "Profile updated successfully!")
            return redirect("battycoda_app:edit_profile")
    else:
        form = UserProfileForm(instance=profile, user=request.user)

    import random
    context = {
        "form": form,
        "user": request.user,
        "profile": profile,
        "random": random.randint(1, 1000000)  # To prevent image caching
    }

    return render(request, "auth/edit_profile.html", context)


@login_required
@require_POST
def generate_api_key_view(request):
    """Generate a new API key for the user"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    new_key = profile.generate_api_key()
    
    messages.success(request, f"New API key generated: {new_key}")
    return redirect("battycoda_app:edit_profile")


def password_reset_request(request):
    """Handle password reset request"""
    if request.method == "POST":
        identifier = request.POST.get("identifier")

        # Check if identifier looks like an email
        user = None
        if '@' in identifier:
            # Treat as email
            user = User.objects.filter(email=identifier).first()
        else:
            # Treat as username
            user = User.objects.filter(username=identifier).first()
            
            # Check if user has an email
            if user and not user.email:
                user = None
        
        if not user:
            # To avoid revealing whether a username or email exists,
            # use a generic message
            messages.success(request, 
                            "If an account exists with the provided information, " 
                            "password reset instructions will be sent to the associated email address.")
            return redirect("battycoda_app:login")

        # Generate password reset token
        from .models.user import PasswordResetToken
        from .email_utils import send_password_reset_email
        
        # Create new password reset token
        token_obj = PasswordResetToken.generate_token(user)
        
        # Send the reset link via email
        success = send_password_reset_email(
            user=user,
            token=token_obj.token,
            expires_at=token_obj.expires_at
        )
        
        # Always show the same message whether the email was sent successfully or not
        # This prevents enumeration attacks
        messages.success(request, 
                        "If an account exists with the provided information, " 
                        "password reset instructions will be sent to the associated email address.")
        return redirect("battycoda_app:login")

    return render(request, "auth/forgot_password.html")

def password_reset(request, token):
    """Reset password with token"""
    from .models.user import PasswordResetToken
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    
    # Verify token
    try:
        token_obj = PasswordResetToken.objects.get(
            token=token,
            used=False,
            expires_at__gt=timezone.now()
        )
        user = token_obj.user
    except PasswordResetToken.DoesNotExist:
        messages.error(request, "Invalid or expired password reset link. Please request a new password reset.")
        return redirect("battycoda_app:password_reset_request")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "auth/reset_password.html", {"token": token})

        # Validate password using Django's built-in validation
        try:
            validate_password(password, user)
            
            # Update user password
            user.set_password(password)
            user.save()
            
            # Mark token as used
            token_obj.used = True
            token_obj.save()

            messages.success(request, "Password has been reset successfully. Please log in.")
            return redirect("battycoda_app:login")
            
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, "auth/reset_password.html", {"token": token})

    return render(request, "auth/reset_password.html", {"token": token})

def request_login_code(request):
    """Request one-time login code"""
    if request.method == "POST":
        identifier = request.POST.get("username")
        
        user = None
        # Check if identifier looks like an email
        if '@' in identifier:
            # Try to find user by email
            user = User.objects.filter(email=identifier).first()
        else:
            # Try to find user by username
            user = User.objects.filter(username=identifier).first()
            
        # Process only if we found a valid user with an email
        if user and user.email:
            # Generate the login code
            from .models import LoginCode
            from .email_utils import send_login_code_email
            
            # Create new login code
            login_code = LoginCode.generate_code(user)
            
            # Send the code via email
            send_login_code_email(
                user=user,
                code=login_code.code,
                token=login_code.token,
                expires_at=login_code.expires_at
            )
        
        # Always redirect to enter code page with the provided identifier
        # This avoids revealing whether a user exists or not
        messages.success(request, "If an account exists with that username or email, a login code has been sent.")
        return redirect("battycoda_app:enter_login_code", username=identifier)

    return render(request, "auth/request_login_code.html")

def enter_login_code(request, username):
    """Process one-time login code"""
    if request.method == "POST":
        login_code = request.POST.get("login_code")
        identifier = username  # Use the username passed in the URL
        
        user = None
        # Check if the identifier is an email
        if '@' in identifier:
            user = User.objects.filter(email=identifier).first()
        else:
            user = User.objects.filter(username=identifier).first()
            
        if not user:
            # To avoid revealing whether a user exists, use a generic error message
            messages.error(request, "Invalid or expired login code.")
            return render(request, "auth/enter_login_code.html", {"username": identifier})
        
        # Try to find a valid login code
        from .models import LoginCode
        try:
            code_obj = LoginCode.objects.get(
                user=user,
                code=login_code,
                used=False,
                expires_at__gt=timezone.now()
            )
            
            # Valid code found - log the user in
            login(request, user)
            
            # Set session to last for 1 year (365 days)
            request.session.set_expiry(31536000)  # 1 year in seconds
            
            # Mark the code as used
            code_obj.used = True
            code_obj.save()
            
            # Update last login time
            user.last_login = timezone.now()
            user.save()
            
            messages.success(request, "Login successful with one-time code.")
            
            # Process invitation if there is one
            invitation_token = request.session.get("invitation_token")
            if invitation_token:
                process_invitation(request, user, invitation_token)
            
            # Redirect to the appropriate page
            next_page = request.GET.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = reverse("battycoda_app:index")
                
            return redirect(next_page)
        except LoginCode.DoesNotExist:
            # Invalid or expired code
            messages.error(request, "Invalid or expired login code.")
            return render(request, "auth/enter_login_code.html", {"username": identifier})
    
    return render(request, "auth/enter_login_code.html", {"username": username})


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
            # Handle both standard form POST and application/json content type
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                username = data.get("username", "")
                email = data.get("email", "")
            else:
                username = request.POST.get("username", "")
                email = request.POST.get("email", "")
            
            response = {
                "exists": False,
                "valid": True,
                "message": "",
                "email_exists": False
            }
            
            # Check for empty username
            if not username:
                response["valid"] = False
                response["message"] = "Username cannot be empty."
                return JsonResponse(response)
            
            # Check for @ character
            if '@' in username:
                response["valid"] = False
                response["message"] = "Username cannot contain the @ symbol."
                return JsonResponse(response)
                
            # Check for invalid characters (only allow letters, numbers, and ._-)
            import re
            if not re.match(r'^[\w.-]+$', username):
                response["valid"] = False
                response["message"] = "Username can only contain letters, numbers, and the characters ._-"
                return JsonResponse(response)
                
            # Check if username exists
            user_exists = User.objects.filter(username=username).exists()
            if user_exists:
                response["exists"] = True
                response["message"] = "This username is already taken."
                
            # Check if email exists (if provided)
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
            # Handle both standard form POST and application/json content type
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                email = data.get("email", "")
            else:
                email = request.POST.get("email", "")
            
            response = {
                "exists": False,
                "message": ""
            }
            
            # Check for empty email
            if not email:
                response["exists"] = False
                return JsonResponse(response)
            
            # Check if email exists
            email_exists = User.objects.filter(email=email).exists()
            if email_exists:
                response["exists"] = True
                response["message"] = "This email is already in use."
                
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
    return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
@require_POST
def update_theme_preference(request):
    """Update user theme preference via AJAX"""
    try:
        data = json.loads(request.body)
        theme = data.get('theme')
        
        # Validate theme name from choices in UserProfile
        valid_themes = dict(UserProfile.THEME_CHOICES).keys()
        if theme not in valid_themes:
            return JsonResponse({'status': 'error', 'message': 'Invalid theme name'}, status=400)
        
        # Update user profile theme preference
        profile = request.user.profile
        profile.theme = theme
        profile.save(update_fields=['theme'])
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def update_profile_ajax(request):
    """Handle profile updates via AJAX for email and profile image"""
    try:
        profile = request.user.profile
        action = request.POST.get('action')
        
        if action == 'update_email':
            # Update email address
            email = request.POST.get('email')
            if not email:
                return JsonResponse({'success': False, 'message': 'Email is required'})
            
            # Validate email format
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'success': False, 'message': 'Please enter a valid email address'})
            
            # Update user's email
            request.user.email = email
            request.user.save(update_fields=['email'])
            
            return JsonResponse({
                'success': True,
                'message': 'Email updated successfully'
            })
            
        elif action == 'upload_image':
            # Process profile image upload
            if 'profile_image' not in request.FILES:
                return JsonResponse({'success': False, 'message': 'No image file provided'})
            
            # Get the uploaded file
            image_file = request.FILES['profile_image']
            
            # Validate file type
            import imghdr
            image_type = imghdr.what(image_file)
            if image_type not in ['jpeg', 'png', 'gif']:
                return JsonResponse({'success': False, 'message': 'Invalid image format. Please upload a JPEG, PNG, or GIF.'})
            
            # Delete existing image if present
            if profile.profile_image:
                profile.profile_image.delete(save=False)
            
            # Set the new profile image
            profile.profile_image = image_file
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile image uploaded successfully',
                'image_url': profile.profile_image.url,
                'has_image': bool(profile.profile_image)
            })
            
        elif action == 'remove_image':
            # Remove profile image
            if not profile.profile_image:
                return JsonResponse({'success': False, 'message': 'No profile image to remove'})
            
            # Delete the image
            profile.profile_image.delete(save=False)
            profile.profile_image = None
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile image removed successfully',
                'has_image': False
            })
            
        elif action == 'update_management_features':
            # Update management features flag
            enabled = request.POST.get('enabled') == 'true'
            profile.management_features_enabled = enabled
            profile.save(update_fields=['management_features_enabled'])
            
            return JsonResponse({
                'success': True,
                'message': f'Management features {"enabled" if enabled else "disabled"} successfully',
                'enabled': enabled
            })
            
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action'})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)


@login_required
def hijack_user_view(request, user_id):
    """
    Custom view for hijacking a user.
    This is a simplified implementation for admin use that doesn't rely on django-hijack.
    """
    # Only allow superusers to hijack other users
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to impersonate users.")
        return redirect('/')
    
    # Get the user to hijack
    user = get_object_or_404(User, id=user_id)
    
    # Store the original user ID in the session
    if 'hijack_history' not in request.session:
        request.session['hijack_history'] = []
    
    # Add current user ID to the history
    request.session['hijack_history'].append(request.user.id)
    
    # Log in as the target user
    login(request, user)
    
    messages.success(
        request, 
        f"You are now impersonating {user.username}. Use the release button at the top to return to your account."
    )
    
    return redirect('/')


@login_required
def release_hijacked_user_view(request):
    """
    Custom view for releasing a hijacked user.
    This is a simplified implementation for admin use that doesn't rely on django-hijack.
    """
    # Check if there's a hijack history in the session
    if 'hijack_history' not in request.session or not request.session['hijack_history']:
        messages.error(request, "No user impersonation in progress.")
        return redirect('/')
    
    # Get the original user ID
    original_user_id = request.session['hijack_history'].pop()
    
    # Clean up the session
    if not request.session['hijack_history']:
        del request.session['hijack_history']
    
    # Get the original user
    original_user = get_object_or_404(User, id=original_user_id)
    
    # Log in as the original user
    login(request, original_user)
    
    messages.success(request, "You have been returned to your account.")
    
    return redirect('/admin/auth/user/')
