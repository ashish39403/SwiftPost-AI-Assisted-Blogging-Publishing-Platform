from rest_framework.response import Response
from rest_framework.views import APIView

from apps.composer.serializers import (
    ComposerConversationCreateSerializer,
    ComposerConversationSerializer,
    ComposeRunSerializer,
    ComposeWriteSerializer,
    ConversationMessageWriteSerializer,
    ConversationRenameSerializer,
)
from apps.composer.services import (
    archive_conversation,
    compose_from_title,
    continue_conversation,
    create_conversation,
    list_conversations,
    owned_conversation,
    owned_run,
    rename_conversation,
)
from apps.common.pagination import paginated_response
from apps.users.permissions import IsAuthor


class ComposeView(APIView):
    permission_classes = [IsAuthor]

    def post(self, request):
        serializer = ComposeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = compose_from_title(actor=request.user, title=serializer.validated_data["title"])
        return Response(ComposeRunSerializer(run, context={"request": request}).data, status=201)


class ComposeDetailView(APIView):
    permission_classes = [IsAuthor]

    def get(self, request, run_id):
        run = owned_run(request.user, run_id)
        return Response(ComposeRunSerializer(run, context={"request": request}).data)


class ComposerConversationListView(APIView):
    permission_classes = [IsAuthor]

    def get(self, request):
        include_archived = request.query_params.get("include_archived") == "true"
        return paginated_response(self, request, list_conversations(actor=request.user, include_archived=include_archived), ComposerConversationSerializer)

    def post(self, request):
        serializer = ComposerConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data.get("message") or serializer.validated_data.get("title", "")
        conversation = create_conversation(actor=request.user, title=serializer.validated_data.get("title", message))
        run = compose_from_title(actor=request.user, title=message, conversation=conversation)
        return Response(
            {
                "conversation": ComposerConversationSerializer(owned_conversation(actor=request.user, conversation_id=conversation.id), context={"request": request}).data,
                "run": ComposeRunSerializer(run, context={"request": request}).data,
            },
            status=201,
        )


class ComposerConversationDetailView(APIView):
    permission_classes = [IsAuthor]

    def get(self, request, conversation_id):
        return Response(ComposerConversationSerializer(owned_conversation(actor=request.user, conversation_id=conversation_id), context={"request": request}).data)

    def patch(self, request, conversation_id):
        serializer = ConversationRenameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(ComposerConversationSerializer(rename_conversation(actor=request.user, conversation_id=conversation_id, title=serializer.validated_data["title"]), context={"request": request}).data)


class ComposerConversationMessageView(APIView):
    permission_classes = [IsAuthor]

    def post(self, request, conversation_id):
        serializer = ConversationMessageWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = continue_conversation(actor=request.user, conversation_id=conversation_id, content=serializer.validated_data["content"])
        return Response(ComposerConversationSerializer(conversation, context={"request": request}).data)


class ComposerConversationArchiveView(APIView):
    permission_classes = [IsAuthor]

    def post(self, request, conversation_id):
        return Response(ComposerConversationSerializer(archive_conversation(actor=request.user, conversation_id=conversation_id), context={"request": request}).data)
