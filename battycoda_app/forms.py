from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.db import models

from .models.organization import Call, Project, Species
from .models.recording import Recording, Segment
from .models.task import Task, TaskBatch
from .models.user import Group, UserProfile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if '@' in username:
            raise forms.ValidationError("Username cannot contain the @ symbol. Please choose a different username.")
        return username

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["theme", "profile_image", "management_features_enabled"]

    def __init__(self, *args, **kwargs):
        # Get the user making the request
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Add styling to the theme select field
        if "theme" in self.fields:
            self.fields["theme"].widget.attrs.update(
                {"class": "form-control"}
            )
            
        # Add styling to the profile image field
        if "profile_image" in self.fields:
            self.fields["profile_image"].widget.attrs.update({
                "class": "form-control",
                "accept": "image/*"  # Only accept image files
            })
            self.fields["profile_image"].required = False
            self.fields["profile_image"].help_text = "Upload a profile image (JPG, PNG, etc.)"
            
        # Add styling and help text to the management features field
        if "management_features_enabled" in self.fields:
            self.fields["management_features_enabled"].widget.attrs.update({
                "class": "form-check-input"
            })
            self.fields["management_features_enabled"].help_text = (
                "Enable access to administrative features like viewing all group data, "
                "managing recordings and task batches for other users, and system-wide statistics."
            )

class TaskBatchForm(forms.ModelForm):
    wav_file = forms.FileField(
        help_text="Upload the WAV file for this task batch.",
        required=True,
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )
    pickle_file = forms.FileField(
        help_text="Upload a pickle file containing onsets and offsets.",
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = TaskBatch
        fields = ["name", "species", "project", "wav_file"]
        # hidden wav_file_name field that will be auto-populated from the wav_file
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "species": forms.Select(attrs={"class": "form-control"}),
            "project": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Set empty label for dropdowns
        self.fields["species"].empty_label = "Select a species"
        self.fields["project"].empty_label = "Select a project"

        if self.user:
            # Get or create user profile
            from .models import UserProfile

            self.profile, created = UserProfile.objects.get_or_create(user=self.user)

            # Filter species and projects by user's group - always using profile object directly
            if self.profile.group:
                # Filter querysets
                self.fields["species"].queryset = self.fields["species"].queryset.filter(group=self.profile.group)
                self.fields["project"].queryset = self.fields["project"].queryset.filter(group=self.profile.group)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "wav_file_name",
            "onset",
            "offset",
            "species",
            "project",
            "status",
            "is_done",
            "label",
            "classification_result",
            "confidence",
            "notes",
        ]
        widgets = {
            "onset": forms.NumberInput(attrs={"step": "0.01"}),
            "offset": forms.NumberInput(attrs={"step": "0.01"}),
            "confidence": forms.NumberInput(attrs={"step": "0.01"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Set empty label for dropdowns
        self.fields["species"].empty_label = "Select a species"
        self.fields["project"].empty_label = "Select a project"

        if user:
            # Get or create user profile
            from .models import UserProfile

            profile, created = UserProfile.objects.get_or_create(user=user)

            # Filter species and projects by user's group - always using profile object directly
            if profile.group:
                # Filter querysets
                self.fields["species"].queryset = self.fields["species"].queryset.filter(group=profile.group)
                self.fields["project"].queryset = self.fields["project"].queryset.filter(group=profile.group)

class TaskUpdateForm(forms.ModelForm):
    """Form for updating task status and labels"""

    class Meta:
        model = Task
        fields = ["status", "is_done", "label", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species
        fields = ["name", "description", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }

class SpeciesEditForm(forms.ModelForm):
    """Form for editing species without calls file upload"""

    class Meta:
        model = Species
        fields = ["name", "description", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }

class CallForm(forms.ModelForm):
    class Meta:
        model = Call
        fields = ["short_name", "long_name"]
        widgets = {
            "short_name": forms.TextInput(attrs={"class": "form-control"}),
            "long_name": forms.TextInput(attrs={"class": "form-control"}),
            "DELETE": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class CallFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only set empty queryset for new instances, not when editing
        if not self.queryset:
            self.queryset = Call.objects.none()

# Use extra=1 to add a single empty form by default
CallFormSetFactory = forms.modelformset_factory(
    Call, form=CallForm, formset=CallFormSet, extra=1, can_delete=True  # Add one empty form
)

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter project name"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control", "placeholder": "Describe your project here"}),
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

class GroupInvitationForm(forms.Form):
    email = forms.EmailField(
        label="Email Address", help_text="Enter the email address of the person you want to invite to your group"
    )

class RecordingForm(forms.ModelForm):
    """Form for creating and editing recordings"""

    # Make name optional - it will be set automatically for batch uploads
    name = forms.CharField(
        max_length=255, required=False, help_text="Name of the recording"  # Make it optional for batch upload
    )

    recorded_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False, help_text="Date when the recording was made"
    )

    # Override wav_file field to hide "Currently" text
    wav_file = forms.FileField(required=False, widget=forms.FileInput(attrs={"class": "form-control"}))

    class Meta:
        model = Recording
        fields = [
            "name",
            "wav_file",
            "recorded_date",
            "location",
            "equipment",
            "environmental_conditions",
            "species",
            "project",
        ]
        widgets = {
            "environmental_conditions": forms.Textarea(attrs={"rows": 3}),
            "species": forms.Select(attrs={"class": "form-select", "size": "1"}),
            "project": forms.Select(attrs={"class": "form-select", "size": "1"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Set empty label for dropdowns
        self.fields["species"].empty_label = "Select a species"
        self.fields["project"].empty_label = "Select a project"

        # Store user profile for validation
        self.profile = None

        if self.user:
            # Get or create user profile
            self.profile, created = UserProfile.objects.get_or_create(user=self.user)

            # Get system species and those belonging to the user's group
            if self.profile.group:
                self.fields["species"].queryset = Species.objects.filter(
                    models.Q(is_system=True) | models.Q(group=self.profile.group)
                ).order_by('name')
                self.fields["project"].queryset = self.fields["project"].queryset.filter(group=self.profile.group)

    def clean_name(self):
        """Name validation"""
        name = self.cleaned_data.get("name")
        return name

class SegmentForm(forms.ModelForm):
    """Form for creating and editing segments in recordings"""

    class Meta:
        model = Segment
        fields = ["name", "onset", "offset", "notes"]
        widgets = {
            "onset": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "offset": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        recording = kwargs.pop("recording", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        onset = cleaned_data.get("onset")
        offset = cleaned_data.get("offset")

        # Ensure offset is greater than onset
        if onset is not None and offset is not None:
            if offset <= onset:
                raise forms.ValidationError("Offset time must be greater than onset time")

        return cleaned_data

class SegmentFormSet(forms.BaseModelFormSet):
    """Formset for managing multiple segments"""

    def __init__(self, *args, **kwargs):
        recording = kwargs.pop("recording", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validate that segments don't overlap"""
        if any(self.errors):
            # Don't validate formset if individual forms have errors
            return

        segments = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue

            onset = form.cleaned_data.get("onset")
            offset = form.cleaned_data.get("offset")

            if onset is not None and offset is not None:
                # Check for overlap with other segments
                for other_onset, other_offset in segments:
                    if max(onset, other_onset) < min(offset, other_offset):
                        raise forms.ValidationError("Segments cannot overlap")

                segments.append((onset, offset))

# Create formset factory for segments
SegmentFormSetFactory = forms.modelformset_factory(
    Segment, form=SegmentForm, formset=SegmentFormSet, extra=1, can_delete=True
)
