"""Login and logout views for authentication."""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from ..forms import UserLoginForm
from ..models.user import GroupInvitation


def process_invitation(request, user, invitation_token):
    """Process a group invitation for a user"""
    try:
        invitation = GroupInvitation.objects.get(token=invitation_token)
        if not invitation.is_expired and not invitation.accepted:
            invitation.accepted = True
            invitation.save()

            del request.session["invitation_token"]

            from ..models.notification import UserNotification

            dashboard_link = reverse("battycoda_app:index")

            UserNotification.add_notification(
                user=user,
                title="Welcome to BattyCoda!",
                message=(
                    f'You have been added to the group "{invitation.group.name}". '
                    f"You can explore existing projects and content created by your group."
                ),
                notification_type="system",
                icon="s7-like",
                link=dashboard_link,
            )

            messages.success(request, f'You have been added to the group "{invitation.group.name}".')
    except GroupInvitation.DoesNotExist:
        pass


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect("battycoda_app:index")

    invitation_token = request.session.get("invitation_token")

    if request.method == "POST":
        username_or_email = request.POST.get("username")
        password = request.POST.get("password")

        user = None

        user = authenticate(username=username_or_email, password=password)

        if not user and "@" in username_or_email:
            email_user = User.objects.filter(email=username_or_email).first()
            if email_user:
                user = authenticate(username=email_user.username, password=password)

        if user:
            login(request, user)

            request.session.set_expiry(31536000)

            user.last_login = timezone.now()
            user.save()

            if invitation_token:
                process_invitation(request, user, invitation_token)

            next_page = request.GET.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = reverse("battycoda_app:index")

            return redirect(next_page)
        else:
            login_error = "Invalid login credentials. Please check your username/email and password and try again."
            return render(
                request,
                "auth/login.html",
                {"form": UserLoginForm(), "username_or_email": username_or_email, "login_error": login_error},
            )
    else:
        form = UserLoginForm()

    return render(request, "auth/login.html", {"form": form})


def login_with_token(request, token):
    """Handle user login via one-time token link"""
    from ..models import LoginCode

    try:
        login_code = LoginCode.objects.get(token=token, used=False, expires_at__gt=timezone.now())

        user = login_code.user
        login(request, user)

        request.session.set_expiry(31536000)

        login_code.used = True
        login_code.save()

        user.last_login = timezone.now()
        user.save()

        invitation_token = request.session.get("invitation_token")
        if invitation_token:
            process_invitation(request, user, invitation_token)

        messages.success(request, "You have been logged in successfully.")

        next_page = request.GET.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = reverse("battycoda_app:index")

        return redirect(next_page)

    except LoginCode.DoesNotExist:
        messages.error(request, "Invalid or expired login link. Please request a new login code.")
        return redirect("battycoda_app:login")


@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("battycoda_app:login")
