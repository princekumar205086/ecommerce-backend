# views.py
from django.db import IntegrityError
from rest_framework import generics, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError

from .models import (
    ProductCategory, ProductSubCategory, Product, ProductReview,
    Brand, ProductVariant
)
from .serializers import (
    ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer,
    ProductReviewSerializer, BrandSerializer, ProductVariantSerializer
)
from ecommerce.permissions import IsSupplierOrAdmin


class ProductCategoryListCreateView(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [IsSupplierOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']

    def perform_create(self, serializer):
        serializer.save(status='pending', is_publish=False)


class ProductSubCategoryListCreateView(generics.ListCreateAPIView):
    queryset = ProductSubCategory.objects.all()
    serializer_class = ProductSubCategorySerializer
    permission_classes = [IsSupplierOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']

    def perform_create(self, serializer):
        serializer.save(status='pending', is_publish=False)


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsSupplierOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'subcategory', 'brand', 'type', 'status', 'is_publish']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

    def perform_create(self, serializer):
        try:
            serializer.save(status='pending', is_publish=False)
        except IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                raise ValidationError({
                    "detail": "A product with this name already exists. Please use a unique name."
                })
            raise ValidationError({"detail": "An error occurred while creating the product."})


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsSupplierOrAdmin]


# views.py
class ProductReviewListCreateView(generics.ListCreateAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'rating']

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError as e:
            raise ValidationError({
                "detail": "You have already reviewed this product or there was a validation error."
            })


class BrandListCreateView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsSupplierOrAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProductVariantListCreateView(generics.ListCreateAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

    def handle_exception(self, exc):
        if isinstance(exc, IntegrityError) and 'unique_product_variant' in str(exc):
            exc = ValidationError({
                'detail': 'A variant with these specifications already exists for this product.'
            })
        return super().handle_exception(exc)
