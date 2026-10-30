import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes"}
if not SECRET_KEY:  # noqa: F405
    SECRET_KEY = "dev-only-change-me"  # noqa: F405

if not DEBUG and not os.environ.get("DJANGO_SECRET_KEY"):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required when DJANGO_DEBUG is off.")
