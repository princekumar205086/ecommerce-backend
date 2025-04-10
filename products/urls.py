from django.urls import path
from .views import ProductCategoryListView, ProductListCreateView, ProductDetailView

urlpatterns = [
    path('categories/', ProductCategoryListView.as_view(), name='product-category-list'),
    path('', ProductListCreateView.as_view(), name='product-list-create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]
