from rest_framework import serializers

from apps.anna.models import Conversation, Message, ReviewRun
from apps.blogs.serializers import PostSerializer


class ReviewWriteSerializer(serializers.Serializer):
    post_id = serializers.IntegerField()


class ReviewRunSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    conversation_id = serializers.UUIDField(read_only=True)
    review_message_id = serializers.SerializerMethodField()

    class Meta:
        model = ReviewRun
        fields = (
            "id",
            "status",
            "notes",
            "model_name",
            "error_message",
            "post",
            "conversation_id",
            "review_message_id",
            "created_at",
            "finished_at",
        )
        read_only_fields = fields

    def get_review_message_id(self, run):
        if not run.conversation_id:
            return None
        message = run.conversation.messages.filter(role="assistant").order_by("-sequence").first()
        return str(message.id) if message else None


class AnnaMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "role", "content", "sequence", "created_at")
        read_only_fields = fields


class AnnaConversationSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    messages = AnnaMessageSerializer(many=True, read_only=True)
    is_generating = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "title", "status", "post", "messages", "is_generating", "created_at", "updated_at")
        read_only_fields = fields

    def get_is_generating(self, conversation):
        return conversation.review_runs.filter(status__in=("queued", "running")).exists()


class AnnaConversationCreateSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(required=False)
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)


class AnnaConversationMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=8000)
