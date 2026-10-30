import logging
import threading
import time
from datetime import timedelta

from django.conf import settings
from django.db import close_old_connections, transaction
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

logger = logging.getLogger(__name__)
_ACTIVE_RUN_STATUSES = (JobStatus.QUEUED, JobStatus.RUNNING)
_STALE_AFTER = timedelta(minutes=5)
_STREAM_FLUSH_SECONDS = 0.45


def compose_from_title(*, actor, title, llm=None, conversation=None):
    run = _start_compose_run(actor=actor, title=title, conversation=conversation)
    _execute_compose_run(run.id, llm=llm)
    return ComposeRun.objects.select_related("post").prefetch_related("post__image_suggestions").get(pk=run.id)


def start_conversation_compose(*, actor, title, conversation=None):
    run = _start_compose_run(actor=actor, title=title, conversation=conversation)
    _schedule_compose_run(run.id)
    return owned_conversation(actor=actor, conversation_id=run.conversation_id)


def _start_compose_run(*, actor, title, conversation=None):
    if actor.role not in {Role.AUTHOR, Role.ADMIN}:
        raise PermissionDenied("You do not have permission to do that.")
    cleaned = (title or "").strip()
    if not cleaned:
        raise ValidationError({"title": "A title is required."})
    if len(cleaned) > 8000:
        raise ValidationError({"title": "The title is too long."})
    title_text = cleaned[:200]

    conversation = conversation or Conversation.objects.create(author=actor, title=title_text)
    if conversation.author_id != actor.id:
        raise PermissionDenied("You do not have permission to do that.")
    if conversation.status != ConversationStatus.ACTIVE:
        raise ValidationError({"conversation": "Archived conversations cannot be continued."})
    _assert_not_generating(conversation)
    _add_message(conversation, MessageRole.USER, cleaned)
    if not conversation.title:
        conversation.title = title_text
        conversation.save(update_fields=["title", "updated_at"])
    return ComposeRun.objects.create(
        author=actor,
        conversation=conversation,
        title_input=title_text,
        status=JobStatus.RUNNING,
    )


def list_conversations(*, actor, include_archived=False):
    queryset = Conversation.objects.filter(author=actor).select_related("post")
    if not include_archived:
        queryset = queryset.filter(status=ConversationStatus.ACTIVE)
    conversations = list(queryset.prefetch_related("messages", "post__image_suggestions", "compose_runs"))
    for conversation in conversations:
        _fail_stale_runs(conversation)
    return conversations


def owned_conversation(*, actor, conversation_id):
    try:
        conversation = Conversation.objects.select_related("post").prefetch_related("messages", "post__image_suggestions", "compose_runs").get(
            pk=conversation_id, author=actor
        )
        _fail_stale_runs(conversation)
        return conversation
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
    _assert_not_generating(conversation)
    _add_message(conversation, MessageRole.USER, cleaned)
    run = ComposeRun.objects.create(
        author=actor,
        conversation=conversation,
        title_input=cleaned[:200],
        status=JobStatus.RUNNING,
    )
    if llm is not None or getattr(settings, "COMPOSE_RUN_JOBS_INLINE", True):
        _execute_compose_run(run.id, llm=llm)
    else:
        _schedule_compose_run(run.id)
    return owned_conversation(actor=actor, conversation_id=conversation.id)


def _assert_not_generating(conversation):
    if conversation.compose_runs.filter(status__in=_ACTIVE_RUN_STATUSES).exists():
        raise ValidationError({"conversation": "Composer is still writing this draft."})


def _schedule_compose_run(run_id):
    if getattr(settings, "COMPOSE_RUN_JOBS_INLINE", True):
        _execute_compose_run(run_id)
        return

    def start():
        threading.Thread(
            target=_execute_compose_run_isolated,
            args=(run_id,),
            name=f"compose-run-{run_id}",
            daemon=True,
        ).start()

    connection = transaction.get_connection()
    if connection.in_atomic_block:
        transaction.on_commit(start)
    else:
        start()


def _execute_compose_run_isolated(run_id):
    close_old_connections()
    try:
        _execute_compose_run(run_id)
    except Exception:
        logger.exception("Composer background run %s failed", run_id)
    finally:
        close_old_connections()


def _execute_compose_run(run_id, llm=None):
    run = ComposeRun.objects.select_related("author", "conversation", "conversation__post").get(pk=run_id)
    conversation = run.conversation
    actor = run.author
    post = conversation.post
    prompt = run.title_input
    provider = llm or get_llm_provider()
    request = compose_request(
        prompt,
        current_title=post.title if post else "",
        current_excerpt=post.excerpt if post else "",
        current_body=post.body if post else "",
        instruction=prompt if post else "",
    )
    assistant = _add_message(conversation, MessageRole.ASSISTANT, "")
    collected = []
    try:
        for piece in _iter_compose_text(provider, request):
            collected.append(piece)
            _flush_assistant(assistant.pk, collected)
        text = "".join(collected).strip()
        _last_flush.pop(assistant.pk, None)
        if not text:
            raise ProviderUnavailable("The writing model returned empty text.")
        article = parse_article(text)
        formatted = _article_message(article)
        Message.objects.filter(pk=assistant.pk).update(content=formatted)
        with transaction.atomic():
            if article.get("refused"):
                _finish_run(run, article, model_name=_model_name(provider, request), post=None)
                return
            if post:
                update_draft(
                    post,
                    actor=actor,
                    changes={
                        "title": article["title"] or post.title,
                        "excerpt": article["excerpt"],
                        "body": article["body"],
                    },
                )
            else:
                post = create_draft(
                    author=actor,
                    title=(article["title"] or prompt)[:200],
                    excerpt=article["excerpt"],
                    body=article["body"],
                )
                conversation.post = post
                conversation.save(update_fields=["post", "updated_at"])
            _finish_run(run, article, model_name=_model_name(provider, request), post=post)
        if post:
            try:
                suggest_images_for_post(actor=actor, post=post, query=article["title"] or prompt)
            except Exception:
                pass
    except (ProviderNotConfigured, ProviderUnavailable, ValidationError) as exc:
        _keep_or_drop_assistant(assistant.pk, collected)
        _fail(run, exc)
        if getattr(settings, "COMPOSE_RUN_JOBS_INLINE", True):
            raise
    except Exception:
        _keep_or_drop_assistant(assistant.pk, collected)
        _fail(run, None)
        if getattr(settings, "COMPOSE_RUN_JOBS_INLINE", True):
            raise ProviderUnavailable("The writing model could not complete the request.")


def _iter_compose_text(provider, request):
    stream = getattr(provider, "stream", None)
    if callable(stream):
        yield from stream(request)
        return
    result = provider.generate(request)
    if result.text:
        yield result.text


_last_flush = {}


def _flush_assistant(message_id, chunks):
    now = time.monotonic()
    previous = _last_flush.get(message_id, 0)
    if now - previous < _STREAM_FLUSH_SECONDS:
        return
    _last_flush[message_id] = now
    Message.objects.filter(pk=message_id).update(content="".join(chunks))


def _keep_or_drop_assistant(message_id, chunks):
    text = "".join(chunks).strip()
    _last_flush.pop(message_id, None)
    if text:
        Message.objects.filter(pk=message_id).update(content=text)
    else:
        Message.objects.filter(pk=message_id).delete()


def _finish_run(run, article, *, model_name, post):
    run.post = post
    run.generated_title = article.get("title") or ""
    run.generated_excerpt = article.get("excerpt") or ""
    run.generated_body = article.get("body") or ""
    run.model_name = (model_name or "")[:80]
    run.status = JobStatus.SUCCEEDED
    run.finished_at = timezone.now()
    run.save()


def _model_name(provider, request):
    return getattr(settings, "AI_MODEL_COMPOSE", "") or getattr(request, "kind", "")


def _fail_stale_runs(conversation):
    cutoff = timezone.now() - _STALE_AFTER
    updated = conversation.compose_runs.filter(status__in=_ACTIVE_RUN_STATUSES, created_at__lt=cutoff).update(
        status=JobStatus.FAILED,
        error_message="The writing model took too long.",
        finished_at=timezone.now(),
    )
    if updated and hasattr(conversation, "_prefetched_objects_cache"):
        conversation._prefetched_objects_cache.pop("compose_runs", None)


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
