"""Password reset and login code views."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .login import process_invitation


def password_reset_request(request):
    """Handle password reset request"""
    if request.method == "POST":
        identifier = request.POST.get("identifier")

        user = None
        if "@" in identifier:
            user = User.objects.filter(email=identifier).first()
        else:
            user = User.objects.filter(username=identifier).first()

            if user and not user.email:
                user = None

        if not user:
            messages.success(
                request,
                "If an account exists with the provided information, "
                "password reset instructions will be sent to the associated email address.",
            )
            return redirect("battycoda_app:login")

        from ..models.user import PasswordResetToken
        from ..user_emails import send_password_reset_email

        token_obj = PasswordResetToken.generate_token(user)

        send_password_reset_email(user=user, token=token_obj.token, expires_at=token_obj.expires_at)

        messages.success(
            request,
            "If an account exists with the provided information, "
            "password reset instructions will be sent to the associated email address.",
        )
        return redirect("battycoda_app:login")

    return render(request, "auth/forgot_password.html")


def password_reset(request, token):
    """Reset password with token"""
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError

    from ..models.user import PasswordResetToken

    try:
        token_obj = PasswordResetToken.objects.get(token=token, used=False, expires_at__gt=timezone.now())
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

        try:
            validate_password(password, user)

            user.set_password(password)
            user.save()

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
        if "@" in identifier:
            user = User.objects.filter(email=identifier).first()
        else:
            user = User.objects.filter(username=identifier).first()

        if user and user.email:
            from ..models import LoginCode
            from ..user_emails import send_login_code_email

            login_code = LoginCode.generate_code(user)

            send_login_code_email(
                user=user, code=login_code.code, token=login_code.token, expires_at=login_code.expires_at
            )

        messages.success(request, "If an account exists with that username or email, a login code has been sent.")
        return redirect("battycoda_app:enter_login_code", username=identifier)

    return render(request, "auth/request_login_code.html")


def enter_login_code(request, username):
    """Process one-time login code"""
    if request.method == "POST":
        login_code = request.POST.get("login_code")
        identifier = username

        user = None
        if "@" in identifier:
            user = User.objects.filter(email=identifier).first()
        else:
            user = User.objects.filter(username=identifier).first()

        if not user:
            messages.error(request, "Invalid or expired login code.")
            return render(request, "auth/enter_login_code.html", {"username": identifier})

        from ..models import LoginCode

        try:
            code_obj = LoginCode.objects.get(user=user, code=login_code, used=False, expires_at__gt=timezone.now())

            login(request, user)

            request.session.set_expiry(31536000)

            code_obj.used = True
            code_obj.save()

            user.last_login = timezone.now()
            user.save()

            messages.success(request, "Login successful with one-time code.")

            invitation_token = request.session.get("invitation_token")
            if invitation_token:
                process_invitation(request, user, invitation_token)

            next_page = request.GET.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = reverse("battycoda_app:index")

            return redirect(next_page)
        except LoginCode.DoesNotExist:
            messages.error(request, "Invalid or expired login code.")
            return render(request, "auth/enter_login_code.html", {"username": identifier})

    return render(request, "auth/enter_login_code.html", {"username": username})
