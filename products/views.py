from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, permissions
from rest_framework.exceptions import ValidationError

from ecommerce.permissions import IsSupplierOrAdmin
from .models import (
    ProductCategory, Product, ProductReview,
    Brand, ProductVariant, SupplierProductPrice
)
from .serializers import (
    ProductCategorySerializer, BaseProductSerializer, ProductReviewSerializer,
    BrandSerializer, ProductVariantSerializer, SupplierProductPriceSerializer,
    MedicineBaseProductSerializer, EquipmentBaseProductSerializer, PathologyBaseProductSerializer
)

def get_product_serializer_class(product_type):
    return {
        'medicine': MedicineBaseProductSerializer,
        'doctor_equipment': EquipmentBaseProductSerializer,
        'pathology': PathologyBaseProductSerializer,
    }.get(product_type, BaseProductSerializer)




class ProductCategoryListCreateView(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [IsSupplierOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']

    def perform_create(self, serializer):
        serializer.save(status='pending', is_publish=False)


class BrandListCreateView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsSupplierOrAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.prefetch_related('variants', 'images', 'supplier_prices').all()
    permission_classes = [IsSupplierOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'status', 'is_publish', 'product_type']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

    def get_serializer_class(self):
        product_type = self.request.data.get('product_type') or self.request.query_params.get('product_type')
        return get_product_serializer_class(product_type)

    def perform_create(self, serializer):
        try:
            product = serializer.save(status='pending', is_publish=False)
            product._changed_by = self.request.user  # Used in audit logging
        except IntegrityError as e:
            raise ValidationError({
                "detail": "A similar product already exists. Please use a unique combination."
            }) if 'unique' in str(e).lower() else ValidationError({
                "detail": "An error occurred while creating the product."
            })

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.prefetch_related('variants', 'images', 'supplier_prices').all()
    permission_classes = [IsSupplierOrAdmin]

    def get_serializer_class(self):
        instance = self.get_object()
        return get_product_serializer_class(instance.product_type)

    def perform_update(self, serializer):
        instance = serializer.save()
        instance._changed_by = self.request.user  # Used in audit logging

class ProductVariantListCreateView(generics.ListCreateAPIView):
    queryset = ProductVariant.objects.select_related('product').all()
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError as e:
            raise ValidationError({
                'detail': 'A variant with these specifications already exists for this product.'
            }) if 'unique' in str(e).lower() else e

class SupplierProductPriceListCreateView(generics.ListCreateAPIView):
    queryset = SupplierProductPrice.objects.select_related('product', 'supplier').all()
    serializer_class = SupplierProductPriceSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOrAdmin]

    def perform_create(self, serializer):
        serializer.save(supplier=self.request.user)


class ProductReviewListCreateView(generics.ListCreateAPIView):
    queryset = ProductReview.objects.select_related('product', 'user').all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'rating']

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError({
                "detail": "You have already reviewed this product or another integrity error occurred."
            })
