"""Shared id and slug helpers."""

from django.utils.text import slugify


def unique_slug(model, value, *, instance=None, max_length=180):
    base = (slugify(value) or "item")[:max_length].strip("-") or "item"
    slug = base
    number = 2
    queryset = model.objects.all()
    if instance is not None and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(slug=slug).exists():
        suffix = f"-{number}"
        slug = f"{base[: max_length - len(suffix)]}{suffix}"
        number += 1
    return slug
