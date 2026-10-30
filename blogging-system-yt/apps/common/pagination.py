from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


def paginated_response(view, request, queryset, serializer_class):
    paginator = DefaultPagination()
    page = paginator.paginate_queryset(queryset, request, view=view)
    return paginator.get_paginated_response(
        serializer_class(page, many=True, context={"request": request}).data
    )
