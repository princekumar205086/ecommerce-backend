from django.urls import path
from .views import *

urlpatterns = [
    path('categories/', ProductCategoryListCreateView.as_view(), name='product-categories'),
    path('subcategories/', ProductSubCategoryListCreateView.as_view(), name='product-subcategories'),
    path('products/', ProductListCreateView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('reviews/', ProductReviewListCreateView.as_view(), name='product-reviews'),
    path('brands/', BrandListCreateView.as_view(), name='brands'),
    path('variants/', ProductVariantListCreateView.as_view(), name='product-variants'),
]
