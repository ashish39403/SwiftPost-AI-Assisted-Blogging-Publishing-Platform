from django.conf import settings
from django.db import models


class PostStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    IN_REVIEW = "in_review", "In review"
    CHANGES_REQUESTED = "changes_requested", "Changes requested"
    PUBLISHED = "published", "Published"
    UNPUBLISHED = "unpublished", "Unpublished"
    ARCHIVED = "archived", "Archived"


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="posts",
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="posts",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=220, unique=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField(blank=True)
    status = models.CharField(
        max_length=32,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    unpublished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["author", "status"]),
        ]

    def __str__(self):
        return self.title or f"Post {self.pk}"
