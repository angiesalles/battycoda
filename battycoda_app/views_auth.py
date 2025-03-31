
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

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
            messages.error(request, "Please check your login details and try again.")
            # Re-render form with username_or_email to maintain its value
            return render(request, "auth/login.html", {"form": UserLoginForm(), "username_or_email": username_or_email})
    else:
        form = UserLoginForm()

    return render(request, "auth/login.html", {"form": form})


def process_invitation(request, user, invitation_token):
    """Process a group invitation for a user"""
    try:
        invitation = GroupInvitation.objects.get(token=invitation_token)
        if not invitation.is_expired and not invitation.accepted:
            # Add user to group using GroupMembership model
            membership, created = GroupMembership.objects.get_or_create(
                user=user,
                group=invitation.group,
                defaults={"is_admin": False},  # New members aren't admins by default
            )

            # Set the group from the invitation as active
            user.profile.group = invitation.group
            user.profile.save()

            # Mark invitation as accepted
            invitation.accepted = True
            invitation.save()

            # Clear the invitation token from session
            del request.session["invitation_token"]

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

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
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
                    f'Registration successful! You have been added to the group "{invitation.group.name}". Please log in.',
                )
            else:
                messages.success(request, "Registration successful! Please log in.")

            # Send welcome email
            from .email_utils import send_welcome_email
            send_welcome_email(user)

            return redirect("battycoda_app:login")
    else:
        form = UserRegisterForm()

    return render(request, "auth/register.html", {"form": form})

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
        form = UserProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()

            # Update user email if provided
            email = request.POST.get("email")
            if email and email != request.user.email:
                request.user.email = email
                request.user.save()

            messages.success(request, "Profile updated successfully!")
            return redirect("battycoda_app:profile")
    else:
        form = UserProfileForm(instance=profile, user=request.user)

    context = {
        "form": form,
        "user": request.user,
        "profile": profile,
    }

    return render(request, "auth/edit_profile.html", context)

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
        from .models import PasswordResetToken
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
    from .models import PasswordResetToken
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
        username = request.POST.get("username", "")
        
        response = {
            "exists": False,
            "valid": True,
            "message": ""
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
            
        return JsonResponse(response)
        
    return JsonResponse({"error": "Method not allowed"}, status=405)
