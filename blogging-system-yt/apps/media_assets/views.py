from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAuthenticatedAccount
from apps.blogs.queries import get_private_post
from apps.media_assets.image_search import (
    attach_suggested_image,
    listed_suggestions,
    save_suggested_images,
    search_images_for_draft,
)
from apps.media_assets.models import MediaAsset
from apps.media_assets.serializers import (
    ImageSearchWriteSerializer,
    ImageSuggestionSaveSerializer,
    ImageSuggestionSerializer,
    MediaAssetSerializer,
)
from apps.media_assets.services import delete_featured_image, upload_featured_image, visible_asset


class MediaUploadView(APIView):
    permission_classes = [IsAuthenticatedAccount]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        post = get_private_post(request.user, _post_id(request.data.get("post_id")))
        asset = upload_featured_image(
            actor=request.user,
            post=post,
            upload=request.FILES.get("file"),
        )
        return Response(MediaAssetSerializer(asset, context={"request": request}).data, status=201)


class MediaDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticatedAccount()]
        return [AllowAny()]

    def get(self, request, asset_id):
        asset = visible_asset(request.user, asset_id)
        return Response(MediaAssetSerializer(asset, context={"request": request}).data)

    def delete(self, request, asset_id):
        try:
            asset = MediaAsset.objects.select_related("post").get(pk=asset_id)
        except MediaAsset.DoesNotExist:
            asset = visible_asset(request.user, asset_id)
        delete_featured_image(actor=request.user, asset=asset)
        return Response({"status": "ok"})


class ImageSearchView(APIView):
    permission_classes = [IsAuthenticatedAccount]

    def get(self, request):
        post_id = _post_id(request.query_params.get("post_id"))
        suggestions = listed_suggestions(actor=request.user, post_id=post_id)
        return Response(ImageSuggestionSerializer(suggestions, many=True).data)

    def post(self, request):
        serializer = ImageSearchWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        suggestions = search_images_for_draft(
            actor=request.user,
            post_id=serializer.validated_data["post_id"],
            query=serializer.validated_data.get("query") or "",
        )
        return Response(ImageSuggestionSerializer(suggestions, many=True).data)


class ImageSuggestionAttachView(APIView):
    permission_classes = [IsAuthenticatedAccount]

    def post(self, request, suggestion_id):
        asset = attach_suggested_image(actor=request.user, suggestion_id=suggestion_id)
        return Response(MediaAssetSerializer(asset, context={"request": request}).data, status=201)


class ImageSuggestionSaveView(APIView):
    permission_classes = [IsAuthenticatedAccount]

    def post(self, request):
        serializer = ImageSuggestionSaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = save_suggested_images(actor=request.user, suggestion_ids=serializer.validated_data["ids"])
        featured = result["featured"]
        return Response(
            {
                "featured": MediaAssetSerializer(featured, context={"request": request}).data if featured else None,
                "images": MediaAssetSerializer(result["images"], many=True, context={"request": request}).data,
                "selected": ImageSuggestionSerializer(result["selected"], many=True).data,
            }
        )


def _post_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError({"post_id": "A draft is required."}) from None
