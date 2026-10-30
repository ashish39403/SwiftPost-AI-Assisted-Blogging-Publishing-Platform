from django.conf import settings
from django.db import models


class MediaAsset(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="media_assets",
    )
    post = models.ForeignKey(
        "blogs.Post",
        on_delete=models.CASCADE,
        related_name="images",
    )
    is_featured = models.BooleanField(default=False)
    storage_key = models.CharField(max_length=255, unique=True)
    original_filename = models.CharField(max_length=120)
    content_type = models.CharField(max_length=40)
    byte_size = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename

    class Meta:
        ordering = ["is_featured", "created_at", "id"]


class ImageSuggestion(models.Model):
    post = models.ForeignKey(
        "blogs.Post",
        on_delete=models.CASCADE,
        related_name="image_suggestions",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="image_suggestions",
    )
    image_url = models.URLField(max_length=1000)
    page_url = models.URLField(max_length=1000, blank=True)
    description = models.CharField(max_length=300, blank=True)
    selected = models.BooleanField(default=False)
    retrieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-retrieved_at", "-id"]
