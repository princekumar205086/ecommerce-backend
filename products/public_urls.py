# products/public_urls.py
from django.urls import path
from .public_views import (
    PublicProductCategoryListView,
    PublicBrandListView,
    PublicProductListView,
    PublicProductDetailView,
    PublicProductReviewListView,
    PublicProductSearchView,
    PublicFeaturedProductsView,
    PublicProductsByCategory,
    PublicProductsByBrand,
    PublicProductsByType,
)

app_name = 'products_public'

urlpatterns = [
    # Public product endpoints
    path('categories/', PublicProductCategoryListView.as_view(), name='public-category-list'),
    path('brands/', PublicBrandListView.as_view(), name='public-brand-list'),
    path('products/', PublicProductListView.as_view(), name='public-product-list'),
    path('products/<int:pk>/', PublicProductDetailView.as_view(), name='public-product-detail'),
    path('products/<int:product_id>/reviews/', PublicProductReviewListView.as_view(), name='public-product-reviews'),
    
    # Advanced search and filtering
    path('search/', PublicProductSearchView.as_view(), name='public-product-search'),
    path('featured/', PublicFeaturedProductsView.as_view(), name='public-featured-products'),
    
    # Products by category, brand, and type
    path('categories/<int:category_id>/products/', PublicProductsByCategory.as_view(), name='public-products-by-category'),
    path('brands/<int:brand_id>/products/', PublicProductsByBrand.as_view(), name='public-products-by-brand'),
    path('types/<str:product_type>/products/', PublicProductsByType.as_view(), name='public-products-by-type'),
]