from django.urls import path

from .views import (
    ProductCategoryListCreateView,
    ProductListCreateView,
    ProductDetailView,
    ProductReviewListCreateView,
    BrandListCreateView,
    ProductVariantListCreateView,
    SupplierProductPriceListCreateView,
)

app_name = 'products'

urlpatterns = [
    path('categories/', ProductCategoryListCreateView.as_view(), name='category-list-create'),
    path('brands/', BrandListCreateView.as_view(), name='brand-list-create'),
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('variants/', ProductVariantListCreateView.as_view(), name='variant-list-create'),
    path('supplier-prices/', SupplierProductPriceListCreateView.as_view(), name='supplier-price-list-create'),
    path('reviews/', ProductReviewListCreateView.as_view(), name='review-list-create'),
]
