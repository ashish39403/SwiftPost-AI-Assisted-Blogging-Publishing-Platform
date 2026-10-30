from django.urls import path

from apps.media_assets.views import (
    ImageSearchView,
    ImageSuggestionAttachView,
    ImageSuggestionSaveView,
    MediaDetailView,
    MediaUploadView,
)

urlpatterns = [
    path("media/upload/", MediaUploadView.as_view(), name="media-upload"),
    path("media/search-images/", ImageSearchView.as_view(), name="media-search-images"),
    path("media/suggestions/save/", ImageSuggestionSaveView.as_view(), name="media-save-suggestions"),
    path(
        "media/suggestions/<int:suggestion_id>/attach/",
        ImageSuggestionAttachView.as_view(),
        name="media-attach-suggestion",
    ),
    path("media/<int:asset_id>/", MediaDetailView.as_view(), name="media-detail"),
]
