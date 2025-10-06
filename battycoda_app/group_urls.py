"""
Group management and user invitation URL patterns.

Handles group CRUD operations, member management, and user invitations.
"""
from django.urls import path
from . import views_group, views_invitations

urlpatterns = [
    path("groups/", views_group.group_list_view, name="group_list"),
    path("groups/<int:group_id>/", views_group.group_detail_view, name="group_detail"),
    path("groups/create/", views_group.create_group_view, name="create_group"),
    path("groups/<int:group_id>/edit/", views_group.edit_group_view, name="edit_group"),
    path("groups/<int:group_id>/members/", views_group.manage_group_members_view, name="manage_group_members"),
    path("groups/switch/<int:group_id>/", views_group.switch_group_view, name="switch_group"),
    path("users/", views_invitations.group_users_view, name="group_users"),
    path("users/invite/", views_invitations.invite_user_view, name="invite_user"),
    path("invitation/<str:token>/", views_invitations.accept_invitation_view, name="accept_invitation"),
]
