"""Detection models for BattyCoda application."""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from .organization import Call, Species
from .task import TaskBatch
from .user import Group

class Classifier(models.Model):
    """Classifier model for storing algorithm information."""

    name = models.CharField(max_length=255, help_text="Name of the classification algorithm")
    description = models.TextField(blank=True, null=True, help_text="Description of how the algorithm works")

    # Response format choices
    RESPONSE_FORMAT_CHOICES = (
        ("full_probability", "Full Probability Distribution"),
        ("highest_only", "Highest Probability Only"),
    )
    response_format = models.CharField(
        max_length=20, choices=RESPONSE_FORMAT_CHOICES, help_text="Format of the response returned by this algorithm"
    )

    # Celery task to call
    celery_task = models.CharField(
        max_length=255,
        help_text="Fully qualified Celery task name to execute this algorithm",
        default="battycoda_app.audio.task_modules.detection_tasks.run_call_detection",
    )

    # External service parameters
    service_url = models.CharField(
        max_length=255, blank=True, null=True, help_text="URL of the external service, if applicable"
    )
    endpoint = models.CharField(max_length=255, blank=True, null=True, help_text="Endpoint path for the service")

    # Source task batch (if this classifier was created from a task batch)
    source_task_batch = models.ForeignKey(
        "battycoda_app.TaskBatch",
        on_delete=models.SET_NULL,
        related_name="derived_classifiers",
        null=True,
        blank=True,
        help_text="The task batch that was used to train this classifier",
    )

    # Model file path if this is a custom trained classifier
    model_file = models.CharField(
        max_length=512, 
        blank=True, 
        null=True, 
        help_text="Path to the model file for custom trained classifiers"
    )
    
    # Species this classifier is trained for
    species = models.ForeignKey(
        Species,
        on_delete=models.PROTECT,  # Prevent deletion of species used by a classifier
        related_name="classifiers",
        null=True,
        blank=True,
        help_text="Species this classifier is trained for. Once set, this cannot be changed."
    )

    # Admin only flag
    is_active = models.BooleanField(default=True, help_text="Whether this classifier is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_classifiers",
        null=True,
        blank=True,
        help_text="User who created this classifier",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="classifiers",
        null=True,
        blank=True,
        help_text="Group that owns this classifier. If null, it's available to all groups",
    )

    def __str__(self):
        return self.name
        
    def clean(self):
        """Validate the model before saving"""
        # If this is an existing classifier with a species already set
        if self.pk:
            original = Classifier.objects.get(pk=self.pk)
            # Check if species is being changed and was previously set
            if original.species and self.species != original.species:
                raise ValidationError({
                    'species': "Cannot change the species of an existing classifier. "
                               "The classifier is tied to the call types of its species."
                })
    
    def save(self, *args, **kwargs):
        """Override save to enforce validation"""
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["name"]

class DetectionRun(models.Model):
    """Detection run model for tracking automated detection jobs."""

    name = models.CharField(max_length=255)
    segmentation = models.ForeignKey(
        "battycoda_app.Segmentation", on_delete=models.CASCADE, related_name="detection_runs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="detection_runs")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="detection_runs", null=True)

    # Algorithm type choices (for backward compatibility)
    ALGORITHM_TYPE_CHOICES = (
        ("full_probability", "Full Probability Distribution"),
        ("highest_only", "Highest Probability Only"),
    )
    algorithm_type = models.CharField(
        max_length=20,
        choices=ALGORITHM_TYPE_CHOICES,
        default="highest_only",
        help_text="Whether the algorithm returns full probability distributions or only the highest probability",
    )

    # Link to the classifier used
    classifier = models.ForeignKey(
        Classifier,
        on_delete=models.CASCADE,
        related_name="detection_runs",
        null=True,
        blank=True,
        help_text="The classifier algorithm used for this detection run",
    )

    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    progress = models.FloatField(default=0.0, help_text="Progress percentage from 0-100")
    error_message = models.TextField(blank=True, null=True)
    features_file = models.CharField(
        max_length=512, 
        blank=True, 
        null=True, 
        help_text="Path to the exported features CSV file"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.segmentation.recording.name}"

class DetectionResult(models.Model):
    """Detection Result model for storing individual call detection probabilities."""

    detection_run = models.ForeignKey(DetectionRun, on_delete=models.CASCADE, related_name="results")
    segment = models.ForeignKey("battycoda_app.Segment", on_delete=models.CASCADE, related_name="detection_results")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["segment__onset"]

    def __str__(self):
        return f"Detection for {self.segment}"

class CallProbability(models.Model):
    """Call probability model for storing probability for each call type."""

    detection_result = models.ForeignKey(DetectionResult, on_delete=models.CASCADE, related_name="probabilities")
    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name="probabilities")
    probability = models.FloatField(help_text="Probability value between 0-1")

    class Meta:
        ordering = ["-probability"]

    def __str__(self):
        return f"{self.call.short_name}: {self.probability:.2f}"


class ClassifierTrainingJob(models.Model):
    """Model for tracking the training of custom classifiers from task batches."""

    name = models.CharField(max_length=255, help_text="Name for this training job")
    description = models.TextField(blank=True, null=True, help_text="Description of the training job")
    task_batch = models.ForeignKey(
        "battycoda_app.TaskBatch", 
        on_delete=models.CASCADE, 
        related_name="training_jobs",
        help_text="The task batch used for training this classifier"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="training_jobs")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="training_jobs", null=True)
    
    # Classifier settings
    response_format = models.CharField(
        max_length=20, 
        choices=Classifier.RESPONSE_FORMAT_CHOICES,
        default="highest_only",
        help_text="Format of the response returned by this classifier"
    )
    
    # Reference to resulting classifier (set when training completes)
    classifier = models.ForeignKey(
        Classifier,
        on_delete=models.SET_NULL,
        related_name="training_job",
        null=True,
        blank=True,
        help_text="The classifier created by this training job (set after successful completion)"
    )
    
    # Training parameters (can be extended as needed)
    parameters = models.JSONField(
        blank=True, 
        null=True, 
        help_text="JSON with training parameters"
    )
    
    # Status tracking
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    progress = models.FloatField(default=0.0, help_text="Progress percentage from 0-100")
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ["-created_at"]
        
    def __str__(self):
        return f"{self.name} - {self.task_batch.name}"
