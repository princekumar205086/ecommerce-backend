"""
Enterprise-level optimized views with advanced caching, filtering, and performance optimizations
"""

from django.db.models import Q, Prefetch, Count, Avg, F, Case, When
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json

from .models import Product, ProductCategory, Brand, ProductReview, ProductVariant
from .serializers import (
    ProductCategorySerializer, PublicProductListSerializer, PublicProductSerializer,
    BrandSerializer, ProductReviewSerializer, ProductVariantSerializer
)
from .enterprise_filters import (
    EnterpriseProductFilter, EnterpriseCategoryFilter, EnterpriseBrandFilter,
    EnterpriseReviewFilter, EnterpriseVariantFilter
)
from .enterprise_cache import EnterpriseCacheManager, EnterpriseProductCache
from .mixins import MedixMallFilterMixin, MedixMallDetailMixin, MedixMallContextMixin


class EnterpriseProductListView(MedixMallFilterMixin, MedixMallContextMixin, generics.ListAPIView):
    """
    Enterprise-optimized product list view with:
    - Advanced filtering and search
    - Intelligent caching
    - Optimized database queries
    - Performance monitoring
    """
    serializer_class = PublicProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EnterpriseProductFilter
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'created_at', 'name', 'stock']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Optimized queryset with selective prefetching
        """
        queryset = super().get_queryset()
        
        # Optimize for list view - minimal prefetching
        return queryset.select_related(
            'category', 'brand', 'created_by'
        ).prefetch_related(
            'tags'
        ).annotate(
            # Add computed fields for better performance
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating')
        )
    
    def list(self, request, *args, **kwargs):
        """
        Cached list view with intelligent cache management
        """
        # Generate cache key based on request parameters
        filters = dict(request.query_params)
        ordering = request.query_params.get('ordering', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        cache_key = EnterpriseProductCache.get_product_list_cache_key(
            filters, ordering, page, page_size
        )
        
        # Try to get from cache first
        cached_data = EnterpriseCacheManager.get_cached_data('product_list', cache_key)
        if cached_data and not request.query_params.get('no_cache'):
            return Response(cached_data)
        
        # If not in cache, get fresh data
        response = super().list(request, *args, **kwargs)
        
        # Cache the response data
        if response.status_code == 200:
            EnterpriseCacheManager.set_cached_data(
                'product_list', cache_key, response.data
            )
        
        return response
    
    @swagger_auto_schema(
        operation_description="Get optimized list of products with enterprise-level filtering and caching",
        operation_summary="Enterprise Product List",
        tags=['Enterprise - Products'],
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search across multiple fields", type=openapi.TYPE_STRING),
            openapi.Parameter('q', openapi.IN_QUERY, description="Search query (alias for search)", type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID or name", type=openapi.TYPE_STRING),
            openapi.Parameter('brand', openapi.IN_QUERY, description="Filter by brand ID or name", type=openapi.TYPE_STRING),
            openapi.Parameter('product_type', openapi.IN_QUERY, description="Filter by product type", type=openapi.TYPE_STRING, enum=['medicine', 'equipment', 'pathology']),
            openapi.Parameter('price_min', openapi.IN_QUERY, description="Minimum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('price_max', openapi.IN_QUERY, description="Maximum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('in_stock', openapi.IN_QUERY, description="Filter by stock availability", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('prescription_required', openapi.IN_QUERY, description="Filter medicines by prescription requirement", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING, enum=['price', '-price', 'created_at', '-created_at', 'name', '-name']),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Page size", type=openapi.TYPE_INTEGER),
            openapi.Parameter('no_cache', openapi.IN_QUERY, description="Bypass cache", type=openapi.TYPE_BOOLEAN),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class EnterpriseProductDetailView(MedixMallDetailMixin, MedixMallContextMixin, generics.RetrieveAPIView):
    """
    Enterprise-optimized product detail view with heavy caching and prefetching
    """
    serializer_class = PublicProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """
        Heavily optimized queryset for detail view
        """
        return super().get_queryset().prefetch_related(
            Prefetch('variants', queryset=ProductVariant.objects.select_related().prefetch_related('attributes')),
            Prefetch('images'),
            Prefetch('reviews', queryset=ProductReview.objects.select_related('user')),
            'medicine_details',
            'equipment_details', 
            'pathology_details'
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Cached detail view with enhanced data
        """
        product_id = kwargs.get('pk')
        cache_key = EnterpriseProductCache.get_product_detail_cache_key(product_id)
        
        # Try cache first
        cached_data = EnterpriseCacheManager.get_cached_data('product_detail', cache_key)
        if cached_data and not request.query_params.get('no_cache'):
            return Response(cached_data)
        
        # Get fresh data
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add enhanced data
        self._add_enhanced_product_data(data, instance)
        
        # Cache the response
        EnterpriseCacheManager.set_cached_data('product_detail', cache_key, data)
        
        return Response(data)
    
    def _add_enhanced_product_data(self, data, instance):
        """
        Add enhanced data to product detail response
        """
        # Review statistics
        reviews = instance.reviews.all()
        data['review_stats'] = {
            'total_reviews': reviews.count(),
            'average_rating': reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
            'rating_distribution': {
                str(i): reviews.filter(rating=i).count() for i in range(1, 6)
            }
        }
        
        # Related products
        related_products = Product.objects.filter(
            category=instance.category,
            status__in=['approved', 'published'],
            is_publish=True
        ).exclude(id=instance.id).select_related('category', 'brand')[:4]
        
        data['related_products'] = PublicProductListSerializer(related_products, many=True).data
        
        # Price range for variants
        variants = instance.variants.filter(is_active=True)
        if variants:
            prices = [v.total_price for v in variants]
            data['price_range'] = {
                'min_price': min(prices),
                'max_price': max(prices),
                'has_variants': True
            }
        else:
            data['price_range'] = {
                'min_price': instance.price,
                'max_price': instance.price,
                'has_variants': False
            }


class EnterpriseProductSearchView(MedixMallFilterMixin, MedixMallContextMixin, APIView):
    """
    Enterprise-level search with advanced features and caching
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Enterprise-level product search with advanced filtering and intelligent caching",
        operation_summary="Enterprise Product Search",
        tags=['Enterprise - Products'],
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Search query", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('category', openapi.IN_QUERY, description="Category filter", type=openapi.TYPE_STRING),
            openapi.Parameter('brand', openapi.IN_QUERY, description="Brand filter", type=openapi.TYPE_STRING),
            openapi.Parameter('product_type', openapi.IN_QUERY, description="Product type filter", type=openapi.TYPE_STRING),
            openapi.Parameter('min_price', openapi.IN_QUERY, description="Minimum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, description="Maximum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('sort_by', openapi.IN_QUERY, description="Sort order", type=openapi.TYPE_STRING, 
                            enum=['relevance', 'price_low', 'price_high', 'name_asc', 'name_desc', 'newest']),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Page size", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request):
        """
        Perform enterprise search with caching
        """
        query = request.query_params.get('q', '').strip()
        
        # Extract filters
        filters = {
            'category': request.query_params.get('category'),
            'brand': request.query_params.get('brand'),
            'product_type': request.query_params.get('product_type'),
            'min_price': request.query_params.get('min_price'),
            'max_price': request.query_params.get('max_price'),
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Allow filtering without search query if filters are provided
        if not query and not filters:
            return Response({
                'error': 'Search query or filters are required',
                'results': [],
                'count': 0
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ordering = request.query_params.get('sort_by', 'relevance')
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)  # Limit page size
        
        # Check cache
        cache_key = EnterpriseProductCache.get_search_cache_key(query, filters, ordering, page)
        cached_data = EnterpriseCacheManager.get_cached_data('search_results', cache_key)
        
        if cached_data and not request.query_params.get('no_cache'):
            return Response(cached_data)
        
        # Perform search
        queryset = self.get_queryset()
        
        # Apply enterprise search
        filtered_queryset = self._apply_enterprise_search(queryset, query, filters)
        
        # Apply sorting
        sorted_queryset = self._apply_sorting(filtered_queryset, ordering, query)
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_queryset = sorted_queryset[start:end]
        
        # Serialize results
        serializer = PublicProductListSerializer(paginated_queryset, many=True)
        
        # Prepare response
        response_data = {
            'query': query,
            'filters': filters,
            'count': filtered_queryset.count(),
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
            'search_suggestions': self._get_search_suggestions(query),
            'facets': self._get_search_facets(filtered_queryset)
        }
        
        # Cache the results
        EnterpriseCacheManager.set_cached_data('search_results', cache_key, response_data)
        
        return Response(response_data)
    
    def get_queryset(self):
        """Get base queryset with optimizations"""
        queryset = Product.objects.filter(
            status__in=['approved', 'published'],
            is_publish=True
        ).select_related('category', 'brand').prefetch_related('tags')
        
        # Apply MedixMall filtering
        if hasattr(self, 'get_medixmall_mode') and self.get_medixmall_mode(self.request):
            queryset = queryset.filter(product_type='medicine')
        
        return queryset
    
    def _apply_enterprise_search(self, queryset, query, filters):
        """Apply enterprise-level search with filters"""
        # Prepare filter data
        filter_data = dict(filters)
        if query:  # Only add search if query is not empty
            filter_data['search'] = query
            
        # Use the enterprise filter
        filter_instance = EnterpriseProductFilter(data=filter_data, queryset=queryset)
        return filter_instance.qs
    
    def _apply_sorting(self, queryset, sort_by, query=None):
        """Apply intelligent sorting"""
        sort_options = {
            'relevance': ['-created_at'],  # Could be enhanced with search ranking
            'price_low': ['price', 'name'],
            'price_high': ['-price', 'name'],
            'name_asc': ['name'],
            'name_desc': ['-name'],
            'newest': ['-created_at'],
            'oldest': ['created_at'],
        }
        
        if sort_by in sort_options:
            return queryset.order_by(*sort_options[sort_by])
        
        return queryset.order_by('-created_at')
    
    def _get_search_suggestions(self, query):
        """Get search suggestions based on query"""
        # This could be enhanced with a proper search engine
        suggestions = []
        
        if len(query) >= 3:
            # Find similar product names
            similar_products = Product.objects.filter(
                name__icontains=query,
                status__in=['approved', 'published'],
                is_publish=True
            ).values_list('name', flat=True)[:5]
            
            suggestions.extend(list(similar_products))
        
        return suggestions
    
    def _get_search_facets(self, queryset):
        """Get search facets for filtering"""
        facets = {}
        
        # Category facets
        category_facets = queryset.values('category__name', 'category__id').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        facets['categories'] = [
            {'name': item['category__name'], 'id': item['category__id'], 'count': item['count']}
            for item in category_facets if item['category__name']
        ]
        
        # Brand facets
        brand_facets = queryset.values('brand__name', 'brand__id').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        facets['brands'] = [
            {'name': item['brand__name'], 'id': item['brand__id'], 'count': item['count']}
            for item in brand_facets if item['brand__name']
        ]
        
        # Product type facets
        type_facets = queryset.values('product_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        facets['product_types'] = [
            {'name': item['product_type'], 'count': item['count']}
            for item in type_facets
        ]
        
        # Price range facets
        price_ranges = [
            {'min': 0, 'max': 100, 'label': 'Under ₹100'},
            {'min': 100, 'max': 500, 'label': '₹100 - ₹500'},
            {'min': 500, 'max': 1000, 'label': '₹500 - ₹1000'},
            {'min': 1000, 'max': 5000, 'label': '₹1000 - ₹5000'},
            {'min': 5000, 'max': None, 'label': 'Above ₹5000'},
        ]
        
        price_facets = []
        for price_range in price_ranges:
            filter_q = Q(price__gte=price_range['min'])
            if price_range['max']:
                filter_q &= Q(price__lte=price_range['max'])
            
            count = queryset.filter(filter_q).count()
            if count > 0:
                price_facets.append({
                    'label': price_range['label'],
                    'min': price_range['min'],
                    'max': price_range['max'],
                    'count': count
                })
        
        facets['price_ranges'] = price_facets
        
        return facets


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@swagger_auto_schema(
    operation_description="Get search autocomplete suggestions",
    operation_summary="Search Autocomplete",
    tags=['Enterprise - Products'],
    manual_parameters=[
        openapi.Parameter('q', openapi.IN_QUERY, description="Search query", type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('limit', openapi.IN_QUERY, description="Maximum suggestions", type=openapi.TYPE_INTEGER),
    ]
)
def search_autocomplete(request):
    """
    Provide search autocomplete suggestions
    """
    query = request.query_params.get('q', '').strip()
    limit = int(request.query_params.get('limit', 10))
    
    if len(query) < 2:
        return Response({'suggestions': []})
    
    # Cache key for autocomplete
    cache_key = f"autocomplete:{query}:{limit}"
    cached_suggestions = cache.get(cache_key)
    
    if cached_suggestions:
        return Response({'suggestions': cached_suggestions})
    
    suggestions = []
    
    # Product name suggestions
    product_suggestions = Product.objects.filter(
        name__icontains=query,
        status__in=['approved', 'published'],
        is_publish=True
    ).values_list('name', flat=True)[:limit//2]
    
    suggestions.extend([{'text': name, 'type': 'product'} for name in product_suggestions])
    
    # Category suggestions
    category_suggestions = ProductCategory.objects.filter(
        name__icontains=query,
        status__in=['approved', 'published'],
        is_publish=True
    ).values_list('name', flat=True)[:limit//4]
    
    suggestions.extend([{'text': name, 'type': 'category'} for name in category_suggestions])
    
    # Brand suggestions
    brand_suggestions = Brand.objects.filter(
        name__icontains=query,
        status__in=['approved', 'published'],
        is_publish=True
    ).values_list('name', flat=True)[:limit//4]
    
    suggestions.extend([{'text': name, 'type': 'brand'} for name in brand_suggestions])
    
    # Cache suggestions for 5 minutes
    cache.set(cache_key, suggestions, 300)
    
    return Response({'suggestions': suggestions})