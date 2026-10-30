import uuid

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import Role
from apps.blogs.models import Post, PostStatus
from apps.common.types import unique_slug

_EDITABLE = {
    PostStatus.DRAFT,
    PostStatus.CHANGES_REQUESTED,
    PostStatus.UNPUBLISHED,
}


def create_draft(*, author, title="", excerpt="", body="", category=None):
    if author.role not in {Role.AUTHOR, Role.ADMIN}:
        raise PermissionDenied("You do not have permission to do that.")
    with transaction.atomic():
        post = Post.objects.create(
            author=author,
            category=category,
            title=title.strip(),
            excerpt=excerpt.strip(),
            body=body,
            slug=f"pending-{uuid.uuid4().hex}",
            status=PostStatus.DRAFT,
        )
        post.slug = unique_slug(Post, title or f"draft-{post.pk}", instance=post, max_length=220)
        post.save(update_fields=["slug", "updated_at"])
    return post


def update_draft(post, *, actor, changes):
    _require_author_edit(post, actor)
    if "title" in changes:
        post.title = changes["title"].strip()
        if post.status != PostStatus.PUBLISHED:
            post.slug = unique_slug(Post, post.title or f"draft-{post.pk}", instance=post, max_length=220)
    if "excerpt" in changes:
        post.excerpt = changes["excerpt"].strip()
    if "body" in changes:
        post.body = changes["body"]
    if "category" in changes:
        post.category = changes["category"]
    post.save()
    return post


def delete_draft(post, *, actor):
    _require_author_edit(post, actor)
    if post.status != PostStatus.DRAFT:
        raise ValidationError({"status": "Only a draft can be deleted. Archive it instead."})
    post.delete()


def _require_author_edit(post, actor):
    if actor.role != Role.AUTHOR or post.author_id != actor.id:
        raise PermissionDenied("You do not have permission to do that.")
    if post.status not in _EDITABLE:
        raise ValidationError({"status": "This post cannot be edited in its current state."})
