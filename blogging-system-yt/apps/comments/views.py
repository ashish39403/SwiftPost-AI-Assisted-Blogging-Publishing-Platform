from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAuthenticatedAccount
from apps.comments.models import CommentStatus
from apps.comments.serializers import CommentSerializer, CommentWriteSerializer
from apps.comments.services import (
    create_comment,
    delete_comment,
    get_comment,
    like_state,
    moderate_comment,
    public_comments,
    require_published,
    toggle_like,
)
from apps.common.pagination import paginated_response


class CommentListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticatedAccount()]
        return [AllowAny()]

    def get(self, request, post_id):
        post = require_published(post_id)
        return paginated_response(self, request, public_comments(post), CommentSerializer)

    def post(self, request, post_id):
        post = require_published(post_id)
        serializer = CommentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = create_comment(actor=request.user, post=post, body=serializer.validated_data["body"])
        return Response(CommentSerializer(comment).data, status=201)


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticatedAccount]

    def delete(self, request, comment_id):
        delete_comment(actor=request.user, comment=get_comment(comment_id))
        return Response({"status": "ok"})


class CommentApproveView(APIView):
    permission_classes = [IsAuthenticatedAccount]

    def post(self, request, comment_id):
        comment = moderate_comment(
            actor=request.user,
            comment=get_comment(comment_id),
            status=CommentStatus.APPROVED,
        )
        return Response(CommentSerializer(comment).data)


class CommentRejectView(APIView):
    permission_classes = [IsAuthenticatedAccount]

    def post(self, request, comment_id):
        comment = moderate_comment(
            actor=request.user,
            comment=get_comment(comment_id),
            status=CommentStatus.REJECTED,
        )
        return Response(CommentSerializer(comment).data)


class LikeView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticatedAccount()]
        return [AllowAny()]

    def get(self, request, post_id):
        post = require_published(post_id)
        return Response(like_state(user=request.user, post=post))

    def post(self, request, post_id):
        post = require_published(post_id)
        return Response(toggle_like(actor=request.user, post=post))
