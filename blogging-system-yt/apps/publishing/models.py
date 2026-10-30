from django.conf import settings
from django.db import models


class PublishingAction(models.TextChoices):
    SUBMIT = "submit", "Submit"
    PUBLISH = "publish", "Publish"
    UNPUBLISH = "unpublish", "Unpublish"
    ARCHIVE = "archive", "Archive"


class PublishingEvent(models.Model):
    post = models.ForeignKey(
        "blogs.Post",
        on_delete=models.CASCADE,
        related_name="publishing_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="publishing_events",
    )
    action = models.CharField(max_length=32, choices=PublishingAction.choices)
    from_status = models.CharField(max_length=32)
    to_status = models.CharField(max_length=32)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.from_status} -> {self.to_status}"
