from django.urls import path

from apps.blogs.views import (
    ArchivePostView,
    DraftDetailView,
    DraftListCreateView,
    PublishPostView,
    PublishedPostDetailView,
    PublishedPostListView,
    SubmitPostView,
    UnpublishPostView,
)

urlpatterns = [
    path("blogs/", PublishedPostListView.as_view(), name="published-post-list"),
    path("blogs/<int:post_id>/submit/", SubmitPostView.as_view(), name="post-submit"),
    path("blogs/<int:post_id>/publish/", PublishPostView.as_view(), name="post-publish"),
    path("blogs/<int:post_id>/unpublish/", UnpublishPostView.as_view(), name="post-unpublish"),
    path("blogs/<int:post_id>/archive/", ArchivePostView.as_view(), name="post-archive"),
    path("blogs/<str:post_id>/", PublishedPostDetailView.as_view(), name="published-post-detail"),
    path("drafts/", DraftListCreateView.as_view(), name="draft-list"),
    path("drafts/<int:post_id>/", DraftDetailView.as_view(), name="draft-detail"),
]
