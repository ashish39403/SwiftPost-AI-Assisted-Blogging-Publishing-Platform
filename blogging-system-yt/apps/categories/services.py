import uuid

from django.db import transaction

from apps.categories.models import Category
from apps.common.types import unique_slug


def create_category(*, name, description=""):
    name = name.strip()
    with transaction.atomic():
        category = Category(
            name=name,
            description=description.strip(),
            slug=f"pending-{uuid.uuid4().hex}",
        )
        category.save()
        category.slug = unique_slug(Category, name, instance=category, max_length=120)
        category.save(update_fields=["slug", "updated_at"])
    return category


def update_category(category, *, name=None, description=None, is_active=None):
    if name is not None:
        category.name = name.strip()
        category.slug = unique_slug(Category, category.name, instance=category, max_length=120)
    if description is not None:
        category.description = description.strip()
    if is_active is not None:
        category.is_active = is_active
    category.save()
    return category


def deactivate_category(category):
    category.is_active = False
    category.save(update_fields=["is_active", "updated_at"])
    return category
