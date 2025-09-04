from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from ecommerce.permissions import IsSupplierOrAdmin, IsAdminOrReadOnly
from .models import (
    ProductCategory, Product, ProductReview,
    Brand, ProductVariant, SupplierProductPrice,
    MedicineDetails, EquipmentDetails, PathologyDetails,
    ProductAttribute, ProductAttributeValue, ProductImage
)
from .serializers import (
    ProductCategorySerializer, BaseProductSerializer, ProductReviewSerializer,
    BrandSerializer, ProductVariantSerializer, SupplierProductPriceSerializer,
    MedicineBaseProductSerializer, EquipmentBaseProductSerializer, PathologyBaseProductSerializer,
    ProductAttributeSerializer, ProductAttributeValueSerializer, ProductImageSerializer
)


def get_product_serializer_class(product_type):
    return {
        'medicine': MedicineBaseProductSerializer,
        'equipment': EquipmentBaseProductSerializer,
        'pathology': PathologyBaseProductSerializer,
    }.get(product_type, BaseProductSerializer)


class ProductCategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        Anonymous users see only published categories, admins see all.
        """
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'admin':
            return ProductCategory.objects.all()
        else:
            # For anonymous users and non-admin users, show only published categories
            return ProductCategory.objects.filter(status='published', is_publish=True)

    def perform_create(self, serializer):
        serializer.save(status='pending', is_publish=False)


class ProductCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        Anonymous users see only published categories, admins see all.
        """
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'admin':
            return ProductCategory.objects.all()
        else:
            # For anonymous users and non-admin users, show only published categories
            return ProductCategory.objects.filter(status='published', is_publish=True)


class BrandDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


class BrandListCreateView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProductListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'status', 'is_publish', 'product_type']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        Anonymous users see only published products, admins see all.
        """
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'admin':
            return Product.objects.prefetch_related('variants', 'images', 'supplier_prices').all()
        else:
            # For anonymous users and non-admin users, show only published products
            return Product.objects.filter(
                status='published',
                is_publish=True
            ).prefetch_related('variants', 'images', 'supplier_prices').all()

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
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        Anonymous users see only published products, admins see all.
        """
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'admin':
            return Product.objects.prefetch_related('variants', 'images', 'supplier_prices').all()
        else:
            # For anonymous users and non-admin users, show only published products
            return Product.objects.filter(
                status='published',
                is_publish=True
            ).prefetch_related('variants', 'images', 'supplier_prices').all()

    def get_serializer_class(self):
        # Prevent errors during schema generation
        if getattr(self, 'swagger_fake_view', False):
            return BaseProductSerializer  # Use your default serializer here
        instance = self.get_object()
        return get_product_serializer_class(instance.product_type)

    def perform_update(self, serializer):
        instance = serializer.save()
        instance._changed_by = self.request.user  # Used in audit logging


# Product Attribute Views
class ProductAttributeListCreateView(generics.ListCreateAPIView):
    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProductAttributeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductAttributeValueListCreateView(generics.ListCreateAPIView):
    queryset = ProductAttributeValue.objects.select_related('attribute').all()
    serializer_class = ProductAttributeValueSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['attribute']
    search_fields = ['value']


class ProductAttributeValueDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductAttributeValue.objects.select_related('attribute').all()
    serializer_class = ProductAttributeValueSerializer
    permission_classes = [IsAdminOrReadOnly]


# Product Image Views
class ProductImageListCreateView(generics.ListCreateAPIView):
    queryset = ProductImage.objects.select_related('product').all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'variant']


class ProductImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductImage.objects.select_related('product').all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductVariantListCreateView(generics.ListCreateAPIView):
    queryset = ProductVariant.objects.select_related('product').all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
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
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        serializer.save(supplier=self.request.user)


class ProductReviewListCreateView(generics.ListCreateAPIView):
    queryset = ProductReview.objects.select_related('product', 'user').all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'rating']

    def get_permissions(self):
        """
        Override permissions based on request method.
        GET requests are allowed for everyone, POST requires authentication.
        """
        if self.request.method == 'GET':
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError({
                "detail": "You have already reviewed this product or another integrity error occurred."
            })


class ProductVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductVariant.objects.select_related('product').all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminOrReadOnly]


class SupplierProductPriceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SupplierProductPrice.objects.select_related('product', 'supplier').all()
    serializer_class = SupplierProductPriceSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOrAdmin]


class ProductReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductReview.objects.select_related('product', 'user').all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        """
        Override permissions based on request method.
        GET requests are allowed for everyone, POST/PUT/PATCH/DELETE require authentication.
        """
        if self.request.method == 'GET':
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()
