from rest_framework.response import Response
from rest_framework.views import APIView

from apps.anna.serializers import (
    AnnaConversationCreateSerializer,
    AnnaConversationMessageSerializer,
    AnnaConversationSerializer,
    ReviewRunSerializer,
    ReviewWriteSerializer,
)
from apps.anna.services import (
    archive_conversation,
    continue_conversation,
    create_conversation,
    continue_in_composer,
    list_conversations,
    owned_conversation,
    review_owned_draft,
)
from apps.common.pagination import paginated_response
from apps.users.permissions import IsAuthor


class ReviewView(APIView):
    permission_classes = [IsAuthor]

    def get(self, request):
        post_id = request.query_params.get("post_id")
        if not post_id or not post_id.isdigit():
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "post_id is required.", "details": {}}}, status=400)
        from apps.anna.models import ReviewRun

        run = ReviewRun.objects.filter(author=request.user, post_id=post_id).select_related("post", "conversation").order_by("-created_at").first()
        if run is None:
            return Response({"run": None})
        return Response({"run": ReviewRunSerializer(run, context={"request": request}).data})

    def post(self, request):
        serializer = ReviewWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = review_owned_draft(actor=request.user, post_id=serializer.validated_data["post_id"])
        return Response(ReviewRunSerializer(run, context={"request": request}).data, status=201)


class AnnaConversationListView(APIView):
    permission_classes = [IsAuthor]

    def get(self, request):
        include_archived = request.query_params.get("include_archived") == "true"
        return paginated_response(self, request, list_conversations(actor=request.user, include_archived=include_archived), AnnaConversationSerializer)

    def post(self, request):
        serializer = AnnaConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = create_conversation(
            actor=request.user,
            post_id=serializer.validated_data.get("post_id"),
            title=serializer.validated_data.get("title", ""),
        )
        return Response(AnnaConversationSerializer(conversation, context={"request": request}).data, status=201)


class AnnaConversationDetailView(APIView):
    permission_classes = [IsAuthor]

    def get(self, request, conversation_id):
        return Response(AnnaConversationSerializer(owned_conversation(actor=request.user, conversation_id=conversation_id), context={"request": request}).data)


class AnnaConversationMessageView(APIView):
    permission_classes = [IsAuthor]

    def post(self, request, conversation_id):
        serializer = AnnaConversationMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = continue_conversation(actor=request.user, conversation_id=conversation_id, content=serializer.validated_data["content"])
        return Response(
            {
                "conversation": AnnaConversationSerializer(owned_conversation(actor=request.user, conversation_id=conversation_id), context={"request": request}).data,
                "run": ReviewRunSerializer(run, context={"request": request}).data,
            }
        )


class AnnaConversationArchiveView(APIView):
    permission_classes = [IsAuthor]

    def post(self, request, conversation_id):
        return Response(AnnaConversationSerializer(archive_conversation(actor=request.user, conversation_id=conversation_id), context={"request": request}).data)


class AnnaMessageHandoffView(APIView):
    permission_classes = [IsAuthor]

    def post(self, request, message_id):
        conversation = continue_in_composer(actor=request.user, message_id=message_id)
        from apps.composer.serializers import ComposerConversationSerializer

        return Response(ComposerConversationSerializer(conversation, context={"request": request}).data, status=201)
