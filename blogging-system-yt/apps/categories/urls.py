from django.urls import path

from apps.categories.views import CategoryDetailView, CategoryListCreateView

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-list"),
    path("categories/<int:category_id>/", CategoryDetailView.as_view(), name="category-detail"),
]
