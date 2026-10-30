from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.anna.tools.live_search import collect_images
from apps.blogs.queries import get_private_post
from apps.media_assets.fetch import download_image, public_http_url
from apps.media_assets.models import ImageSuggestion
from apps.media_assets.services import replace_post_images, upload_featured_image


def suggest_images_for_post(*, actor, post, query, limit=6, attach=False):
    cleaned = (query or post.title or "").strip()
    if not cleaned:
        return []
    results = collect_images(cleaned, limit=max(1, min(int(limit or 6), 6)))
    ImageSuggestion.objects.filter(post=post, author=actor).delete()
    created = []
    for item in results:
        try:
            public_http_url(item.url, resolve=False)
        except ValidationError:
            continue
        created.append(
            ImageSuggestion.objects.create(
                post=post,
                author=actor,
                image_url=item.url[:1000],
                page_url=(item.page_url or "")[:1000],
                description=(item.description or "")[:300],
            )
        )
        if len(created) >= 3:
            break
    if attach:
        attach_top_image_suggestions(actor=actor, post=post, suggestions=created)
    return created


def attach_top_image_suggestions(*, actor, post, suggestions):
    uploads = []
    selected_ids = []
    for suggestion in suggestions[:3]:
        try:
            uploads.append(download_image(suggestion.image_url))
            selected_ids.append(suggestion.id)
        except Exception:
            continue
    if not uploads:
        return []
    assets = replace_post_images(actor=actor, post=post, uploads=uploads)
    ImageSuggestion.objects.filter(post=post, author=actor).update(selected=False)
    if selected_ids:
        ImageSuggestion.objects.filter(pk__in=selected_ids).update(selected=True)
    return assets


def search_images_for_draft(*, actor, post_id, query=""):
    post = get_private_post(actor, post_id)
    return suggest_images_for_post(actor=actor, post=post, query=query or post.title)


def listed_suggestions(*, actor, post_id):
    post = get_private_post(actor, post_id)
    return post.image_suggestions.filter(author=actor)


def attach_suggested_image(*, actor, suggestion_id):
    try:
        suggestion = ImageSuggestion.objects.select_related("post").get(pk=suggestion_id)
    except ImageSuggestion.DoesNotExist:
        exc = NotFound("The requested image could not be found.")
        exc.api_code = "MEDIA_NOT_FOUND"
        raise exc from None
    if suggestion.author_id != actor.id:
        raise PermissionDenied("You do not have permission to do that.")
    post = get_private_post(actor, suggestion.post_id)
    upload = download_image(suggestion.image_url)
    return upload_featured_image(actor=actor, post=post, upload=upload)


def save_suggested_images(*, actor, suggestion_ids):
    unique_ids = list(dict.fromkeys(suggestion_ids))
    if not unique_ids or len(unique_ids) > 3:
        raise ValidationError({"ids": "Select one to three images."})
    suggestions = list(ImageSuggestion.objects.select_related("post").filter(pk__in=unique_ids, author=actor))
    if len(suggestions) != len(unique_ids):
        exc = NotFound("The requested image could not be found.")
        exc.api_code = "MEDIA_NOT_FOUND"
        raise exc
    by_id = {suggestion.id: suggestion for suggestion in suggestions}
    selected = [by_id[suggestion_id] for suggestion_id in unique_ids]
    post_id = selected[0].post_id
    if any(suggestion.post_id != post_id for suggestion in selected):
        raise ValidationError({"ids": "Choose images from one story at a time."})
    post = get_private_post(actor, post_id)
    uploads = [download_image(suggestion.image_url) for suggestion in selected]
    assets = replace_post_images(actor=actor, post=post, uploads=uploads)
    ImageSuggestion.objects.filter(post=post, author=actor).update(selected=False)
    ImageSuggestion.objects.filter(pk__in=unique_ids).update(selected=True)
    return {"featured": assets[0], "images": assets, "selected": selected}
