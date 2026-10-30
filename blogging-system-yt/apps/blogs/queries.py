from django.db.models import Q
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.accounts.models import Role
from apps.blogs.models import Post, PostStatus


def published_posts(params):
    queryset = Post.objects.filter(status=PostStatus.PUBLISHED).select_related("author", "category").prefetch_related("images")
    category = (params.get("category") or "").strip()
    if category:
        queryset = queryset.filter(category__slug=category, category__is_active=True)
    return _search(queryset, params).order_by("-published_at", "-id")


def visible_private_posts(user, params):
    if user.role == Role.ADMIN:
        queryset = Post.objects.all()
    elif user.role == Role.AUTHOR:
        queryset = Post.objects.filter(author=user)
    else:
        raise PermissionDenied("You do not have permission to do that.")

    status = (params.get("status") or "").strip()
    if status:
        if status not in PostStatus.values:
            raise ValidationError({"status": "Unknown status."})
        queryset = queryset.filter(status=status)
    else:
        queryset = queryset.exclude(status=PostStatus.ARCHIVED)
    return _search(queryset, params).select_related("author", "category").prefetch_related("images").order_by(
        "-updated_at", "-id"
    )


def get_private_post(user, post_id):
    post = _get_post(post_id)
    if user.role == Role.ADMIN:
        return post
    if user.role == Role.AUTHOR and post.author_id == user.id:
        return post
    raise post_not_found()


def get_published_post(post_id):
    lookup = {"status": PostStatus.PUBLISHED}
    if str(post_id).isdigit():
        lookup["pk"] = post_id
    else:
        lookup["slug"] = post_id
    try:
        return Post.objects.select_related("author", "category").prefetch_related("images").get(**lookup)
    except Post.DoesNotExist:
        raise post_not_found() from None


def post_not_found():
    exc = NotFound("The requested post could not be found.")
    exc.api_code = "POST_NOT_FOUND"
    return exc


def _get_post(post_id):
    try:
        return Post.objects.select_related("author", "category").prefetch_related("images").get(pk=post_id)
    except Post.DoesNotExist:
        raise post_not_found() from None


def _search(queryset, params):
    term = (params.get("search") or "").strip()
    if not term:
        return queryset
    return queryset.filter(
        Q(title__icontains=term) | Q(excerpt__icontains=term) | Q(body__icontains=term)
    )
