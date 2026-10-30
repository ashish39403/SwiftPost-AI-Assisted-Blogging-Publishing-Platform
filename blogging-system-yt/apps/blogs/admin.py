from django.contrib import admin

from apps.blogs.models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "category", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "slug", "author__email", "author__username")
    readonly_fields = ("slug", "created_at", "updated_at")
