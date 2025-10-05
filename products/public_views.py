# products/public_views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Avg, Count, Min, Max
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    ProductCategory, Product, ProductReview, Brand, ProductVariant
)
from .serializers import (
    ProductCategorySerializer, BaseProductSerializer, PublicProductSerializer, PublicProductListSerializer, 
    ProductReviewSerializer, BrandSerializer, ProductVariantSerializer
)
from .mixins import MedixMallFilterMixin, MedixMallDetailMixin, MedixMallContextMixin, EnterpriseSearchMixin
from .enterprise_filters import EnterpriseProductFilter
from .enterprise_views import EnterpriseProductListView, EnterpriseProductSearchView


class PublicProductCategoryListView(generics.ListAPIView):
    """
    Public endpoint to list all published product categories.

    Behaviour change: when the client does NOT provide a `page` query parameter,
    return all matching categories (no pagination). If `page` is provided,
    regular DRF pagination is used.
    """
    queryset = ProductCategory.objects.filter(status__in=['approved', 'published'], is_publish=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']
    ordering = ['name']

    def list(self, request, *args, **kwargs):
        """Return all results when 'page' query param is absent.

        This preserves existing pagination behaviour when clients request a
        specific page (for example, `?page=2`). If `page` is not present we
        return the full result set in a single response.
        """
        # If client explicitly asked for a page, use normal pagination
        if 'page' in request.query_params:
            return super().list(request, *args, **kwargs)

        # No page param: return all results
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'next': None,
            'previous': None,
            'results': serializer.data,
        })

    @swagger_auto_schema(
        operation_description="Get list of all published product categories",
        operation_summary="List Product Categories (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search categories by name", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response('Success', ProductCategorySerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicBrandListView(generics.ListAPIView):
    """
    Public endpoint to list all published brands
    """
    queryset = Brand.objects.filter(status__in=['approved', 'published'], is_publish=True)
    serializer_class = BrandSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    ordering = ['name']

    @swagger_auto_schema(
        operation_description="Get list of all brands",
        operation_summary="List Brands (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search brands by name", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response('Success', BrandSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """Return all brands when 'page' query param is absent.

        Preserve normal DRF pagination when the client explicitly requests a page
        using the `page` query parameter.
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


class PublicProductListView(EnterpriseProductListView):
    """
    Public endpoint to list all published products with filtering and search
    Inherits from Enterprise view for optimized performance
    """
    pass  # All functionality inherited from EnterpriseProductListView

    @swagger_auto_schema(
        operation_description="Get list of all published products in stock. Respects user's MedixMall mode preference - if enabled, only shows medicine products.",
        operation_summary="List Products (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search products by name or description", type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('brand', openapi.IN_QUERY, description="Filter by brand ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('product_type', openapi.IN_QUERY, description="Filter by product type", type=openapi.TYPE_STRING, enum=['medicine', 'equipment', 'pathology']),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING, enum=['price', '-price', 'created_at', '-created_at', 'name', '-name']),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number for pagination (if not provided, returns all products)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <access_token> (optional for MedixMall mode)", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response(
                'Success', 
                PublicProductSerializer(many=True),
                headers={
                    'X-MedixMall-Mode': openapi.Schema(type=openapi.TYPE_STRING, description="true if user is in MedixMall mode, false otherwise")
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """Return all products when 'page' query param is absent.

        Preserve normal DRF pagination when the client explicitly requests a page
        using the `page` query parameter.
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

    def get_queryset(self):
        # Use the mixin's get_queryset which handles MedixMall filtering
        return super().get_queryset()


class PublicProductDetailView(MedixMallDetailMixin, MedixMallContextMixin, generics.RetrieveAPIView):
    """
    Public endpoint to view individual product details
    Respects user's MedixMall mode preference
    Includes full data: variants, images, reviews, supplier prices
    """
    serializer_class = PublicProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'

    @swagger_auto_schema(
        operation_description="Get detailed information about a specific product including reviews and related products. Respects user's MedixMall mode preference.",
        operation_summary="Product Detail (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <access_token> (optional for MedixMall mode)", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response(
                'Success', 
                PublicProductSerializer,
                headers={
                    'X-MedixMall-Mode': openapi.Schema(type=openapi.TYPE_STRING, description="true if user is in MedixMall mode, false otherwise")
                }
            ),
            404: 'Product not found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Add additional data
        data = serializer.data
        
        # Add review statistics
        reviews = instance.reviews.all()
        data['review_stats'] = {
            'total_reviews': reviews.count(),
            'average_rating': reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0,
            'rating_distribution': {
                '5': reviews.filter(rating=5).count(),
                '4': reviews.filter(rating=4).count(),
                '3': reviews.filter(rating=3).count(),
                '2': reviews.filter(rating=2).count(),
                '1': reviews.filter(rating=1).count(),
            }
        }
        
        # Add related products (same category, different product)
        related_products = Product.objects.filter(
            category=instance.category,
            status='published',
            is_publish=True
        ).exclude(id=instance.id)[:4]
        
        from .serializers import PublicProductSerializer
        data['related_products'] = PublicProductSerializer(related_products, many=True).data
        
        return Response(data)


class PublicProductReviewListView(generics.ListAPIView):
    """
    Public endpoint to list reviews for a specific product
    """
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="Get reviews for a specific product",
        operation_summary="Product Reviews (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('rating', openapi.IN_QUERY, description="Filter by rating", type=openapi.TYPE_INTEGER, enum=[1, 2, 3, 4, 5]),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING, enum=['created_at', '-created_at', 'rating', '-rating']),
        ],
        responses={
            200: openapi.Response('Success', ProductReviewSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return ProductReview.objects.filter(
            product_id=product_id
        ).select_related('user', 'product')


class PublicProductSearchView(EnterpriseProductSearchView):
    """
    Enterprise-level product search with advanced features
    Inherits from Enterprise search view for maximum performance
    """
    pass  # All functionality inherited from EnterpriseProductSearchView


class PublicFeaturedProductsView(MedixMallFilterMixin, MedixMallContextMixin, generics.ListAPIView):
    """
    Public endpoint for featured/trending products
    Respects user's MedixMall mode preference
    Uses lightweight serializer for better performance
    """
    serializer_class = PublicProductListSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Get featured/trending products (most reviewed products). Respects user's MedixMall mode preference.",
        operation_summary="Featured Products (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <access_token> (optional for MedixMall mode)", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response(
                'Success', 
                PublicProductSerializer(many=True),
                headers={
                    'X-MedixMall-Mode': openapi.Schema(type=openapi.TYPE_STRING, description="true if user is in MedixMall mode, false otherwise")
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Get base queryset with MedixMall filtering and add review count annotation
        queryset = super().get_queryset()
        return queryset.annotate(
            review_count=Count('reviews')
        ).order_by('-review_count', '-created_at')[:10]


class PublicProductsByCategory(MedixMallFilterMixin, MedixMallContextMixin, generics.ListAPIView):
    """
    Public endpoint to get products by category
    Respects user's MedixMall mode preference
    Enhanced to show parent category info, subcategories, and products from all subcategories
    Uses lightweight serializer for better performance
    """
    serializer_class = PublicProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="Get all products in a specific category. If the category has subcategories, includes products from all subcategories too. Respects user's MedixMall mode preference.",
        operation_summary="Products by Category (Public) - Enhanced with Subcategories",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING, enum=['price', '-price', 'created_at', '-created_at', 'name', '-name']),
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <access_token> (optional for MedixMall mode)", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response(
                'Success', 
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'category': openapi.Schema(type=openapi.TYPE_OBJECT, description="Parent category information"),
                        'subcategories': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="List of subcategories"),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Total products count"),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, description="Next page URL"),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, description="Previous page URL"),
                        'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="Product list"),
                    }
                ),
                headers={
                    'X-MedixMall-Mode': openapi.Schema(type=openapi.TYPE_STRING, description="true if user is in MedixMall mode, false otherwise")
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        from .models import ProductCategory
        
        category_id = self.kwargs.get('category_id')
        
        # Get the parent category
        try:
            parent_category = ProductCategory.objects.get(id=category_id, is_publish=True)
        except ProductCategory.DoesNotExist:
            from django.http import Http404
            raise Http404("Category not found")
        
        # Get all subcategories (children of this category)
        subcategory_ids = list(ProductCategory.objects.filter(
            parent_id=category_id,
            is_publish=True
        ).values_list('id', flat=True))
        
        # Create a list of all category IDs to search in (parent + subcategories)
        all_category_ids = [category_id] + subcategory_ids
        
        # Get base queryset with MedixMall filtering
        queryset = super().get_queryset()
        
        # Filter products from parent category and all subcategories
        return queryset.filter(category_id__in=all_category_ids)
    
    def list(self, request, *args, **kwargs):
        """Enhanced list method to include category and subcategory information"""
        from .models import ProductCategory
        
        category_id = self.kwargs.get('category_id')
        
        # Get the parent category
        try:
            parent_category = ProductCategory.objects.get(id=category_id, is_publish=True)
        except ProductCategory.DoesNotExist:
            from django.http import Http404
            raise Http404("Category not found")
        
        # Get all subcategories
        subcategories = ProductCategory.objects.filter(
            parent_id=category_id,
            is_publish=True
        ).order_by('name')
        
        # Get the standard product list response
        response = super().list(request, *args, **kwargs)
        
        # Enhance the response with category and subcategory information
        response.data = {
            'category': {
                'id': parent_category.id,
                'name': parent_category.name,
                'slug': parent_category.slug,
                'icon': parent_category.icon,
                'is_parent': subcategories.exists(),
                'total_subcategories': subcategories.count()
            },
            'subcategories': [
                {
                    'id': subcat.id,
                    'name': subcat.name,
                    'slug': subcat.slug,
                    'icon': subcat.icon,
                    'product_count': self.get_products_count_for_category(subcat.id)
                }
                for subcat in subcategories
            ],
            'count': response.data['count'],
            'next': response.data['next'],
            'previous': response.data['previous'],
            'results': response.data['results'],
        }
        
        return response
    
    def get_products_count_for_category(self, category_id):
        """Get product count for a specific category"""
        # Use the same base queryset logic to respect MedixMall mode
        base_queryset = super().get_queryset()
        return base_queryset.filter(category_id=category_id).count()


class PublicProductsByBrand(MedixMallFilterMixin, MedixMallContextMixin, generics.ListAPIView):
    """
    Public endpoint to get products by brand
    Respects user's MedixMall mode preference
    Uses lightweight serializer for better performance
    """
    serializer_class = PublicProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="Get all products by a specific brand. Respects user's MedixMall mode preference.",
        operation_summary="Products by Brand (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING, enum=['price', '-price', 'created_at', '-created_at', 'name', '-name']),
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <access_token> (optional for MedixMall mode)", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response(
                'Success', 
                PublicProductSerializer(many=True),
                headers={
                    'X-MedixMall-Mode': openapi.Schema(type=openapi.TYPE_STRING, description="true if user is in MedixMall mode, false otherwise")
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        brand_id = self.kwargs.get('brand_id')
        queryset = super().get_queryset()
        return queryset.filter(brand_id=brand_id)


class PublicProductsByType(MedixMallFilterMixin, MedixMallContextMixin, generics.ListAPIView):
    """
    Public endpoint to get products by product type (medicine, equipment, pathology)
    Respects user's MedixMall mode preference
    Uses lightweight serializer for better performance
    """
    serializer_class = PublicProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="Get all products by a specific product type (medicine, equipment, pathology). Respects user's MedixMall mode preference.",
        operation_summary="Products by Type (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING, enum=['price', '-price', 'created_at', '-created_at', 'name', '-name']),
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <access_token> (optional for MedixMall mode)", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response(
                'Success', 
                PublicProductSerializer(many=True),
                headers={
                    'X-MedixMall-Mode': openapi.Schema(type=openapi.TYPE_STRING, description="true if user is in MedixMall mode, false otherwise")
                }
            ),
            404: 'Invalid product type'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        product_type = self.kwargs.get('product_type')
        
        # Validate product_type against allowed choices
        valid_types = ['medicine', 'equipment', 'pathology']
        if product_type not in valid_types:
            from django.http import Http404
            raise Http404(f"Invalid product type. Must be one of: {', '.join(valid_types)}")
        
        queryset = super().get_queryset()
        return queryset.filter(product_type=product_type)