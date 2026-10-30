import uuid

from django.conf import settings
from django.db import models


class JobStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"


class MessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"
    TOOL = "tool", "Tool"


class ConversationStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="anna_conversations",
    )
    post = models.ForeignKey(
        "blogs.Post",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anna_conversations",
    )
    title = models.CharField(max_length=200, blank=True)
    memory_summary = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ConversationStatus.choices, default=ConversationStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["author", "status", "updated_at"], name="anna_conver_author__6330de_idx")]


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=MessageRole.choices)
    content = models.TextField()
    sequence = models.PositiveIntegerField()
    used_search = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sequence", "created_at"]
        unique_together = ("conversation", "sequence")


class ReviewRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="anna_reviews",
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review_runs",
    )
    post = models.ForeignKey(
        "blogs.Post",
        on_delete=models.CASCADE,
        related_name="anna_reviews",
    )
    notes = models.TextField(blank=True)
    model_name = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.QUEUED)
    error_message = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
