import io
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from rest_framework.exceptions import NotFound, ValidationError

from apps.accounts.models import Role
from apps.blogs.models import PostStatus
from apps.blogs.services import _require_author_edit
from apps.media_assets.models import MediaAsset
from apps.media_assets.storage import get_storage

_FORMATS = {
    "JPEG": ("image/jpeg", "jpg"),
    "PNG": ("image/png", "png"),
    "WEBP": ("image/webp", "webp"),
}
_DECLARED = {
    "image/jpeg": {"jpg", "jpeg"},
    "image/png": {"png"},
    "image/webp": {"webp"},
}
_DECLARED_ALIASES = {
    "image/jpg": "image/jpeg",
    "image/pjpeg": "image/jpeg",
    "image/x-png": "image/png",
    "image/x-webp": "image/webp",
}


def upload_featured_image(*, actor, post, upload):
    return upload_post_image(actor=actor, post=post, upload=upload, is_featured=True)


def upload_post_image(*, actor, post, upload, is_featured=False):
    _require_author_edit(post, actor)
    if not is_featured and post.images.count() >= 3:
        raise ValidationError({"images": "A story can have up to three images."})
    content, content_type, extension, width, height = _validated_image(upload)
    key = f"uploads/{uuid.uuid4().hex}.{extension}"
    storage = get_storage()
    storage.save(key, content, content_type)
    old_featured = _featured_asset(post) if is_featured else None
    old_key = old_featured.storage_key if old_featured else None
    try:
        with transaction.atomic():
            if old_featured:
                old_featured.delete()
            asset = MediaAsset.objects.create(
                owner=actor,
                post=post,
                is_featured=is_featured,
                storage_key=key,
                original_filename=_display_name(upload.name),
                content_type=content_type,
                byte_size=len(content),
                width=width,
                height=height,
            )
    except Exception:
        storage.delete(key)
        raise
    if old_key:
        storage.delete(old_key)
    return asset


def delete_featured_image(*, actor, asset):
    if asset.owner_id != actor.id:
        raise _missing()
    _require_author_edit(asset.post, actor)
    post = asset.post
    was_featured = asset.is_featured
    key = asset.storage_key
    asset.delete()
    if was_featured:
        replacement = post.images.first()
        if replacement:
            replacement.is_featured = True
            replacement.save(update_fields=["is_featured"])
    get_storage().delete(key)


def visible_asset(user, asset_id):
    try:
        asset = MediaAsset.objects.select_related("post", "owner").get(pk=asset_id)
    except MediaAsset.DoesNotExist:
        raise _missing() from None
    if asset.post.status == PostStatus.PUBLISHED:
        return asset
    if user.is_authenticated and (user.role == Role.ADMIN or asset.owner_id == user.id):
        return asset
    raise _missing()


def _validated_image(upload):
    if upload is None:
        raise ValidationError({"file": "An image file is required."})
    size = getattr(upload, "size", None)
    content = upload.read()
    if size is None:
        size = len(content)
    if size > settings.MAX_IMAGE_BYTES or len(content) > settings.MAX_IMAGE_BYTES:
        raise ValidationError({"file": "The image is too large."})
    if not content:
        raise ValidationError({"file": "The image is empty."})

    declared = (getattr(upload, "content_type", "") or "").split(";")[0].strip().lower()
    declared = _DECLARED_ALIASES.get(declared, declared)
    extension = Path(getattr(upload, "name", "") or "").suffix.lower().lstrip(".")
    try:
        Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_EDGE * settings.MAX_IMAGE_EDGE
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            detected = image.format
            width, height = image.size
    except (UnidentifiedImageError, DecompressionBombError, OSError):
        raise ValidationError({"file": "Upload a JPEG, PNG, or WebP image."}) from None

    if detected not in _FORMATS:
        raise ValidationError({"file": "Upload a JPEG, PNG, or WebP image."})
    content_type, stored_extension = _FORMATS[detected]
    if declared and declared not in {content_type, "application/octet-stream"}:
        raise ValidationError({"file": "The file contents do not match its type."})
    if extension and extension not in _DECLARED[content_type]:
        raise ValidationError({"file": "The file extension does not match its type."})
    if width < 1 or height < 1 or width > settings.MAX_IMAGE_EDGE or height > settings.MAX_IMAGE_EDGE:
        raise ValidationError({"file": "The image dimensions are not allowed."})
    return content, content_type, stored_extension, width, height


def _display_name(name):
    base = Path(name or "image").name.replace("\\", "/").split("/")[-1].strip()
    return (base or "image")[:120]


def replace_post_images(*, actor, post, uploads):
    """Replace a draft's image set with one to three validated uploads."""
    _require_author_edit(post, actor)
    if not uploads or len(uploads) > 3:
        raise ValidationError({"images": "Select one to three images."})
    old_assets = list(post.images.all())
    old_keys = [asset.storage_key for asset in old_assets]
    for asset in old_assets:
        asset.delete()
    saved = []
    try:
        for index, upload in enumerate(uploads):
            saved.append(upload_post_image(actor=actor, post=post, upload=upload, is_featured=index == 0))
    except Exception:
        for asset in saved:
            key = asset.storage_key
            asset.delete()
            get_storage().delete(key)
        raise
    for key in old_keys:
        get_storage().delete(key)
    return saved


def _featured_asset(post):
    return post.images.filter(is_featured=True).first()


def _missing():
    exc = NotFound("The requested media could not be found.")
    exc.api_code = "MEDIA_NOT_FOUND"
    return exc


@receiver(pre_delete, sender="blogs.Post")
def delete_post_file(sender, instance, **kwargs):
    for key in instance.images.values_list("storage_key", flat=True):
        get_storage().delete(key)
