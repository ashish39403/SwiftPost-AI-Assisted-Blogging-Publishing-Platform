from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from apps.accounts.models import Role
from apps.blogs.models import Post, PostStatus
from apps.publishing.models import PublishingAction, PublishingEvent

_WRITABLE = {
    PostStatus.DRAFT,
    PostStatus.CHANGES_REQUESTED,
    PostStatus.UNPUBLISHED,
    PostStatus.IN_REVIEW,
}
_TRANSITIONS = {
    PublishingAction.SUBMIT: {
        Role.AUTHOR: {
            PostStatus.DRAFT: PostStatus.IN_REVIEW,
            PostStatus.CHANGES_REQUESTED: PostStatus.IN_REVIEW,
            PostStatus.UNPUBLISHED: PostStatus.IN_REVIEW,
        }
    },
    PublishingAction.PUBLISH: {
        Role.AUTHOR: {status: PostStatus.PUBLISHED for status in _WRITABLE},
        Role.ADMIN: {status: PostStatus.PUBLISHED for status in _WRITABLE},
    },
    PublishingAction.UNPUBLISH: {
        Role.AUTHOR: {PostStatus.PUBLISHED: PostStatus.UNPUBLISHED},
        Role.ADMIN: {PostStatus.PUBLISHED: PostStatus.UNPUBLISHED},
    },
    PublishingAction.ARCHIVE: {
        Role.AUTHOR: {
            PostStatus.DRAFT: PostStatus.ARCHIVED,
            PostStatus.IN_REVIEW: PostStatus.ARCHIVED,
            PostStatus.CHANGES_REQUESTED: PostStatus.ARCHIVED,
            PostStatus.UNPUBLISHED: PostStatus.ARCHIVED,
        },
        Role.ADMIN: {
            PostStatus.DRAFT: PostStatus.ARCHIVED,
            PostStatus.IN_REVIEW: PostStatus.ARCHIVED,
            PostStatus.CHANGES_REQUESTED: PostStatus.ARCHIVED,
            PostStatus.UNPUBLISHED: PostStatus.ARCHIVED,
        },
    },
}


class InvalidTransition(APIException):
    status_code = 400
    default_detail = "That status change is not allowed."
    api_code = "INVALID_TRANSITION"


def transition(*, post, actor, action, reason=""):
    allowed = _TRANSITIONS[action].get(actor.role, {})
    new_status = allowed.get(post.status)
    if new_status is None or not _actor_may_touch(post, actor, action):
        if actor.role not in _TRANSITIONS[action] or not _actor_may_touch(post, actor, action):
            raise PermissionDenied("You do not have permission to do that.")
        raise InvalidTransition()

    if action in {PublishingAction.SUBMIT, PublishingAction.PUBLISH}:
        _require_complete(post)

    now = timezone.now()
    previous = post.status
    post.status = new_status
    if new_status == PostStatus.IN_REVIEW:
        post.submitted_at = now
    elif new_status == PostStatus.PUBLISHED:
        post.published_at = now
    elif new_status == PostStatus.UNPUBLISHED:
        post.unpublished_at = now

    with transaction.atomic():
        post.save()
        PublishingEvent.objects.create(
            post=post,
            actor=actor,
            action=action,
            from_status=previous,
            to_status=new_status,
            reason=reason.strip(),
        )
    return post


def _actor_may_touch(post, actor, action):
    if actor.role == Role.ADMIN and action in {
        PublishingAction.PUBLISH,
        PublishingAction.UNPUBLISH,
        PublishingAction.ARCHIVE,
    }:
        return True
    return actor.role == Role.AUTHOR and post.author_id == actor.id


def _require_complete(post):
    details = {}
    if not post.title.strip():
        details["title"] = "Title is required before publishing."
    if not post.excerpt.strip():
        details["excerpt"] = "Excerpt is required before publishing."
    if not post.body.strip():
        details["body"] = "Body is required before publishing."
    if post.category_id is None or not post.category.is_active:
        details["category"] = "An active category is required before publishing."
    if details:
        raise ValidationError(details)
