"""User registration views."""
import random

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.utils import timezone

from ..forms import UserRegisterForm
from ..models.user import GroupInvitation, GroupMembership
from ..utils_modules.validation import safe_int
from .login import process_invitation


def register_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect("battycoda_app:index")

    invitation_token = request.session.get("invitation_token")
    invitation = None
    if invitation_token:
        try:
            invitation = GroupInvitation.objects.get(token=invitation_token)
            initial_email = invitation.email
        except GroupInvitation.DoesNotExist:
            invitation = None
            initial_email = ""
    else:
        initial_email = ""

    if request.method == "POST":
        captcha_num1 = safe_int(request.POST.get('captcha_num1'), default=0)
        captcha_num2 = safe_int(request.POST.get('captcha_num2'), default=0)

        form = UserRegisterForm(request.POST, captcha_num1=captcha_num1, captcha_num2=captcha_num2)
        if form.is_valid():
            user = form.save()

            if invitation and not invitation.is_expired and not invitation.accepted:
                profile = user.profile

                membership, created = GroupMembership.objects.get_or_create(
                    user=user,
                    group=invitation.group,
                    defaults={"is_admin": False},
                )

                profile.group = invitation.group
                profile.save()

                invitation.accepted = True
                invitation.save()

                if "invitation_token" in request.session:
                    del request.session["invitation_token"]

                messages.success(
                    request,
                    f'Registration successful! You have been added to the group "{invitation.group.name}".',
                )
            else:
                messages.success(request, "Registration successful!")

            from ..email_utils import send_welcome_email
            send_welcome_email(user)

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)

                request.session.set_expiry(31536000)

                user.last_login = timezone.now()
                user.save()

                return redirect("battycoda_app:index")

            return redirect("battycoda_app:login")
        else:
            captcha_num1 = random.randint(1, 20)
            captcha_num2 = random.randint(1, 20)
    else:
        captcha_num1 = random.randint(1, 20)
        captcha_num2 = random.randint(1, 20)
        form = UserRegisterForm()

    context = {
        "form": form,
        "captcha_num1": captcha_num1,
        "captcha_num2": captcha_num2,
        "initial_email": initial_email,
        "invitation": invitation,
    }
    return render(request, "auth/register.html", context)
