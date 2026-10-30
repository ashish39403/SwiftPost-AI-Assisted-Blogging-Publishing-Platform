from rest_framework import serializers

from apps.comments.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id", "post_id", "author", "body", "status", "created_at")
        read_only_fields = fields

    def get_author(self, comment):
        return {"id": comment.author_id, "username": comment.author.username}


class CommentWriteSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=2000)
