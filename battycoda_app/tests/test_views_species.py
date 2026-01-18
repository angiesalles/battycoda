"""Tests for species views"""

import json

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from battycoda_app.models import Group, GroupMembership, UserProfile
from battycoda_app.models.organization import Call, Species
from battycoda_app.tests.test_base import BattycodaTestCase


class SpeciesListViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # Create a group species
        self.species = Species.objects.create(
            name="Test Species",
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.species_list_url = reverse("battycoda_app:species_list")

    def test_species_list_view_authenticated(self):
        """Authenticated users should see the species list"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.species_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "species/species_list.html")
        self.assertIn("species_list", response.context)

    def test_species_list_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.species_list_url)
        self.assertEqual(response.status_code, 302)

    def test_species_list_shows_group_species(self):
        """Species list should show group species"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.species_list_url)
        species_list = response.context["species_list"]
        self.assertTrue(any(s.name == "Test Species" for s in species_list))


class SpeciesDetailViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # Create a group species
        self.species = Species.objects.create(
            name="Test Species",
            group=self.group,
            created_by=self.user,
        )

        # Create calls for the species
        self.call = Call.objects.create(
            species=self.species,
            short_name="TC",
            long_name="Test Call",
        )

        # URL paths
        self.species_detail_url = reverse("battycoda_app:species_detail", args=[self.species.id])

    def test_species_detail_view_authenticated(self):
        """Authenticated users should see the species detail"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.species_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "species/species_detail.html")
        self.assertEqual(response.context["species"].name, "Test Species")

    def test_species_detail_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.species_detail_url)
        self.assertEqual(response.status_code, 302)

    def test_species_detail_shows_calls(self):
        """Species detail should show call types"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.species_detail_url)
        calls = response.context["calls"]
        self.assertTrue(any(c.short_name == "TC" for c in calls))


class CreateSpeciesViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # URL paths
        self.create_species_url = reverse("battycoda_app:create_species")

    def test_create_species_view_get(self):
        """GET request should show the create species form"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.create_species_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "species/create_species.html")
        self.assertIn("form", response.context)

    def test_create_species_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.create_species_url)
        self.assertEqual(response.status_code, 302)

    def test_create_species_post_success(self):
        """POST request with valid data should create species"""
        self.client.login(username="testuser", password="password123")
        species_data = {
            "name": "New Species",
            "description": "A new species",
            "call_types_json": json.dumps([{"short_name": "NC", "long_name": "New Call"}]),
            "detail_padding_start_ms": 8,
            "detail_padding_end_ms": 8,
            "overview_padding_start_ms": 500,
            "overview_padding_end_ms": 500,
        }
        response = self.client.post(self.create_species_url, species_data)
        self.assertEqual(response.status_code, 302)  # Redirects to detail
        self.assertTrue(Species.objects.filter(name="New Species").exists())

    def test_create_species_creates_calls(self):
        """Creating species should also create call types"""
        self.client.login(username="testuser", password="password123")
        species_data = {
            "name": "Species With Calls",
            "description": "A species with calls",
            "call_types_json": json.dumps(
                [
                    {"short_name": "C1", "long_name": "Call One"},
                    {"short_name": "C2", "long_name": "Call Two"},
                ]
            ),
            "detail_padding_start_ms": 8,
            "detail_padding_end_ms": 8,
            "overview_padding_start_ms": 500,
            "overview_padding_end_ms": 500,
        }
        response = self.client.post(self.create_species_url, species_data)
        self.assertEqual(response.status_code, 302)

        species = Species.objects.get(name="Species With Calls")
        calls = Call.objects.filter(species=species)
        self.assertEqual(calls.count(), 2)


class EditSpeciesViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # Create a group species
        self.species = Species.objects.create(
            name="Test Species",
            description="Original description",
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.edit_species_url = reverse("battycoda_app:edit_species", args=[self.species.id])

    def test_edit_species_view_get(self):
        """GET request should show the edit species form"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.edit_species_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "species/edit_species.html")
        self.assertIn("form", response.context)

    def test_edit_species_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.edit_species_url)
        self.assertEqual(response.status_code, 302)

    def test_edit_species_post_success(self):
        """POST request with valid data should update species"""
        self.client.login(username="testuser", password="password123")
        species_data = {
            "name": "Updated Species Name",
            "description": "Updated description",
            "detail_padding_start_ms": 8,
            "detail_padding_end_ms": 8,
            "overview_padding_start_ms": 500,
            "overview_padding_end_ms": 500,
        }
        response = self.client.post(self.edit_species_url, species_data)
        self.assertEqual(response.status_code, 302)  # Redirects to detail

        self.species.refresh_from_db()
        self.assertEqual(self.species.name, "Updated Species Name")
        self.assertEqual(self.species.description, "Updated description")

    def test_edit_system_species_forbidden(self):
        """Editing system species should be forbidden"""
        # Create a system species
        system_species = Species.objects.create(
            name="System Species",
            is_system=True,
        )

        self.client.login(username="testuser", password="password123")
        edit_url = reverse("battycoda_app:edit_species", args=[system_species.id])
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 302)  # Redirects

    def test_edit_species_with_call_types_json(self):
        """POST with call_types_json should add, update, and delete calls"""
        # First add some existing calls
        Call.objects.create(species=self.species, short_name="C1", long_name="Call One")
        Call.objects.create(species=self.species, short_name="C2", long_name="Call Two")
        Call.objects.create(species=self.species, short_name="C3", long_name="Call Three")

        self.client.login(username="testuser", password="password123")

        # Submit with updated calls:
        # - C1: Keep (with updated long_name)
        # - C2: Delete (not in list)
        # - C3: Delete (not in list)
        # - C4: Add new
        species_data = {
            "name": "Test Species",
            "description": "Updated description",
            "call_types_json": json.dumps(
                [
                    {"short_name": "C1", "long_name": "Call One Updated"},
                    {"short_name": "C4", "long_name": "Call Four"},
                ]
            ),
            "detail_padding_start_ms": 8,
            "detail_padding_end_ms": 8,
            "overview_padding_start_ms": 500,
            "overview_padding_end_ms": 500,
        }
        response = self.client.post(self.edit_species_url, species_data)
        self.assertEqual(response.status_code, 302)  # Redirects to detail

        # Verify the calls
        calls = Call.objects.filter(species=self.species)
        self.assertEqual(calls.count(), 2)

        # C1 should be updated
        c1 = calls.get(short_name="C1")
        self.assertEqual(c1.long_name, "Call One Updated")

        # C4 should be added
        self.assertTrue(calls.filter(short_name="C4").exists())

        # C2 and C3 should be deleted
        self.assertFalse(calls.filter(short_name="C2").exists())
        self.assertFalse(calls.filter(short_name="C3").exists())

    def test_edit_species_clear_all_calls(self):
        """POST with empty call_types_json should delete all calls"""
        # Add some existing calls
        Call.objects.create(species=self.species, short_name="C1", long_name="Call One")
        Call.objects.create(species=self.species, short_name="C2", long_name="Call Two")

        self.client.login(username="testuser", password="password123")

        species_data = {
            "name": "Test Species",
            "description": "Updated description",
            "call_types_json": "[]",  # Empty list
            "detail_padding_start_ms": 8,
            "detail_padding_end_ms": 8,
            "overview_padding_start_ms": 500,
            "overview_padding_end_ms": 500,
        }
        response = self.client.post(self.edit_species_url, species_data)
        self.assertEqual(response.status_code, 302)

        # All calls should be deleted
        calls = Call.objects.filter(species=self.species)
        self.assertEqual(calls.count(), 0)


class DeleteSpeciesViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # Create a species to delete
        self.species = Species.objects.create(
            name="Species To Delete",
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.delete_species_url = reverse("battycoda_app:delete_species", args=[self.species.id])

    def test_delete_species_view_get(self):
        """GET request should show the delete confirmation page"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.delete_species_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "species/delete_species.html")

    def test_delete_species_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.delete_species_url)
        self.assertEqual(response.status_code, 302)

    def test_delete_species_post_success(self):
        """POST request should delete species"""
        self.client.login(username="testuser", password="password123")
        species_id = self.species.id
        response = self.client.post(self.delete_species_url)
        self.assertEqual(response.status_code, 302)  # Redirects to list
        self.assertFalse(Species.objects.filter(id=species_id).exists())

    def test_delete_system_species_forbidden(self):
        """Deleting system species should be forbidden"""
        # Create a system species
        system_species = Species.objects.create(
            name="System Species",
            is_system=True,
        )

        self.client.login(username="testuser", password="password123")
        delete_url = reverse("battycoda_app:delete_species", args=[system_species.id])
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 302)  # Redirects


class ParseCallsFileViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # URL paths
        self.parse_calls_url = reverse("battycoda_app:parse_calls_file")

    def test_parse_calls_file_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.post(self.parse_calls_url)
        self.assertEqual(response.status_code, 302)

    def test_parse_calls_file_no_file(self):
        """Missing file should return error"""
        self.client.login(username="testuser", password="password123")
        response = self.client.post(self.parse_calls_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
