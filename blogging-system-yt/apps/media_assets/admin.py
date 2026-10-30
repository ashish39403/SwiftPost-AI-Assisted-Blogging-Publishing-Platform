from django.contrib import admin

from apps.media_assets.models import MediaAsset


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "owner", "content_type", "byte_size", "width", "height")
    readonly_fields = (
        "owner",
        "post",
        "storage_key",
        "original_filename",
        "content_type",
        "byte_size",
        "width",
        "height",
        "created_at",
    )

    def has_add_permission(self, request):
        return False
