from django.core.cache import cache
from django.db.models import Prefetch, Q, Count, Avg
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from .views import ProductViewSet, ProductCategoryViewSet, BrandViewSet, ProductReviewViewSet

class OptimizedProductViewSet(ProductViewSet):
    """Enterprise-optimized Product ViewSet with advanced caching and query optimization"""
    
    def get_queryset(self):
        """Optimized queryset with select_related and prefetch_related"""
        queryset = super().get_queryset().select_related(
            'category', 
            'brand', 
            'supplier'
        ).prefetch_related(
            'variants',
            'images',
            'attributes__attribute',
            'reviews'
        )
        
        # Apply filters
        category = self.request.query_params.get('category')
        brand = self.request.query_params.get('brand')
        product_type = self.request.query_params.get('product_type')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if category:
            queryset = queryset.filter(category_id=category)
        if brand:
            queryset = queryset.filter(brand_id=brand)
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        if min_price:
            queryset = queryset.filter(variants__price__gte=min_price)
        if max_price:
            queryset = queryset.filter(variants__price__lte=max_price)
            
        return queryset.distinct()
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        """Cached product list with pagination"""
        return super().list(request, *args, **kwargs)
    
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def retrieve(self, request, *args, **kwargs):
        """Cached product detail view"""
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def featured_products(self, request):
        """Get featured products with advanced caching"""
        cache_key = 'featured_products_list'
        featured = cache.get(cache_key)
        
        if not featured:
            featured = self.get_queryset().filter(
                status='approved'
            ).annotate(
                avg_rating=Avg('reviews__rating'),
                review_count=Count('reviews')
            ).order_by('-avg_rating', '-review_count')[:10]
            
            cache.set(cache_key, featured, 60 * 60)  # Cache for 1 hour
            
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Optimized search with caching"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Search query required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create cache key from search parameters
        cache_key = f"search_{hash(query)}_{request.query_params.get('category', '')}"
        results = cache.get(cache_key)
        
        if not results:
            queryset = self.get_queryset().filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(brand__name__icontains=query) |
                Q(category__name__icontains=query)
            )
            
            results = self.paginate_queryset(queryset)
            if results is not None:
                serializer = self.get_serializer(results, many=True)
                cache.set(cache_key, serializer.data, 60 * 5)  # Cache for 5 minutes
                return self.get_paginated_response(serializer.data)
        else:
            return Response(results)


class OptimizedProductCategoryViewSet(ProductCategoryViewSet):
    """Optimized Category ViewSet with caching"""
    
    @method_decorator(cache_page(60 * 60))  # Cache for 1 hour
    def list(self, request, *args, **kwargs):
        """Cached category list - categories rarely change"""
        return super().list(request, *args, **kwargs)


class OptimizedBrandViewSet(BrandViewSet):
    """Optimized Brand ViewSet with caching"""
    
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def list(self, request, *args, **kwargs):
        """Cached brand list"""
        return super().list(request, *args, **kwargs)


class OptimizedProductReviewViewSet(ProductReviewViewSet):
    """Optimized Review ViewSet with query optimization"""
    
    def get_queryset(self):
        """Optimized queryset with user and product prefetch"""
        return super().get_queryset().select_related(
            'user', 
            'product'
        ).prefetch_related(
            'product__images'
        )
    
    @action(detail=False, methods=['get'])
    def product_reviews(self, request):
        """Get reviews for a specific product with caching"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        cache_key = f"product_reviews_{product_id}"
        reviews = cache.get(cache_key)
        
        if not reviews:
            queryset = self.get_queryset().filter(product_id=product_id)
            reviews = self.paginate_queryset(queryset)
            if reviews is not None:
                serializer = self.get_serializer(reviews, many=True)
                cache.set(cache_key, serializer.data, 60 * 10)  # Cache for 10 minutes
                return self.get_paginated_response(serializer.data)
        else:
            return Response(reviews)


# Cache utility functions
class ProductCacheManager:
    """Manages product-related caching"""
    
    @staticmethod
    def invalidate_product_cache(product_id):
        """Invalidate all caches related to a product"""
        cache_keys = [
            f'product_{product_id}_detail',
            f'product_reviews_{product_id}',
            'featured_products_list',
            'categories_list',
            'brands_list'
        ]
        
        for key in cache_keys:
            cache.delete(key)
    
    @staticmethod
    def warm_cache():
        """Pre-warm frequently accessed cache entries"""
        from .models import ProductCategory, Brand
        
        # Pre-cache categories
        categories = list(ProductCategory.objects.filter(status='approved'))
        cache.set('categories_list', categories, 60 * 60)
        
        # Pre-cache brands
        brands = list(Brand.objects.filter(status='approved'))
        cache.set('brands_list', brands, 60 * 30)
        
        print("Cache warmed successfully")
