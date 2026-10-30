"""Shared SwiftPost settings.

Secrets and environment-specific hosts live in the environment, not in this file.
Local development defaults to SQLite. Set DATABASE_URL to a PostgreSQL URL for
production or for a production-parity check.
"""

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _csv_env(name, default=""):
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _database_from_env():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme in {"postgres", "postgresql"}:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path.lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
        }
    raise RuntimeError("DATABASE_URL must be empty or a postgres/postgresql URL.")


FRONTEND_ORIGINS = _csv_env("FRONTEND_ORIGIN", "http://localhost:3000")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = False
ALLOWED_HOSTS = _csv_env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "apps.accounts",
    "apps.users",
    "apps.blogs",
    "apps.categories",
    "apps.comments",
    "apps.publishing",
    "apps.moderation",
    "apps.media_assets",
    "apps.composer",
    "apps.anna",
    "apps.common",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
]

MIDDLEWARE = [
    "apps.common.middleware.ApiSlashMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "apps.accounts.middleware.TabSessionMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {"default": _database_from_env()}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_STORAGE = os.environ.get("MEDIA_STORAGE", "local")
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", str(5 * 1024 * 1024)))
MAX_IMAGE_EDGE = int(os.environ.get("MAX_IMAGE_EDGE", "4000"))
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_IMAGE_BYTES + 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_IMAGE_BYTES + 1024 * 1024
AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "")
AWS_S3_REGION = os.environ.get("AWS_REGION", "")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL") or None
AWS_S3_PUBLIC_BASE_URL = os.environ.get("AWS_S3_PUBLIC_BASE_URL", "")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")


def _clean_env(name, default=""):
    return os.environ.get(name, default).strip().strip('"').strip("'")


AI_PROVIDER = _clean_env("AI_PROVIDER")
AI_MODEL = _clean_env("AI_MODEL")
AI_MODEL_COMPOSE = _clean_env("AI_MODEL_COMPOSE")
AI_MODEL_REVIEW = _clean_env("AI_MODEL_REVIEW")
AI_PROVIDER_API_KEY = _clean_env("AI_PROVIDER_API_KEY")
AI_PROVIDER_BASE_URL = _clean_env("AI_PROVIDER_BASE_URL").rstrip("/")
if AI_PROVIDER_BASE_URL in {"https://aicredits.in/v1", "http://aicredits.in/v1", "https://aicredits.in"}:
    AI_PROVIDER_BASE_URL = "https://api.aicredits.in/v1"
SEARCH_PROVIDER = os.environ.get("SEARCH_PROVIDER", "").strip()
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "").strip()
TAVILY_MAX_RESULTS = min(int(os.environ.get("TAVILY_MAX_RESULTS", "5")), 10)
TAVILY_TEST_BUDGET = int(os.environ.get("TAVILY_TEST_BUDGET", "12"))
ANNA_RUN_JOBS_INLINE = os.environ.get("ANNA_RUN_JOBS_INLINE", "true").lower() in {
    "1",
    "true",
    "yes",
}

CORS_ALLOWED_ORIGINS = _csv_env("DJANGO_CORS_ALLOWED_ORIGINS", ",".join(FRONTEND_ORIGINS))
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [*default_headers, "x-session-key"]
CORS_EXPOSE_HEADERS = ["X-Session-Key"]
CSRF_TRUSTED_ORIGINS = _csv_env("DJANGO_CSRF_TRUSTED_ORIGINS", ",".join(FRONTEND_ORIGINS))

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = os.environ.get("CSRF_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_FAILURE_VIEW = "apps.common.csrf.csrf_failure"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "apps.accounts.permissions.IsAuthenticatedAccount",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "apps.common.api_errors.api_exception_handler",
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
}
