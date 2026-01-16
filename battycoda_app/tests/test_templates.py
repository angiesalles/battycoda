"""
Template validation tests.

These tests ensure that all templates are syntactically valid and can render
without errors. They help catch issues like:
- Invalid block tags (e.g., mismatched {% block %} and {% endblock %})
- Missing template includes
- Template syntax errors
- Invalid template variable references
"""

import os

from django.conf import settings
from django.contrib.auth.models import User
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template
from django.test import RequestFactory, TestCase, override_settings

from battycoda_app.forms import SpeciesForm
from battycoda_app.models.organization import Species
from battycoda_app.models.user import Group
from battycoda_app.tests.test_settings import PASSWORD_HASHERS

# Suppress noisy logs during tests
import logging

logging.disable(logging.ERROR)


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS)
class TemplateValidationTestCase(TestCase):
    """Test that all templates are syntactically valid."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.group = Group.objects.create(name="Test Group")
        self.profile = self.user.profile
        self.profile.group = self.group
        self.profile.save()

    def get_all_templates(self):
        """
        Get all template files in the templates directory.
        Returns list of template paths relative to templates dir.
        """
        templates = []
        templates_dir = os.path.join(settings.BASE_DIR, "templates")

        for root, dirs, files in os.walk(templates_dir):
            for filename in files:
                if filename.endswith(".html"):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, templates_dir)
                    templates.append(rel_path)

        return templates

    def test_all_templates_load_without_syntax_errors(self):
        """Test that all templates can be loaded without TemplateSyntaxError."""
        templates = self.get_all_templates()
        errors = []

        for template_path in templates:
            try:
                template = get_template(template_path)
                # Just loading the template will catch syntax errors
                self.assertIsNotNone(template)
            except TemplateSyntaxError as e:
                errors.append(f"{template_path}: {str(e)}")
            except TemplateDoesNotExist:
                # Some templates might be conditional, skip those
                pass

        if errors:
            error_msg = "Templates with syntax errors:\n" + "\n".join(errors)
            self.fail(error_msg)

    def test_base_template_loads(self):
        """Test that the base template loads correctly."""
        try:
            template = get_template("base.html")
            self.assertIsNotNone(template)
        except TemplateSyntaxError as e:
            self.fail(f"base.html has syntax error: {str(e)}")

    def test_species_create_template_loads(self):
        """Test that the species create template loads correctly."""
        try:
            template = get_template("species/create_species.html")
            self.assertIsNotNone(template)
        except TemplateSyntaxError as e:
            self.fail(f"species/create_species.html has syntax error: {str(e)}")

    def test_species_create_includes_exist(self):
        """Test that all includes referenced by species/create_species.html exist."""
        includes = [
            "species/includes/basic_form.html",
            "species/includes/call_types.html",
        ]

        for include_path in includes:
            try:
                template = get_template(include_path)
                self.assertIsNotNone(template)
            except TemplateDoesNotExist:
                self.fail(f"Include template does not exist: {include_path}")
            except TemplateSyntaxError as e:
                self.fail(f"Include template has syntax error: {include_path}: {str(e)}")

    def test_species_create_template_renders(self):
        """Test that the species create template can render with appropriate context."""
        template = get_template("species/create_species.html")

        context = {
            "form": SpeciesForm(),
            "existing_species_names": [],
            "user": self.user,
        }

        try:
            rendered = template.render(context)
            self.assertIsNotNone(rendered)
            self.assertIn("Add New Species", rendered)
            self.assertIn("call_types_json", rendered)
        except Exception as e:
            self.fail(f"Template rendering failed: {str(e)}")

    def test_species_list_template_renders(self):
        """Test that the species list template can render."""
        template = get_template("species/species_list.html")

        species = Species.objects.create(name="Test Species", group=self.group)

        context = {
            "system_species": [species],
            "user_species": [],
            "user": self.user,
            "profile": self.profile,
        }

        try:
            rendered = template.render(context)
            self.assertIsNotNone(rendered)
        except Exception as e:
            self.fail(f"Template rendering failed: {str(e)}")

    def test_species_detail_template_renders(self):
        """Test that the species detail template can render."""
        template = get_template("species/species_detail.html")

        species = Species.objects.create(name="Test Species", group=self.group)

        context = {
            "species": species,
            "tasks_page": [],
            "batches_page": [],
            "user": self.user,
            "profile": self.profile,
        }

        try:
            rendered = template.render(context)
            self.assertIsNotNone(rendered)
        except Exception as e:
            self.fail(f"Template rendering failed: {str(e)}")


class TemplateBlockStructureTestCase(TestCase):
    """Test that template block structures are valid."""

    def check_template_blocks(self, template_path):
        """
        Check that a template has matching block/endblock tags.
        Returns (is_valid, error_message).
        """
        try:
            template = get_template(template_path)
            # If it loads without TemplateSyntaxError, blocks are valid
            return True, None
        except TemplateSyntaxError as e:
            if "endblock" in str(e).lower():
                return False, str(e)
            # Other syntax errors are handled elsewhere
            return True, None
        except TemplateDoesNotExist:
            return True, None  # Skip non-existent templates

    def test_species_create_blocks(self):
        """Test that species/create_species.html has valid block structure."""
        is_valid, error = self.check_template_blocks("species/create_species.html")
        if not is_valid:
            self.fail(f"Invalid block structure: {error}")

    def test_species_includes_blocks(self):
        """Test that species includes have valid block structure."""
        includes = [
            "species/includes/basic_form.html",
            "species/includes/call_types.html",
        ]

        errors = []
        for include_path in includes:
            is_valid, error = self.check_template_blocks(include_path)
            if not is_valid:
                errors.append(f"{include_path}: {error}")

        if errors:
            self.fail("Invalid block structures:\n" + "\n".join(errors))


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS)
class TemplateCriticalPathTestCase(TestCase):
    """Test critical user-facing templates render correctly."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.group = Group.objects.create(name="Test Group")
        self.profile = self.user.profile
        self.profile.group = self.group
        self.profile.save()

    def test_critical_templates_exist(self):
        """Test that critical templates exist and load."""
        critical_templates = [
            "base.html",
            "species/species_list.html",
            "species/species_detail.html",
            "species/create_species.html",
            "tasks/annotate_task.html",
            "recordings/recording_list.html",
            "projects/project_list.html",
        ]

        missing = []
        syntax_errors = []

        for template_path in critical_templates:
            try:
                template = get_template(template_path)
                self.assertIsNotNone(template)
            except TemplateDoesNotExist:
                missing.append(template_path)
            except TemplateSyntaxError as e:
                syntax_errors.append(f"{template_path}: {str(e)}")

        errors = []
        if missing:
            errors.append("Missing templates:\n" + "\n".join(missing))
        if syntax_errors:
            errors.append("Templates with syntax errors:\n" + "\n".join(syntax_errors))

        if errors:
            self.fail("\n\n".join(errors))
