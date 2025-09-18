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

from .admin_views import (
    pending_approvals,
    approve_brand, reject_brand,
    approve_category, reject_category,
    approve_product, reject_product,
    approve_variant, reject_variant,
    bulk_approve
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
    
    # Admin approval endpoints
    path('admin/pending-approvals/', pending_approvals, name='pending-approvals'),
    path('admin/brands/<int:brand_id>/approve/', approve_brand, name='approve-brand'),
    path('admin/brands/<int:brand_id>/reject/', reject_brand, name='reject-brand'),
    path('admin/categories/<int:category_id>/approve/', approve_category, name='approve-category'),
    path('admin/categories/<int:category_id>/reject/', reject_category, name='reject-category'),
    path('admin/products/<int:product_id>/approve/', approve_product, name='approve-product'),
    path('admin/products/<int:product_id>/reject/', reject_product, name='reject-product'),
    path('admin/variants/<int:variant_id>/approve/', approve_variant, name='approve-variant'),
    path('admin/variants/<int:variant_id>/reject/', reject_variant, name='reject-variant'),
    path('admin/bulk-approve/', bulk_approve, name='bulk-approve'),
]
