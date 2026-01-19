from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import GroupForm
from .models.organization import Project, Species
from .models.task import TaskBatch
from .models.user import Group, GroupMembership


def _require_group_admin(request, group):
    """Check if user is admin of the specified group.

    Returns (is_admin, redirect_response) tuple.
    If user is admin, returns (True, None).
    If not, returns (False, redirect_response) with error message set.
    """
    if not request.user.profile.is_admin_of_group(group):
        messages.error(request, "You do not have permission to perform this action.")
        return False, redirect("battycoda_app:group_list")
    return True, None


def _handle_add_member(request, group):
    """Handle adding a user to a group."""
    user_id = request.POST.get("user_id")
    if not user_id:
        return

    user = get_object_or_404(User, id=user_id)
    GroupMembership.objects.get_or_create(user=user, group=group, defaults={"is_admin": False})

    # Set as active group if user doesn't have one
    if not user.profile.group:
        user.profile.group = group
        user.profile.save()

    messages.success(request, f"User {user.username} added to the group.")


def _handle_remove_member(request, group):
    """Handle removing a user from a group.

    Returns redirect response if action should be aborted, None otherwise.
    """
    user_id = request.POST.get("user_id")
    if not user_id:
        return None

    user = get_object_or_404(User, id=user_id)

    can_remove, error_msg = group.can_remove_member(user)
    if not can_remove:
        messages.error(request, error_msg)
        return redirect("battycoda_app:manage_group_members", group_id=group.id)

    GroupMembership.objects.filter(user=user, group=group).delete()

    # Clear active group if this was it
    if user.profile.group == group:
        user.profile.group = None
        user.profile.save()

    messages.success(request, f"User {user.username} removed from the group.")
    return None


def _handle_toggle_admin(request, group):
    """Handle toggling admin status for a group member.

    Returns redirect response if action should be aborted, None otherwise.
    """
    user_id = request.POST.get("user_id")
    if not user_id:
        return None

    user = get_object_or_404(User, id=user_id)
    membership = get_object_or_404(GroupMembership, user=user, group=group)

    # Check if demoting the last admin
    if membership.is_admin:
        can_demote, error_msg = group.can_demote_admin(user)
        if not can_demote:
            messages.error(request, error_msg)
            return redirect("battycoda_app:manage_group_members", group_id=group.id)

    membership.is_admin = not membership.is_admin
    membership.save()

    status = "granted" if membership.is_admin else "revoked"
    messages.success(request, f"Admin status {status} for user {user.username}.")
    return None


@login_required
def group_list_view(request):
    """Display list of groups"""
    # Get all groups the user is a member of through GroupMembership

    # Get user's memberships and related groups
    user_groups = (
        Group.objects.filter(group_memberships__user=request.user).select_related().distinct().order_by("name")
    )

    context = {
        "groups": user_groups,
    }

    return render(request, "groups/group_list.html", context)


@login_required
def group_detail_view(request, group_id):
    """Display details of a group"""
    # Get the group
    group = get_object_or_404(Group, id=group_id)

    # Check if the user is a member of this group via GroupMembership
    membership_exists = GroupMembership.objects.filter(user=request.user, group=group).exists()

    if membership_exists:
        # Get group with members preloaded
        group = Group.objects.prefetch_related("group_memberships", "group_memberships__user").get(id=group_id)

        # Get projects for this group
        projects = Project.objects.filter(group=group)

        # Get species for this group
        species = Species.objects.filter(group=group)

        # Get task batches for this group
        batches = TaskBatch.objects.filter(group=group)

        context = {
            "group": group,
            "projects": projects,
            "species": species,
            "batches": batches,
        }

        return render(request, "groups/group_detail.html", context)
    else:
        messages.error(request, "You do not have permission to view this group.")
        return redirect("battycoda_app:group_list")


@login_required
def create_group_view(request):
    """Handle creation of a group"""
    # Any authenticated user can create a group
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Create the group
                group = form.save()

                # Get the current user's profile
                user_profile = request.user.profile

                # Create GroupMembership record for the new group
                membership, created = GroupMembership.objects.get_or_create(
                    user=request.user,
                    group=group,
                    defaults={"is_admin": True},  # Group creator is always admin
                )

                # Always make the creator a member and admin of the new group
                user_profile.group = group
                user_profile.save()

            messages.success(request, "Group created successfully! You have been added as an admin.")
            return redirect("battycoda_app:group_detail", group_id=group.id)
    else:
        form = GroupForm()

    context = {
        "form": form,
    }

    return render(request, "groups/create_group.html", context)


@login_required
def edit_group_view(request, group_id):
    """Handle editing of a group (group admin only)"""
    group = get_object_or_404(Group, id=group_id)

    is_admin, error_response = _require_group_admin(request, group)
    if not is_admin:
        return error_response

    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()

            messages.success(request, "Group updated successfully.")
            return redirect("battycoda_app:group_detail", group_id=group.id)
    else:
        form = GroupForm(instance=group)

    context = {
        "form": form,
        "group": group,
    }

    return render(request, "groups/edit_group.html", context)


@login_required
def manage_group_members_view(request, group_id):
    """Handle managing group members (group admin only)."""
    group = get_object_or_404(Group, id=group_id)

    is_admin, error_response = _require_group_admin(request, group)
    if not is_admin:
        return error_response

    if request.method == "POST":
        # Dispatch to appropriate handler based on action
        if "add_user" in request.POST:
            _handle_add_member(request, group)
        elif "remove_user" in request.POST:
            abort_response = _handle_remove_member(request, group)
            if abort_response:
                return abort_response
        elif "toggle_admin" in request.POST:
            abort_response = _handle_toggle_admin(request, group)
            if abort_response:
                return abort_response

        return redirect("battycoda_app:manage_group_members", group_id=group.id)

    # GET request - show member management page
    group_memberships = GroupMembership.objects.filter(group=group).select_related("user", "user__profile")
    users_in_group = group_memberships.values_list("user__id", flat=True)
    non_group_users = User.objects.exclude(id__in=users_in_group)

    context = {
        "group": group,
        "group_memberships": group_memberships,
        "non_group_users": non_group_users,
    }

    return render(request, "groups/manage_members.html", context)


@login_required
def switch_group_view(request, group_id):
    """Allow a user to switch their active group."""
    group = get_object_or_404(Group, id=group_id)

    # User must be a member of the group to switch to it
    if not GroupMembership.objects.filter(user=request.user, group=group).exists():
        messages.error(request, "You are not a member of this group.")
        return redirect("battycoda_app:group_list")

    # Update the user's active group
    request.user.profile.group = group
    request.user.profile.save()

    messages.success(request, f'You are now working in the "{group.name}" group.')

    # Redirect back to referring page or index
    next_page = request.META.get("HTTP_REFERER", reverse("battycoda_app:index"))
    return redirect(next_page)
