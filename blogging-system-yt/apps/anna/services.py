from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.accounts.models import Role
from apps.anna.exceptions import ProviderNotConfigured, ProviderUnavailable
from apps.anna.models import Conversation, ConversationStatus, JobStatus, Message, MessageRole, ReviewRun
from apps.anna.orchestration.generation import review_request
from apps.anna.providers import get_llm_provider
from apps.blogs.queries import get_private_post


def review_owned_draft(*, actor, post_id, llm=None, conversation=None, prompt=""):
    if actor.role not in {Role.AUTHOR, Role.ADMIN}:
        raise PermissionDenied("You do not have permission to do that.")
    post = get_private_post(actor, post_id)
    if post.author_id != actor.id:
        exc = NotFound("The requested post could not be found.")
        exc.api_code = "POST_NOT_FOUND"
        raise exc
    if not post.title.strip() or not post.body.strip():
        raise ValidationError({"post": "The draft needs a title and body before Anna can review it."})

    provider = llm or get_llm_provider()
    conversation = conversation or Conversation.objects.create(author=actor, post=post, title=post.title[:200])
    if conversation.author_id != actor.id:
        raise PermissionDenied("You do not have permission to do that.")
    if conversation.status != ConversationStatus.ACTIVE:
        raise ValidationError({"conversation": "Archived conversations cannot be continued."})
    _add_message(conversation, MessageRole.USER, (prompt or f"Review: {post.title}").strip())
    run = ReviewRun.objects.create(author=actor, conversation=conversation, post=post, status=JobStatus.RUNNING)
    try:
        result = provider.generate(review_request(post.title, post.excerpt, post.body))
        notes = result.text.strip()
        if not notes:
            raise ProviderUnavailable("Anna returned an empty review.")
        run.notes = notes
        run.model_name = result.model[:80]
        run.status = JobStatus.SUCCEEDED
        run.finished_at = timezone.now()
        run.save()
        _add_message(conversation, MessageRole.ASSISTANT, notes)
    except (ProviderNotConfigured, ProviderUnavailable, ValidationError) as exc:
        run.status = JobStatus.FAILED
        run.error_message = "Anna could not finish the review."[:240]
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error_message", "finished_at"])
        raise
    except Exception:
        run.status = JobStatus.FAILED
        run.error_message = "Anna could not finish the review."
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error_message", "finished_at"])
        raise ProviderUnavailable("Anna could not finish the review.")
    return run


def list_conversations(*, actor, include_archived=False):
    queryset = Conversation.objects.filter(author=actor).select_related("post")
    if not include_archived:
        queryset = queryset.filter(status=ConversationStatus.ACTIVE)
    return queryset.prefetch_related("messages")


def owned_conversation(*, actor, conversation_id):
    try:
        return Conversation.objects.select_related("post").prefetch_related("messages").get(
            pk=conversation_id, author=actor
        )
    except Conversation.DoesNotExist:
        exc = NotFound("The requested conversation could not be found.")
        exc.api_code = "CONVERSATION_NOT_FOUND"
        raise exc


def create_conversation(*, actor, post_id=None, title=""):
    if actor.role not in {Role.AUTHOR, Role.ADMIN}:
        raise PermissionDenied("You do not have permission to do that.")
    post = get_private_post(actor, post_id) if post_id else None
    return Conversation.objects.create(author=actor, post=post, title=(title or (post.title if post else "")).strip()[:200])


def archive_conversation(*, actor, conversation_id):
    conversation = owned_conversation(actor=actor, conversation_id=conversation_id)
    conversation.status = ConversationStatus.ARCHIVED
    conversation.save(update_fields=["status", "updated_at"])
    return conversation


def continue_conversation(*, actor, conversation_id, content, llm=None):
    conversation = owned_conversation(actor=actor, conversation_id=conversation_id)
    if not conversation.post_id:
        raise ValidationError({"post": "Choose a draft before asking Anna for a review."})
    return review_owned_draft(
        actor=actor,
        post_id=conversation.post_id,
        llm=llm,
        conversation=conversation,
        prompt=content,
    )


def continue_in_composer(*, actor, message_id):
    try:
        message = Message.objects.select_related("conversation").get(
            pk=message_id,
            conversation__author=actor,
            role=MessageRole.ASSISTANT,
        )
    except Message.DoesNotExist:
        exc = NotFound("The requested message could not be found.")
        exc.api_code = "MESSAGE_NOT_FOUND"
        raise exc
    from apps.composer.services import create_handoff_conversation

    return create_handoff_conversation(actor=actor, content=message.content)


def _add_message(conversation, role, content):
    with transaction.atomic():
        locked = Conversation.objects.select_for_update().get(pk=conversation.pk)
        last_sequence = Message.objects.filter(conversation=locked).aggregate(value=Max("sequence"))["value"] or 0
        message = Message.objects.create(
            conversation=locked,
            role=role,
            content=content,
            sequence=last_sequence + 1,
        )
        Conversation.objects.filter(pk=locked.pk).update(updated_at=timezone.now())
    return message
