from django.urls import path

from .views import (
    ProductCategoryListCreateView,
    ProductCategoryDetailView,
    ProductListCreateView,
    ProductDetailView,
    ProductReviewListCreateView,
    ProductReviewDetailView,
    BrandListCreateView,
    BrandDetailView,
    ProductVariantListCreateView,
    ProductVariantDetailView,
    SupplierProductPriceListCreateView,
    SupplierProductPriceDetailView,
    ProductAttributeListCreateView,
    ProductAttributeDetailView,
    ProductAttributeValueListCreateView,
    ProductAttributeValueDetailView,
    ProductImageListCreateView,
    ProductImageDetailView,
)

app_name = 'products'

urlpatterns = [
    path('categories/', ProductCategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', ProductCategoryDetailView.as_view(), name='category-detail'),
    path('brands/', BrandListCreateView.as_view(), name='brand-list-create'),
    path('brands/<int:pk>/', BrandDetailView.as_view(), name='brand-detail'),
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('variants/', ProductVariantListCreateView.as_view(), name='variant-list-create'),
    path('variants/<int:pk>/', ProductVariantDetailView.as_view(), name='variant-detail'),
    path('supplier-prices/', SupplierProductPriceListCreateView.as_view(), name='supplier-price-list-create'),
    path('supplier-prices/<int:pk>/', SupplierProductPriceDetailView.as_view(), name='supplier-price-detail'),
    path('reviews/', ProductReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<int:pk>/', ProductReviewDetailView.as_view(), name='review-detail'),
    path('attributes/', ProductAttributeListCreateView.as_view(), name='attribute-list-create'),
    path('attributes/<int:pk>/', ProductAttributeDetailView.as_view(), name='attribute-detail'),
    path('attribute-values/', ProductAttributeValueListCreateView.as_view(), name='attribute-value-list-create'),
    path('attribute-values/<int:pk>/', ProductAttributeValueDetailView.as_view(), name='attribute-value-detail'),
    path('images/', ProductImageListCreateView.as_view(), name='image-list-create'),
    path('images/<int:pk>/', ProductImageDetailView.as_view(), name='image-detail'),
]
