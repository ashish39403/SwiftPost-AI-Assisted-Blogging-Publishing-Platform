import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

if not os.environ.get("DJANGO_SECRET_KEY"):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required in production.")
if not os.environ.get("DJANGO_ALLOWED_HOSTS"):
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS is required in production.")
if not os.environ.get("DATABASE_URL"):
    raise ImproperlyConfigured("DATABASE_URL is required in production.")
if not CSRF_TRUSTED_ORIGINS:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_CSRF_TRUSTED_ORIGINS is required in production.")
if os.environ.get("MEDIA_STORAGE") != "s3":
    raise ImproperlyConfigured("MEDIA_STORAGE=s3 is required in production.")
if not os.environ.get("AWS_S3_BUCKET") or not os.environ.get("AWS_S3_PUBLIC_BASE_URL"):
    raise ImproperlyConfigured("AWS_S3_BUCKET and AWS_S3_PUBLIC_BASE_URL are required in production.")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
