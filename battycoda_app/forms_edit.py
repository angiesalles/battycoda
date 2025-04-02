from django import forms
from django.db import models

from .models.organization import Project, Species
from .models.recording import Recording
from .models.user import UserProfile

class RecordingEditForm(forms.ModelForm):
    """Form specifically for editing recordings - doesn't allow changing species or file"""

    recorded_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False, help_text="Date when the recording was made"
    )

    class Meta:
        model = Recording
        fields = [
            "name",
            "description",
            "recorded_date",
            "location",
            "equipment",
            "environmental_conditions",
            "project",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "environmental_conditions": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "project": forms.Select(attrs={"class": "form-select", "size": "1"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Set empty label for dropdowns
        self.fields["project"].empty_label = "Select a project"

        # Store user profile for validation
        self.profile = None

        if self.user:
            # Get or create user profile
            self.profile, created = UserProfile.objects.get_or_create(user=self.user)

            # Filter projects by user's group
            if self.profile.group:
                self.fields["project"].queryset = self.fields["project"].queryset.filter(group=self.profile.group)