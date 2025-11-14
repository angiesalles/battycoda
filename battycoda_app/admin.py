from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.widgets import AdminTextInputWidget
from hijack.contrib.admin import HijackUserAdminMixin

from .models.classification import CallProbability, Classifier, ClassifierTrainingJob, ClassificationResult, ClassificationRun
from .models.organization import Species, Call, Project
from .models.recording import Recording
from .models.segmentation import Segment, Segmentation, SegmentationAlgorithm
from .models.task import Task, TaskBatch
from .models.user import UserProfile, GroupMembership
from .models.user import Group as BattycodaGroup

# Try to import clustering models if they exist
try:
    from .models.clustering import (
        ClusteringAlgorithm, 
        ClusteringRun, 
        Cluster, 
        SegmentCluster, 
        ClusterCallMapping
    )
    clustering_enabled = True
except ImportError:
    clustering_enabled = False

# Add hijack functionality to the User admin
class HijackUserAdmin(HijackUserAdminMixin, UserAdmin):
    # Don't modify list_display - the mixin handles this automatically
    pass

# Re-register UserAdmin with hijack functionality
admin.site.unregister(User)
admin.site.register(User, HijackUserAdmin)

# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "id")
    search_fields = ("user__username", "user__email")

@admin.register(Classifier)
class ClassifierAdmin(admin.ModelAdmin):
    list_display = ("name", "response_format", "service_url", "is_active", "group")
    list_filter = ("response_format", "is_active", "group")
    search_fields = ("name", "description", "service_url")
    list_editable = ("is_active",)

class CallInline(admin.TabularInline):
    model = Call
    extra = 1
    fields = ('short_name', 'long_name')

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ("name", "is_system", "group", "created_by")
    list_filter = ("is_system", "group")
    search_fields = ("name", "description")
    inlines = [CallInline]
    readonly_fields = []  # Allow all fields to be edited, including is_system

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "description", "image", "is_system", "group", "created_by")
        }),
        ("Spectrogram Padding (milliseconds)", {
            "fields": (
                ("detail_padding_start_ms", "detail_padding_end_ms"),
                ("overview_padding_start_ms", "overview_padding_end_ms"),
            ),
            "description": "Configure padding around calls in spectrograms. Detail view shows the immediate call context, while overview provides broader temporal context."
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of system species
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name", "species")
    list_filter = ("species",)
    search_fields = ("short_name", "long_name", "species__name")
    
    def get_readonly_fields(self, request, obj=None):
        # Make fields editable even for system species
        return []

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "created_by", "created_at")
    list_filter = ("group",)
    search_fields = ("name", "description")

@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ("name", "species", "project", "created_by")
    list_filter = ("species", "project", "group")
    search_fields = ("name", "description")

@admin.register(ClassificationRun)
class ClassificationRunAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "classifier", "created_at", "created_by")
    list_filter = ("status", "classifier", "group")
    search_fields = ("name",)

@admin.register(CallProbability)
class CallProbabilityAdmin(admin.ModelAdmin):
    list_display = ("call", "probability", "classification_result")
    list_filter = ("call",)
    search_fields = ("call__short_name",)

# Register the rest of the models
admin.site.register(ClassifierTrainingJob)
admin.site.register(ClassificationResult)
admin.site.register(Segment)
admin.site.register(Segmentation)
admin.site.register(SegmentationAlgorithm)
admin.site.register(Task)
admin.site.register(TaskBatch)
admin.site.register(GroupMembership)
admin.site.register(BattycodaGroup)

# Register clustering models if they exist
if clustering_enabled:
    @admin.register(ClusteringAlgorithm)
    class ClusteringAlgorithmAdmin(admin.ModelAdmin):
        list_display = ("name", "algorithm_type", "is_active", "created_by", "group")
        list_filter = ("algorithm_type", "is_active", "group")
        search_fields = ("name", "description")
        
    @admin.register(ClusteringRun)
    class ClusteringRunAdmin(admin.ModelAdmin):
        list_display = ("name", "algorithm", "status", "num_clusters_created", "progress", "created_by")
        list_filter = ("status", "algorithm", "group")
        search_fields = ("name", "description")
        
    @admin.register(Cluster)
    class ClusterAdmin(admin.ModelAdmin):
        list_display = ("__str__", "clustering_run", "size", "is_labeled", "coherence")
        list_filter = ("is_labeled", "clustering_run")
        search_fields = ("label", "description")
        
    admin.site.register(SegmentCluster)
    admin.site.register(ClusterCallMapping)
