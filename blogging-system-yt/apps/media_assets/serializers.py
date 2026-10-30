from rest_framework import serializers

from apps.media_assets.models import ImageSuggestion, MediaAsset
from apps.media_assets.storage import get_storage


class MediaAssetSerializer(serializers.ModelSerializer):
    post_id = serializers.IntegerField(read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = (
            "id",
            "post_id",
            "content_type",
            "byte_size",
            "width",
            "height",
            "original_filename",
            "url",
        )
        read_only_fields = fields

    def get_url(self, asset):
        url = get_storage().url(asset.storage_key)
        if url.startswith("/"):
            return url
        return url


class ImageSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageSuggestion
        fields = ("id", "image_url", "page_url", "description", "selected", "retrieved_at")
        read_only_fields = fields


class ImageSearchWriteSerializer(serializers.Serializer):
    post_id = serializers.IntegerField()
    query = serializers.CharField(required=False, allow_blank=True, max_length=200)


class ImageSuggestionSaveSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), min_length=1, max_length=12)
