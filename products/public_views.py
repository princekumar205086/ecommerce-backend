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
from .mixins import MedixMallFilterMixin, MedixMallContextMixin, EnterpriseSearchMixin


class PublicProductCategoryListView(generics.ListAPIView):
    """
    Public endpoint to list all published product categories.

    Behaviour change: when the client does NOT provide a `page` query parameter,
    return all matching categories (no pagination). If `page` is provided,
    regular DRF pagination is used.
    """
    queryset = ProductCategory.objects.filter(status='published', is_publish=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']
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


class PublicProductListView(MedixMallFilterMixin, MedixMallContextMixin, generics.ListAPIView):
    """
    Public endpoint to list all published products with filtering and search
    Respects user's MedixMall mode preference
    """
    serializer_class = BaseProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'product_type']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

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
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <access_token> (optional for MedixMall mode)", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response(
                'Success', 
                BaseProductSerializer(many=True),
                headers={
                    'X-MedixMall-Mode': openapi.Schema(type=openapi.TYPE_STRING, description="true if user is in MedixMall mode, false otherwise")
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Use the mixin's get_queryset which handles MedixMall filtering
        return super().get_queryset()


class PublicProductDetailView(MedixMallFilterMixin, MedixMallContextMixin, generics.RetrieveAPIView):
    """
    Public endpoint to view individual product details
    Respects user's MedixMall mode preference
    """
    serializer_class = BaseProductSerializer
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
                BaseProductSerializer,
                headers={
                    'X-MedixMall-Mode': openapi.Schema(type=openapi.TYPE_STRING, description="true if user is in MedixMall mode, false otherwise")
                }
            ),
            404: 'Product not found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Use the mixin's queryset and filter further for product details
        queryset = super().get_queryset()
        return queryset.prefetch_related('variants', 'images', 'reviews')

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


class PublicProductSearchView(MedixMallFilterMixin, MedixMallContextMixin, EnterpriseSearchMixin, APIView):
    """
    Enterprise-level product search with advanced features
    Similar to Amazon/Flipkart search capabilities
    Respects user's MedixMall mode preference
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Enterprise-level product search with multiple filters, intelligent sorting, and fuzzy matching. Respects user's MedixMall mode preference - if enabled, only searches medicine products.",
        operation_summary="Enterprise Product Search (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Search query (supports multiple terms, fuzzy matching)", type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, description="Category ID or name", type=openapi.TYPE_STRING),
            openapi.Parameter('brand', openapi.IN_QUERY, description="Brand ID or name", type=openapi.TYPE_STRING),
            openapi.Parameter('product_type', openapi.IN_QUERY, description="Product type", type=openapi.TYPE_STRING, enum=['medicine', 'equipment', 'pathology']),
            openapi.Parameter('min_price', openapi.IN_QUERY, description="Minimum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, description="Maximum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('sort_by', openapi.IN_QUERY, description="Sort by field", type=openapi.TYPE_STRING, 
                            enum=['relevance', 'price_low', 'price_high', 'name_asc', 'name_desc', 'newest', 'oldest', 'popularity', 'rating'], default='relevance'),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max 50)", type=openapi.TYPE_INTEGER, default=20),
            openapi.Parameter('in_stock_only', openapi.IN_QUERY, description="Show only products in stock", type=openapi.TYPE_BOOLEAN, default=True),
            openapi.Parameter('prescription_required', openapi.IN_QUERY, description="Filter by prescription requirement (medicines only)", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('form', openapi.IN_QUERY, description="Medicine form (tablet, syrup, etc.)", type=openapi.TYPE_STRING),
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <access_token> (optional for MedixMall mode)", type=openapi.TYPE_STRING, required=False),
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
                        'search_suggestions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'medixmall_mode': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                ),
                headers={
                    'X-MedixMall-Mode': openapi.Schema(type=openapi.TYPE_STRING, description="true if user is in MedixMall mode, false otherwise")
                }
            ),
        }
    )

    def get(self, request):
        # Get query parameters
        query = request.GET.get('q', '').strip()
        page = max(int(request.GET.get('page', 1)), 1)
        page_size = min(max(int(request.GET.get('page_size', 20)), 1), 50)  # Max 50 items per page
        sort_by = request.GET.get('sort_by', 'relevance')

        # Collect all filter parameters
        filters = {
            'category': request.GET.get('category'),
            'brand': request.GET.get('brand'),
            'product_type': request.GET.get('product_type'),
            'min_price': request.GET.get('min_price'),
            'max_price': request.GET.get('max_price'),
            'in_stock_only': request.GET.get('in_stock_only', 'true').lower() == 'true',
            'prescription_required': request.GET.get('prescription_required'),
            'form': request.GET.get('form'),
        }

        # Get base queryset with MedixMall filtering
        products = self.get_queryset().prefetch_related('variants', 'images').select_related('category', 'brand')

        # Apply enterprise search
        if query:
            products = self.apply_enterprise_search(products, query)

        # Apply smart filters
        products = self.apply_smart_filters(products, filters)

        # Apply intelligent sorting
        products = self.apply_intelligent_sorting(products, sort_by, query)

        # Pagination
        paginator = Paginator(products, page_size)
        page_obj = paginator.get_page(page)

        # Serialize data
        serializer = BaseProductSerializer(page_obj.object_list, many=True)

        # Generate search suggestions
        search_suggestions = self.generate_search_suggestions(query, products)

        # Check if user is in MedixMall mode
        medixmall_mode = (
            hasattr(request, 'user') and 
            request.user.is_authenticated and 
            getattr(request.user, 'medixmall_mode', False)
        )

        # Prepare response
        response_data = {
            'results': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'filters': self.get_available_filters(products),
            'search_suggestions': search_suggestions,
            'medixmall_mode': medixmall_mode,
            'search_query': query,
            'applied_filters': {k: v for k, v in filters.items() if v is not None},
        }

        response = Response(response_data)
        
        # Add MedixMall mode to response headers
        response['X-MedixMall-Mode'] = 'true' if medixmall_mode else 'false'
        response['X-Search-Results-Count'] = str(paginator.count)
        
        return response

    def generate_search_suggestions(self, query, products):
        """Generate intelligent search suggestions"""
        if not query or len(query) < 2:
            return []

        suggestions = set()
        
        # Get unique product names that contain the query
        for product in products[:20]:  # Limit for performance
            name_words = product.name.lower().split()
            for word in name_words:
                if len(word) > 2 and query.lower() in word.lower():
                    suggestions.add(word.title())
        
        # Add category suggestions
        categories = products.values_list('category__name', flat=True).distinct()[:10]
        for category in categories:
            if category and query.lower() in category.lower():
                suggestions.add(category)
        
        # Add brand suggestions
        brands = products.values_list('brand__name', flat=True).distinct()[:10]
        for brand in brands:
            if brand and query.lower() in brand.lower():
                suggestions.add(brand)

        return list(suggestions)[:10]  # Return max 10 suggestions

    def get_available_filters(self, products):
        """Get available filter options based on current results"""
        return {
            'categories': list(products.values_list('category__id', 'category__name').distinct()),
            'brands': list(products.values_list('brand__id', 'brand__name').distinct()),
            'product_types': list(products.values_list('product_type', flat=True).distinct()),
            'price_range': {
                'min': products.aggregate(min_price=Min('price'))['min_price'] or 0,
                'max': products.aggregate(max_price=Max('price'))['max_price'] or 0,
            },
            'forms': list(products.exclude(medicine_details__form='').values_list('medicine_details__form', flat=True).distinct()) if products.filter(product_type='medicine').exists() else [],
        }


class PublicFeaturedProductsView(MedixMallFilterMixin, MedixMallContextMixin, generics.ListAPIView):
    """
    Public endpoint for featured/trending products
    Respects user's MedixMall mode preference
    """
    serializer_class = BaseProductSerializer
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
                BaseProductSerializer(many=True),
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
    """
    serializer_class = BaseProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="Get all products in a specific category. Respects user's MedixMall mode preference.",
        operation_summary="Products by Category (Public)",
        tags=['Public - Products'],
        manual_parameters=[
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING, enum=['price', '-price', 'created_at', '-created_at', 'name', '-name']),
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <access_token> (optional for MedixMall mode)", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response(
                'Success', 
                BaseProductSerializer(many=True),
                headers={
                    'X-MedixMall-Mode': openapi.Schema(type=openapi.TYPE_STRING, description="true if user is in MedixMall mode, false otherwise")
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        queryset = super().get_queryset()
        return queryset.filter(category_id=category_id)


class PublicProductsByBrand(MedixMallFilterMixin, MedixMallContextMixin, generics.ListAPIView):
    """
    Public endpoint to get products by brand
    Respects user's MedixMall mode preference
    """
    serializer_class = BaseProductSerializer
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
                BaseProductSerializer(many=True),
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