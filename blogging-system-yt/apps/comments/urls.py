from django.urls import path

from apps.comments.views import (
    CommentApproveView,
    CommentDetailView,
    CommentListCreateView,
    CommentRejectView,
    LikeView,
)

urlpatterns = [
    path("blogs/<int:post_id>/comments/", CommentListCreateView.as_view(), name="post-comments"),
    path("blogs/<int:post_id>/likes/", LikeView.as_view(), name="post-likes"),
    path("comments/<int:comment_id>/", CommentDetailView.as_view(), name="comment-detail"),
    path("comments/<int:comment_id>/approve/", CommentApproveView.as_view(), name="comment-approve"),
    path("comments/<int:comment_id>/reject/", CommentRejectView.as_view(), name="comment-reject"),
]
