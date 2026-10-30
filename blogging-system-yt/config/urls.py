from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from apps.common.health import api_not_found, health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health, name="api-health"),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.categories.urls")),
    path("api/v1/", include("apps.comments.urls")),
    path("api/v1/", include("apps.blogs.urls")),
    path("api/v1/", include("apps.media_assets.urls")),
    path("api/v1/", include("apps.composer.urls")),
    path("api/v1/", include("apps.anna.urls")),
    re_path(r"^api(?:/.*)?$", api_not_found),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
