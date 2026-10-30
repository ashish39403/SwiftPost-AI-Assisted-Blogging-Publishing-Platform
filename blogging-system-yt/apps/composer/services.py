from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import Role
from apps.anna.exceptions import ProviderNotConfigured, ProviderUnavailable
from apps.anna.orchestration.generation import compose_request
from apps.anna.providers import get_llm_provider
from apps.blogs.services import create_draft, update_draft
from apps.composer.models import ComposeRun, Conversation, ConversationStatus, JobStatus, Message, MessageRole
from apps.composer.parsers import parse_article
from apps.media_assets.image_search import suggest_images_for_post


def compose_from_title(*, actor, title, llm=None, conversation=None):
    if actor.role not in {Role.AUTHOR, Role.ADMIN}:
        raise PermissionDenied("You do not have permission to do that.")
    cleaned = (title or "").strip()
    if not cleaned:
        raise ValidationError({"title": "A title is required."})
    if len(cleaned) > 8000:
        raise ValidationError({"title": "The title is too long."})
    title_text = cleaned[:200]

    provider = llm or get_llm_provider()
    conversation = conversation or Conversation.objects.create(author=actor, title=title_text)
    if conversation.author_id != actor.id:
        raise PermissionDenied("You do not have permission to do that.")
    if conversation.status != ConversationStatus.ACTIVE:
        raise ValidationError({"conversation": "Archived conversations cannot be continued."})
    _add_message(conversation, MessageRole.USER, cleaned)
    if not conversation.title:
        conversation.title = title_text
        conversation.save(update_fields=["title", "updated_at"])
    run = ComposeRun.objects.create(
        author=actor,
        conversation=conversation,
        title_input=title_text,
        status=JobStatus.RUNNING,
    )
    try:
        result = provider.generate(compose_request(cleaned))
        article = parse_article(result.text)
        with transaction.atomic():
            post = None
            if not article.get("refused"):
                post = create_draft(
                    author=actor,
                    title=(article["title"] or title_text)[:200],
                    excerpt=article["excerpt"],
                    body=article["body"],
                )
                conversation.post = post
                conversation.save(update_fields=["post", "updated_at"])
            run.post = post
            run.generated_title = article["title"]
            run.generated_excerpt = article["excerpt"]
            run.generated_body = article["body"]
            run.model_name = result.model[:80]
            run.status = JobStatus.SUCCEEDED
            run.finished_at = timezone.now()
            run.save()
            _add_message(conversation, MessageRole.ASSISTANT, _article_message(article))
        if post:
            try:
                suggest_images_for_post(actor=actor, post=post, query=article["title"] or title_text)
            except Exception:
                pass
    except (ProviderNotConfigured, ProviderUnavailable, ValidationError) as exc:
        _fail(run, exc)
        raise
    except Exception:
        _fail(run, None)
        raise ProviderUnavailable("The writing model could not complete the request.")
    return run


def list_conversations(*, actor, include_archived=False):
    queryset = Conversation.objects.filter(author=actor).select_related("post")
    if not include_archived:
        queryset = queryset.filter(status=ConversationStatus.ACTIVE)
    return queryset.prefetch_related("messages", "post__image_suggestions")


def owned_conversation(*, actor, conversation_id):
    try:
        return Conversation.objects.select_related("post").prefetch_related("messages", "post__image_suggestions").get(
            pk=conversation_id, author=actor
        )
    except Conversation.DoesNotExist:
        from rest_framework.exceptions import NotFound

        exc = NotFound("The requested conversation could not be found.")
        exc.api_code = "CONVERSATION_NOT_FOUND"
        raise exc


def create_conversation(*, actor, title=""):
    if actor.role not in {Role.AUTHOR, Role.ADMIN}:
        raise PermissionDenied("You do not have permission to do that.")
    return Conversation.objects.create(author=actor, title=(title or "").strip()[:200])


def create_handoff_conversation(*, actor, content):
    cleaned = (content or "").strip()
    if not cleaned:
        raise ValidationError({"content": "A message is required."})
    conversation = create_conversation(actor=actor, title=cleaned[:200])
    _add_message(conversation, MessageRole.USER, cleaned)
    return owned_conversation(actor=actor, conversation_id=conversation.id)


def rename_conversation(*, actor, conversation_id, title):
    conversation = owned_conversation(actor=actor, conversation_id=conversation_id)
    cleaned = (title or "").strip()
    if not cleaned:
        raise ValidationError({"title": "A conversation title is required."})
    conversation.title = cleaned[:200]
    conversation.save(update_fields=["title", "updated_at"])
    return conversation


def archive_conversation(*, actor, conversation_id):
    conversation = owned_conversation(actor=actor, conversation_id=conversation_id)
    conversation.status = ConversationStatus.ARCHIVED
    conversation.save(update_fields=["status", "updated_at"])
    return conversation


def continue_conversation(*, actor, conversation_id, content, llm=None):
    conversation = owned_conversation(actor=actor, conversation_id=conversation_id)
    cleaned = (content or "").strip()
    if not cleaned:
        raise ValidationError({"content": "A message is required."})
    if conversation.status != ConversationStatus.ACTIVE:
        raise ValidationError({"conversation": "Archived conversations cannot be continued."})
    _add_message(conversation, MessageRole.USER, cleaned)
    provider = llm or get_llm_provider()
    try:
        post = conversation.post
        result = provider.generate(
            compose_request(
                cleaned,
                current_title=post.title if post else "",
                current_excerpt=post.excerpt if post else "",
                current_body=post.body if post else "",
                instruction=cleaned,
            )
        )
        article = parse_article(result.text)
        if article.get("refused"):
            _add_message(conversation, MessageRole.ASSISTANT, _article_message(article))
            return owned_conversation(actor=actor, conversation_id=conversation.id)
        if post:
            update_draft(
                post,
                actor=actor,
                changes={"title": article["title"] or post.title, "excerpt": article["excerpt"], "body": article["body"]},
            )
        else:
            post = create_draft(
                author=actor,
                title=article["title"] or cleaned,
                excerpt=article["excerpt"],
                body=article["body"],
            )
            conversation.post = post
            conversation.save(update_fields=["post", "updated_at"])
        _add_message(conversation, MessageRole.ASSISTANT, _article_message(article))
        try:
            # Each Composer request gets a fresh, topic-relevant image set. Saved
            # assets are separate from suggestions, so a new search never removes
            # a user's selected draft images.
            suggest_images_for_post(actor=actor, post=post, query=article["title"] or cleaned)
        except Exception:
            pass
    except (ProviderNotConfigured, ProviderUnavailable, ValidationError):
        raise
    except Exception:
        raise ProviderUnavailable("The writing model could not complete the request.")
    return owned_conversation(actor=actor, conversation_id=conversation.id)


def owned_run(actor, run_id):
    try:
        run = ComposeRun.objects.select_related("post").prefetch_related("post__image_suggestions").get(
            pk=run_id, author=actor
        )
    except ComposeRun.DoesNotExist:
        from rest_framework.exceptions import NotFound

        exc = NotFound("The requested draft could not be found.")
        exc.api_code = "COMPOSE_NOT_FOUND"
        raise exc
    return run


def _fail(run, exc):
    message = "The article could not be written."
    if isinstance(exc, ValidationError):
        detail = exc.detail
        if isinstance(detail, dict):
            first = next(iter(detail.values()), message)
            message = str(first[0] if isinstance(first, list) else first)
        else:
            message = str(detail)
    elif isinstance(exc, (ProviderNotConfigured, ProviderUnavailable)):
        message = str(exc.detail if hasattr(exc, "detail") else exc)
    run.status = JobStatus.FAILED
    run.error_message = message[:240]
    run.finished_at = timezone.now()
    run.save(update_fields=["status", "error_message", "finished_at"])


def _article_message(article):
    parts = [article.get("title"), article.get("excerpt"), article.get("body")]
    if article.get("refused"):
        parts = [article.get("body") or "I cannot help with that request."]
    return "\n\n".join(part for part in parts if part)


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
