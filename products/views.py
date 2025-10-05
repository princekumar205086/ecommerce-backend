from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from ecommerce.permissions import IsSupplierOrAdmin, IsAdminOrReadOnly, IsReviewOwnerOrAdminOrReadOnly, IsCreatedByUserOrAdmin, IsSupplierOrAdminForUpdates
from .models import (
    ProductCategory, Product, ProductReview,
    Brand, ProductVariant, SupplierProductPrice,
    MedicineDetails, EquipmentDetails, PathologyDetails,
    ProductAttribute, ProductAttributeValue, ProductImage
)
from .enterprise_filters import EnterpriseProductFilter
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
    permission_classes = [IsSupplierOrAdmin]  # Allow suppliers to create categories
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']

    def get_permissions(self):
        """
        Override permissions based on request method.
        GET requests are allowed for everyone, POST requires supplier or admin.
        """
        if self.request.method == 'GET':
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [IsSupplierOrAdmin]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        - Anonymous users see only published categories
        - Admins see all categories
        - Suppliers see their own categories (any status) and published categories from others
        """
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'admin':
            return ProductCategory.objects.all()
        elif self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'supplier':
            # Suppliers can see their own categories (any status) and published categories
            from django.db.models import Q
            return ProductCategory.objects.filter(
                Q(created_by=self.request.user) | Q(status__in=['approved', 'published'], is_publish=True)
            )
        else:
            # For anonymous users, show only published categories
            return ProductCategory.objects.filter(status__in=['approved', 'published'], is_publish=True)

    def list(self, request, *args, **kwargs):
        """
        Return all results when 'page' query param is absent.
        Preserve normal DRF pagination when the client explicitly requests a page.
        """
        if 'page' in request.query_params:
            return super().list(request, *args, **kwargs)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'next': None,
            'previous': None,
            'results': serializer.data,
        })

    def perform_create(self, serializer):
        # Set defaults based on user role
        if self.request.user.role == 'admin':
            serializer.save(status='published', is_publish=True, created_by=self.request.user)
        else:  # supplier
            serializer.save(status='pending', is_publish=False, created_by=self.request.user)


class ProductCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductCategorySerializer
    permission_classes = [IsSupplierOrAdminForUpdates]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        - Anonymous users see only published categories
        - Admins see all categories  
        - Suppliers see their own categories (any status) and published categories from others
        """
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'admin':
            return ProductCategory.objects.all()
        elif self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'supplier':
            # Suppliers can see their own categories (any status) and published categories
            from django.db.models import Q
            return ProductCategory.objects.filter(
                Q(created_by=self.request.user) | Q(status__in=['approved', 'published'], is_publish=True)
            )
        else:
            # For anonymous users, show only published categories
            return ProductCategory.objects.filter(status__in=['approved', 'published'], is_publish=True)


class BrandDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BrandSerializer
    permission_classes = [IsSupplierOrAdminForUpdates]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_permissions(self):
        """
        Override permissions based on request method.
        All operations require supplier or admin role.
        Regular users should use public endpoints.
        """
        if self.request.method == 'GET':
            self.permission_classes = [IsSupplierOrAdmin]
        else:
            self.permission_classes = [IsSupplierOrAdminForUpdates]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        Only suppliers and admins can access this endpoint.
        - Admins see all brands  
        - Suppliers see their own brands (any status) and published brands from others
        """
        user = self.request.user
        
        if user.role == 'admin':
            return Brand.objects.all()
        elif user.role == 'supplier':
            # Suppliers can see their own brands (any status) and published brands
            from django.db.models import Q
            return Brand.objects.filter(
                Q(created_by=user) | Q(status__in=['approved', 'published'], is_publish=True)
            )
        else:
            # This should not happen due to permission checks, but fallback to empty queryset
            return Brand.objects.none()


class BrandListCreateView(generics.ListCreateAPIView):
    serializer_class = BrandSerializer
    permission_classes = [IsSupplierOrAdmin]  # Allow suppliers to create brands
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_permissions(self):
        """
        Override permissions based on request method.
        Both GET and POST require supplier or admin role.
        Regular users should use public endpoints.
        """
        self.permission_classes = [IsSupplierOrAdmin]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        Only suppliers and admins can access this endpoint.
        - Admins see all brands
        - Suppliers see their own brands (any status) and published brands from others
        """
        user = self.request.user
        
        if user.role == 'admin':
            return Brand.objects.all()
        elif user.role == 'supplier':
            # Suppliers can see their own brands (any status) and published brands
            from django.db.models import Q
            return Brand.objects.filter(
                Q(created_by=user) | Q(status__in=['approved', 'published'], is_publish=True)
            )
        else:
            # This should not happen due to permission checks, but fallback to empty queryset
            return Brand.objects.none()

    def list(self, request, *args, **kwargs):
        """
        Return all results when 'page' query param is absent.
        Preserve normal DRF pagination when the client explicitly requests a page.
        """
        if 'page' in request.query_params:
            return super().list(request, *args, **kwargs)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'next': None,
            'previous': None,
            'results': serializer.data,
        })

    def perform_create(self, serializer):
        # Set defaults based on user role
        if self.request.user.role == 'admin':
            serializer.save(status='published', is_publish=True, created_by=self.request.user)
        else:  # supplier
            serializer.save(status='pending', is_publish=False, created_by=self.request.user)


class ProductListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsSupplierOrAdmin]  # Custom permission that allows read for all, create for supplier/admin
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EnterpriseProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

    def get_permissions(self):
        """
        Override permissions based on request method.
        GET requests are allowed for everyone, POST requires supplier or admin.
        """
        if self.request.method == 'GET':
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [IsSupplierOrAdmin]
        return super().get_permissions()

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        - Anonymous users see only published products
        - Admins see all products
        - Suppliers see their own products (any status) and published products from others
        """
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'admin':
            return Product.objects.prefetch_related('variants__supplier_prices', 'images').all()
        elif self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'supplier':
            # Suppliers can see their own products (any status) and published products
            from django.db.models import Q
            return Product.objects.filter(
                Q(created_by=self.request.user) | Q(status__in=['approved', 'published'], is_publish=True)
            ).prefetch_related('variants__supplier_prices', 'images').all()
        else:
            # For anonymous users, show only published products
            return Product.objects.filter(
                status__in=['approved', 'published'],
                is_publish=True
            ).prefetch_related('variants__supplier_prices', 'images').all()

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
    permission_classes = [IsSupplierOrAdminForUpdates]  # Allow suppliers to edit their own products
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        """
        Override permissions based on request method.
        GET requests are allowed for everyone, PUT/PATCH/DELETE require supplier/admin ownership.
        """
        if self.request.method == 'GET':
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [IsSupplierOrAdminForUpdates]
        return super().get_permissions()

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        - Anonymous users see only published products
        - Admins see all products
        - Suppliers see their own products (any status) and published products from others
        """
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'admin':
            return Product.objects.prefetch_related('variants__supplier_prices', 'images').all()
        elif self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'supplier':
            # Suppliers can see their own products (any status) and published products
            from django.db.models import Q
            return Product.objects.filter(
                Q(created_by=self.request.user) | Q(status__in=['approved', 'published'], is_publish=True)
            ).prefetch_related('variants__supplier_prices', 'images').all()
        else:
            # For anonymous users, show only published products
            return Product.objects.filter(
                status__in=['approved', 'published'],
                is_publish=True
            ).prefetch_related('variants__supplier_prices', 'images').all()

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
    serializer_class = ProductVariantSerializer
    permission_classes = [IsSupplierOrAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        - Admins see all variants
        - Suppliers see variants of their own products and variants of published products
        """
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'admin':
            return ProductVariant.objects.select_related('product').all()
        elif self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'supplier':
            # Suppliers can see variants of their own products and variants of published products
            from django.db.models import Q
            return ProductVariant.objects.select_related('product').filter(
                Q(product__created_by=self.request.user) | Q(product__status__in=['approved', 'published'], product__is_publish=True)
            )
        else:
            # For anonymous users, show variants of published products only
            return ProductVariant.objects.select_related('product').filter(
                product__status__in=['approved', 'published'],
                product__is_publish=True
            )

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError as e:
            raise ValidationError({
                'detail': 'A variant with these specifications already exists for this product.'
            }) if 'unique' in str(e).lower() else e


class SupplierProductPriceListCreateView(generics.ListCreateAPIView):
    queryset = SupplierProductPrice.objects.select_related('product_variant', 'supplier').all()
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
    serializer_class = ProductVariantSerializer
    permission_classes = [IsSupplierOrAdmin]

    def get_queryset(self):
        """
        Override queryset based on user permissions.
        - Admins see all variants
        - Suppliers see variants of their own products only
        """
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'admin':
            return ProductVariant.objects.select_related('product').all()
        elif self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'supplier':
            # Suppliers can only access variants of their own products
            return ProductVariant.objects.select_related('product').filter(
                product__created_by=self.request.user
            )
        else:
            # For anonymous users, show variants of published products only
            return ProductVariant.objects.select_related('product').filter(
                product__status__in=['approved', 'published'],
                product__is_publish=True
            )


class SupplierProductPriceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SupplierProductPrice.objects.select_related('product_variant', 'supplier').all()
    serializer_class = SupplierProductPriceSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOrAdmin]


class ProductReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductReview.objects.select_related('product', 'user').all()
    serializer_class = ProductReviewSerializer
    permission_classes = [IsReviewOwnerOrAdminOrReadOnly]
