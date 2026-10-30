from rest_framework import serializers

from apps.categories.models import Category

_FORBIDDEN = {"slug", "is_active"}


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "is_active", "created_at", "updated_at")
        read_only_fields = fields


class CategoryWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80, required=False)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        forbidden = sorted(_FORBIDDEN & {str(key) for key in self.initial_data})
        if forbidden:
            raise serializers.ValidationError(
                {field: "This field cannot be set." for field in forbidden}
            )
        if self.instance is None and "name" not in attrs:
            raise serializers.ValidationError({"name": "Name is required."})
        if "name" not in attrs:
            return attrs
        name = attrs["name"].strip()
        if not name:
            raise serializers.ValidationError({"name": "Name is required."})
        taken = Category.objects.filter(name__iexact=name)
        if self.instance is not None:
            taken = taken.exclude(pk=self.instance.pk)
        if taken.exists():
            raise serializers.ValidationError({"name": "A category with this name already exists."})
        attrs["name"] = name
        return attrs
