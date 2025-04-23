from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from hijack.contrib.admin import HijackUserAdminMixin

from .models.detection import Classifier
from .models.user import UserProfile

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
