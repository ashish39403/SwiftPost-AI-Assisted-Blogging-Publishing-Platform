from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.blogs.models import PostStatus
from apps.blogs.queries import get_published_post, post_not_found
from apps.comments.models import Comment, CommentStatus, PostLike


def public_comments(post):
    return post.comments.filter(status=CommentStatus.APPROVED).select_related("author")


def create_comment(*, actor, post, body):
    if not actor.is_authenticated or not actor.is_active:
        raise PermissionDenied("You do not have permission to do that.")
    if post.status != PostStatus.PUBLISHED:
        raise post_not_found()
    cleaned = (body or "").strip()
    if not cleaned:
        raise ValidationError({"body": "Write a comment."})
    if len(cleaned) > 2000:
        raise ValidationError({"body": "That comment is too long."})
    return Comment.objects.create(
        post=post,
        author=actor,
        body=cleaned,
        status=CommentStatus.APPROVED,
    )


def get_comment(comment_id):
    try:
        return Comment.objects.select_related("post", "author").get(pk=comment_id)
    except Comment.DoesNotExist:
        exc = NotFound("The requested comment could not be found.")
        exc.api_code = "COMMENT_NOT_FOUND"
        raise exc from None


def moderate_comment(*, actor, comment, status):
    if actor.role != Role.ADMIN and comment.post.author_id != actor.id:
        raise PermissionDenied("You do not have permission to do that.")
    comment.status = status
    comment.save(update_fields=["status", "updated_at"])
    return comment


def delete_comment(*, actor, comment):
    if actor.role != Role.ADMIN and comment.author_id != actor.id:
        raise PermissionDenied("You do not have permission to do that.")
    comment.delete()


def like_state(*, user, post):
    if post.status != PostStatus.PUBLISHED:
        raise post_not_found()
    count = post.likes.count()
    liked = bool(user and user.is_authenticated and post.likes.filter(user=user).exists())
    return {"count": count, "liked": liked}


def toggle_like(*, actor, post):
    if post.status != PostStatus.PUBLISHED:
        raise post_not_found()
    like, created = PostLike.objects.get_or_create(post=post, user=actor)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return {"count": post.likes.count(), "liked": liked}


def require_published(post_id):
    return get_published_post(post_id)
