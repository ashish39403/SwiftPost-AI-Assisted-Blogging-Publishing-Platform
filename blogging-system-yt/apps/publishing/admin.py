from django.contrib import admin

from apps.publishing.models import PublishingEvent


@admin.register(PublishingEvent)
class PublishingEventAdmin(admin.ModelAdmin):
    list_display = ("post", "action", "from_status", "to_status", "actor", "created_at")
    readonly_fields = ("post", "actor", "action", "from_status", "to_status", "reason", "created_at")

    def has_add_permission(self, request):
        return False
