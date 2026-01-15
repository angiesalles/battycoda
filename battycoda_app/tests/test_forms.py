from django.contrib.auth.models import User

from battycoda_app.forms import (
    GroupForm,
    ProjectForm,
    TaskForm,
    TaskUpdateForm,
    UserLoginForm,
    UserProfileForm,
    UserRegisterForm,
)
from battycoda_app.models import Group, Project, Species, UserProfile
from battycoda_app.tests.test_base import BattycodaTestCase


class UserFormsTest(BattycodaTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

    def test_user_register_form_valid(self):
        # Form requires captcha_num1, captcha_num2 kwargs and captcha_answer in data
        form = UserRegisterForm(
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password1": "Password123!",
                "password2": "Password123!",
                "captcha_answer": 8,  # 5 + 3 = 8
            },
            captcha_num1=5,
            captcha_num2=3,
        )
        self.assertTrue(form.is_valid())

    def test_user_register_form_invalid_passwords(self):
        form = UserRegisterForm(
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password1": "Password123!",
                "password2": "DifferentPassword123!",
                "captcha_answer": 8,
            },
            captcha_num1=5,
            captcha_num2=3,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_user_login_form_valid(self):
        form = UserLoginForm(data={"username": "testuser", "password": "password123"})
        # Note: AuthenticationForm requires the request to be passed in at initialization
        # In a real test, we'd mock the request or use the test client
        # For this simple validation, we're just checking field presence
        self.assertEqual(form.fields["username"].label, "Username")
        self.assertEqual(form.fields["password"].label, "Password")

    def test_user_profile_form_fields(self):
        # UserProfileForm should have theme, profile_image, and management_features_enabled fields
        form = UserProfileForm(instance=self.profile, user=self.user)

        self.assertIn("theme", form.fields)
        self.assertIn("profile_image", form.fields)
        self.assertIn("management_features_enabled", form.fields)

        # Should not have is_admin or group fields (these were removed)
        self.assertNotIn("is_admin", form.fields)
        self.assertNotIn("group", form.fields)


class TaskFormsTest(BattycodaTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")

        self.profile = UserProfile.objects.get(user=self.user)

        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Set as active group for user
        self.profile.group = self.group
        self.profile.save()

        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )

        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
        )

    def test_task_form_init(self):
        form = TaskForm(user=self.user)

        # Form should have species and project fields filtered by group
        self.assertEqual(list(form.fields["species"].queryset), [self.species])
        self.assertEqual(list(form.fields["project"].queryset), [self.project])

    def test_task_form_valid(self):
        form = TaskForm(
            data={
                "wav_file_name": "test.wav",
                "onset": 1.0,
                "offset": 2.0,
                "species": self.species.id,
                "project": self.project.id,
                "status": "pending",
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_task_update_form_valid(self):
        # Task.STATUS_CHOICES are: pending, in_progress, done
        form = TaskUpdateForm(
            data={"status": "done", "is_done": True, "label": "Test Label", "notes": "Test notes"}
        )
        self.assertTrue(form.is_valid())


class ProjectFormsTest(BattycodaTestCase):
    def test_project_form_valid(self):
        form = ProjectForm(data={"name": "Test Project", "description": "A test project description"})
        self.assertTrue(form.is_valid())

    def test_project_form_invalid_missing_name(self):
        form = ProjectForm(data={"description": "A test project description"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class GroupFormsTest(BattycodaTestCase):
    def test_group_form_valid(self):
        form = GroupForm(data={"name": "Test Group", "description": "A test group description"})
        self.assertTrue(form.is_valid())

    def test_group_form_invalid_missing_name(self):
        form = GroupForm(data={"description": "A test group description"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
