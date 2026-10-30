from django.apps import AppConfig


class MediaAssetsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media_assets"
    label = "media_assets"

    def ready(self):
        from apps.media_assets import services  # noqa: F401
