from rest_framework import serializers

from apps.blogs.serializers import PostSerializer
from apps.composer.models import ComposeRun, Conversation, JobStatus, Message
from apps.media_assets.serializers import ImageSuggestionSerializer


class ComposeWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)


class ComposeRunSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    suggested_images = serializers.SerializerMethodField()

    class Meta:
        model = ComposeRun
        fields = (
            "id",
            "status",
            "title_input",
            "generated_title",
            "generated_excerpt",
            "model_name",
            "error_message",
            "post",
            "suggested_images",
            "created_at",
            "finished_at",
        )
        read_only_fields = fields

    def get_suggested_images(self, run):
        if not run.post_id:
            return []
        return ImageSuggestionSerializer(run.post.image_suggestions.all()[:8], many=True).data


class ComposerMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "role", "content", "sequence", "created_at")
        read_only_fields = fields


class ComposerConversationSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    messages = ComposerMessageSerializer(many=True, read_only=True)
    suggested_images = serializers.SerializerMethodField()
    is_generating = serializers.SerializerMethodField()
    last_error = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "title",
            "status",
            "post",
            "messages",
            "suggested_images",
            "is_generating",
            "last_error",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_suggested_images(self, conversation):
        if not conversation.post_id:
            return []
        return ImageSuggestionSerializer(conversation.post.image_suggestions.all()[:12], many=True).data

    def get_is_generating(self, conversation):
        return conversation.compose_runs.filter(status__in=("queued", "running")).exists()

    def get_last_error(self, conversation):
        run = conversation.compose_runs.order_by("-created_at").first()
        if run and run.status == JobStatus.FAILED:
            return run.error_message
        return ""


class ComposerConversationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    message = serializers.CharField(max_length=8000, required=False, allow_blank=False)

    def validate(self, attrs):
        if not attrs.get("title") and not attrs.get("message"):
            raise serializers.ValidationError({"message": "Provide a title or first message."})
        return attrs


class ConversationMessageWriteSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=8000)


class ConversationRenameSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
