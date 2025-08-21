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
    ProductCategorySerializer, BaseProductSerializer, ProductReviewSerializer,
    BrandSerializer, ProductVariantSerializer
)


class PublicProductCategoryListView(generics.ListAPIView):
    """
    Public endpoint to list all published product categories
    """
    queryset = ProductCategory.objects.filter(status='published', is_publish=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']
    ordering = ['name']

    @swagger_auto_schema(
        operation_description="Get list of all published product categories",
        operation_summary="List Product Categories (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search categories by name or description", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response('Success', ProductCategorySerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicBrandListView(generics.ListAPIView):
    """
    Public endpoint to list all brands
    """
    queryset = Brand.objects.all()
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


class PublicProductListView(generics.ListAPIView):
    """
    Public endpoint to list all published products with filtering and search
    """
    serializer_class = BaseProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'product_type']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="Get list of all published products in stock",
        operation_summary="List Products (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search products by name or description", type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('brand', openapi.IN_QUERY, description="Filter by brand ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('product_type', openapi.IN_QUERY, description="Filter by product type", type=openapi.TYPE_STRING, enum=['medicine', 'equipment', 'pathology']),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING, enum=['price', '-price', 'created_at', '-created_at', 'name', '-name']),
        ],
        responses={
            200: openapi.Response('Success', BaseProductSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Product.objects.filter(
            status='published',
            is_publish=True,
            stock__gt=0  # Only show products in stock
        ).prefetch_related('variants', 'images').select_related('category', 'brand')


class PublicProductDetailView(generics.RetrieveAPIView):
    """
    Public endpoint to view individual product details
    """
    serializer_class = BaseProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'

    @swagger_auto_schema(
        operation_description="Get detailed information about a specific product including reviews and related products",
        operation_summary="Product Detail (Public)",
        tags=['Public - Products'],
        responses={
            200: openapi.Response('Success', BaseProductSerializer),
            404: 'Product not found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Product.objects.filter(
            status='published',
            is_publish=True
        ).prefetch_related('variants', 'images', 'reviews').select_related('category', 'brand')

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
        
        from .serializers import BaseProductSerializer
        data['related_products'] = BaseProductSerializer(related_products, many=True).data
        
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

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return ProductReview.objects.filter(
            product_id=product_id
        ).select_related('user', 'product')


class PublicProductSearchView(APIView):
    """
    Advanced product search with filters, sorting, and pagination
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Advanced product search with multiple filters and sorting options",
        operation_summary="Advanced Product Search (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Search query", type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, description="Category ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('brand', openapi.IN_QUERY, description="Brand ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('product_type', openapi.IN_QUERY, description="Product type", type=openapi.TYPE_STRING, enum=['medicine', 'equipment', 'pathology']),
            openapi.Parameter('min_price', openapi.IN_QUERY, description="Minimum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, description="Maximum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('sort_by', openapi.IN_QUERY, description="Sort by field", type=openapi.TYPE_STRING, enum=['price', '-price', 'name', '-name', 'created_at', '-created_at']),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page", type=openapi.TYPE_INTEGER, default=20),
        ],
        responses={
            200: openapi.Response(
                'Success',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'pagination': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'filters': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
        }
    )

    def get(self, request):
        # Get query parameters
        query = request.GET.get('q', '')
        category_id = request.GET.get('category')
        brand_id = request.GET.get('brand')
        product_type = request.GET.get('product_type')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        sort_by = request.GET.get('sort_by', '-created_at')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))

        # Base queryset
        products = Product.objects.filter(
            status='published',
            is_publish=True,
            stock__gt=0
        ).prefetch_related('variants', 'images').select_related('category', 'brand')

        # Apply filters
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(brand__name__icontains=query)
            )

        if category_id:
            products = products.filter(category_id=category_id)

        if brand_id:
            products = products.filter(brand_id=brand_id)

        if product_type:
            products = products.filter(product_type=product_type)

        if min_price:
            products = products.filter(price__gte=min_price)

        if max_price:
            products = products.filter(price__lte=max_price)

        # Apply sorting
        if sort_by in ['price', '-price', 'name', '-name', 'created_at', '-created_at']:
            products = products.order_by(sort_by)

        # Pagination
        paginator = Paginator(products, page_size)
        page_obj = paginator.get_page(page)

        # Serialize data
        serializer = BaseProductSerializer(page_obj.object_list, many=True)

        # Prepare response
        return Response({
            'results': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'filters': {
                'categories': list(ProductCategory.objects.filter(
                    status='published', is_publish=True
                ).values('id', 'name')),
                'brands': list(Brand.objects.all().values('id', 'name')),
                'product_types': list(Product.objects.filter(
                    status='published', is_publish=True
                ).values_list('product_type', flat=True).distinct()),
                'price_range': {
                    'min': products.aggregate(min_price=Min('price'))['min_price'] or 0,
                    'max': products.aggregate(max_price=Max('price'))['max_price'] or 0,
                }
            }
        })


class PublicFeaturedProductsView(generics.ListAPIView):
    """
    Public endpoint for featured/trending products
    """
    serializer_class = BaseProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # You can implement your own logic for featured products
        # For now, we'll show most reviewed products
        return Product.objects.filter(
            status='published',
            is_publish=True,
            stock__gt=0
        ).annotate(
            review_count=Count('reviews')
        ).order_by('-review_count', '-created_at')[:10]


class PublicProductsByCategory(generics.ListAPIView):
    """
    Public endpoint to get products by category
    """
    serializer_class = BaseProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return Product.objects.filter(
            category_id=category_id,
            status='published',
            is_publish=True,
            stock__gt=0
        ).prefetch_related('variants', 'images').select_related('category', 'brand')


class PublicProductsByBrand(generics.ListAPIView):
    """
    Public endpoint to get products by brand
    """
    serializer_class = BaseProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        brand_id = self.kwargs.get('brand_id')
        return Product.objects.filter(
            brand_id=brand_id,
            status='published',
            is_publish=True,
            stock__gt=0
        ).prefetch_related('variants', 'images').select_related('category', 'brand')