from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAuthenticatedAccount
from apps.blogs.queries import (
    get_private_post,
    get_published_post,
    published_posts,
    visible_private_posts,
)
from apps.blogs.serializers import DraftWriteSerializer, PostSerializer
from apps.blogs.services import create_draft, delete_draft, update_draft
from apps.common.pagination import paginated_response
from apps.publishing.models import PublishingAction
from apps.publishing.services import transition
from apps.users.permissions import IsAuthor


def post_payload(request, post):
    return PostSerializer(post, context={"request": request}).data


class PublishedPostListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return paginated_response(
            self,
            request,
            published_posts(request.query_params),
            PostSerializer,
        )


class PublishedPostDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, post_id):
        return Response(post_payload(request, get_published_post(post_id)))


class DraftListCreateView(APIView):
    permission_classes = [IsAuthenticatedAccount]

    def get(self, request):
        return paginated_response(
            self,
            request,
            visible_private_posts(request.user, request.query_params),
            PostSerializer,
        )

    def post(self, request):
        serializer = DraftWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        post = create_draft(
            author=request.user,
            title=data.get("title", ""),
            excerpt=data.get("excerpt", ""),
            body=data.get("body", ""),
            category=data.get("category"),
        )
        return Response(post_payload(request, post), status=201)


class DraftDetailView(APIView):
    permission_classes = [IsAuthenticatedAccount]

    def get(self, request, post_id):
        return Response(post_payload(request, get_private_post(request.user, post_id)))

    def patch(self, request, post_id):
        post = get_private_post(request.user, post_id)
        serializer = DraftWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = update_draft(post, actor=request.user, changes=serializer.validated_data)
        return Response(post_payload(request, post))

    def delete(self, request, post_id):
        post = get_private_post(request.user, post_id)
        delete_draft(post, actor=request.user)
        return Response({"status": "ok"})


class SubmitPostView(APIView):
    permission_classes = [IsAuthor]

    def post(self, request, post_id):
        return _act(request, post_id, PublishingAction.SUBMIT)


class PublishPostView(APIView):
    permission_classes = [IsAuthor]

    def post(self, request, post_id):
        return _act(request, post_id, PublishingAction.PUBLISH)


class UnpublishPostView(APIView):
    permission_classes = [IsAuthor]

    def post(self, request, post_id):
        return _act(request, post_id, PublishingAction.UNPUBLISH)


class ArchivePostView(APIView):
    permission_classes = [IsAuthenticatedAccount]

    def post(self, request, post_id):
        return _act(request, post_id, PublishingAction.ARCHIVE)


def _act(request, post_id, action):
    post = get_private_post(request.user, post_id)
    reason = request.data.get("reason", "") if isinstance(request.data, dict) else ""
    if not isinstance(reason, str):
        reason = ""
    post = transition(post=post, actor=request.user, action=action, reason=reason)
    return Response(post_payload(request, post))
