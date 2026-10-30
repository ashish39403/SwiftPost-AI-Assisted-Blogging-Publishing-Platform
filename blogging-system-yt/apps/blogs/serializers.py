from rest_framework import serializers

from apps.accounts.models import User
from apps.blogs.models import Post
from apps.categories.models import Category
from apps.media_assets.serializers import MediaAssetSerializer

_FORBIDDEN = {"status", "author", "author_id", "slug", "published_at", "featured_image", "storage_key"}


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username")
        read_only_fields = fields


class CategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")
        read_only_fields = fields


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategoryBriefSerializer(read_only=True)
    featured_image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "slug",
            "excerpt",
            "body",
            "status",
            "category",
            "author",
            "featured_image",
            "images",
            "like_count",
            "comment_count",
            "liked",
            "published_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_featured_image(self, post):
        asset = next((image for image in post.images.all() if image.is_featured), None)
        if asset is None:
            return None
        return MediaAssetSerializer(asset, context=self.context).data

    def get_images(self, post):
        return MediaAssetSerializer(post.images.all(), many=True, context=self.context).data

    def get_like_count(self, post):
        return post.likes.count()

    def get_comment_count(self, post):
        from apps.comments.models import CommentStatus

        return post.comments.filter(status=CommentStatus.APPROVED).count()

    def get_liked(self, post):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return post.likes.filter(user=user).exists()


class DraftWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    excerpt = serializers.CharField(max_length=500, required=False, allow_blank=True)
    body = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        forbidden = sorted(_FORBIDDEN & {str(key) for key in self.initial_data})
        if forbidden:
            raise serializers.ValidationError(
                {field: "This field cannot be set." for field in forbidden}
            )
        if "category_id" in attrs:
            category_id = attrs["category_id"]
            if category_id is None:
                attrs["category"] = None
            else:
                try:
                    attrs["category"] = Category.objects.get(pk=category_id, is_active=True)
                except Category.DoesNotExist:
                    raise serializers.ValidationError(
                        {"category_id": "Choose an active category."}
                    ) from None
        return attrs
