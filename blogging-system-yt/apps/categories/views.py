from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.categories.models import Category
from apps.categories.serializers import CategorySerializer, CategoryWriteSerializer
from apps.categories.services import create_category, deactivate_category, update_category
from apps.common.pagination import paginated_response
from apps.users.permissions import IsAdmin


class CategoryListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdmin()]

    def get(self, request):
        queryset = Category.objects.all()
        include_inactive = request.query_params.get("include_inactive") == "true"
        if not (
            include_inactive
            and request.user.is_authenticated
            and request.user.role == Role.ADMIN
        ):
            queryset = queryset.filter(is_active=True)
        return paginated_response(self, request, queryset.order_by("name"), CategorySerializer)

    def post(self, request):
        serializer = CategoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = create_category(
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description", ""),
        )
        return Response(CategorySerializer(category).data, status=201)


class CategoryDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdmin()]

    def get(self, request, category_id):
        category = _active_category(category_id)
        return Response(CategorySerializer(category).data)

    def patch(self, request, category_id):
        category = _any_category(category_id)
        serializer = CategoryWriteSerializer(data=request.data, instance=category)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        category = update_category(
            category,
            name=data.get("name"),
            description=data.get("description") if "description" in data else None,
        )
        return Response(CategorySerializer(category).data)

    def delete(self, request, category_id):
        category = _any_category(category_id)
        category = deactivate_category(category)
        return Response(CategorySerializer(category).data)


def _active_category(category_id):
    try:
        return Category.objects.get(pk=category_id, is_active=True)
    except Category.DoesNotExist:
        raise _missing() from None


def _any_category(category_id):
    try:
        return Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        raise _missing() from None


def _missing():
    exc = NotFound("The requested category could not be found.")
    exc.api_code = "CATEGORY_NOT_FOUND"
    return exc
