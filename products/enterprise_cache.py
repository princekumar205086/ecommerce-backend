"""
Enterprise-level caching system for products
Implements Redis caching with intelligent cache invalidation
"""

from django.core.cache import cache
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import json
import hashlib
from typing import Any, Optional, Dict, List
from .models import Product, ProductCategory, Brand, ProductReview, ProductVariant


class EnterpriseCacheManager:
    """
    Enterprise-level cache manager with intelligent caching strategies
    """
    
    # Cache timeouts (in seconds)
    CACHE_TIMEOUTS = {
        'product_list': 300,  # 5 minutes
        'product_detail': 600,  # 10 minutes
        'category_list': 900,  # 15 minutes
        'brand_list': 900,  # 15 minutes
        'search_results': 180,  # 3 minutes
        'filter_results': 240,  # 4 minutes
        'aggregated_data': 1800,  # 30 minutes
    }
    
    # Cache key prefixes
    CACHE_PREFIXES = {
        'product': 'product',
        'category': 'category',
        'brand': 'brand',
        'search': 'search',
        'filter': 'filter',
        'agg': 'aggregated',
    }
    
    @classmethod
    def generate_cache_key(cls, prefix: str, *args, **kwargs) -> str:
        """
        Generate a unique cache key based on prefix and parameters
        """
        # Create a string representation of all parameters
        params_str = '_'.join([str(arg) for arg in args])
        if kwargs:
            kwargs_str = '_'.join([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            params_str = f"{params_str}_{kwargs_str}" if params_str else kwargs_str
        
        # Hash the parameters if they're too long
        if len(params_str) > 100:
            params_str = hashlib.md5(params_str.encode()).hexdigest()
        
        return f"{cls.CACHE_PREFIXES[prefix]}:{params_str}"
    
    @classmethod
    def get_cached_data(cls, cache_type: str, key: str) -> Optional[Any]:
        """
        Get cached data with fallback handling
        """
        try:
            return cache.get(key)
        except Exception as e:
            # Log the error (in production, use proper logging)
            print(f"Cache retrieval error: {e}")
            return None
    
    @classmethod
    def set_cached_data(cls, cache_type: str, key: str, data: Any, timeout: Optional[int] = None) -> bool:
        """
        Set cached data with intelligent timeout
        """
        try:
            timeout = timeout or cls.CACHE_TIMEOUTS.get(cache_type, 300)
            cache.set(key, data, timeout)
            return True
        except Exception as e:
            # Log the error (in production, use proper logging)
            print(f"Cache setting error: {e}")
            return False
    
    @classmethod
    def invalidate_cache_pattern(cls, pattern: str) -> bool:
        """
        Invalidate cache keys matching a pattern
        """
        try:
            cache.delete_pattern(pattern)
            return True
        except Exception as e:
            print(f"Cache invalidation error: {e}")
            return False
    
    @classmethod
    def invalidate_product_caches(cls, product_id: int):
        """
        Invalidate all caches related to a specific product
        """
        patterns = [
            f"{cls.CACHE_PREFIXES['product']}:*:{product_id}:*",
            f"{cls.CACHE_PREFIXES['product']}:*:product_{product_id}",
            f"{cls.CACHE_PREFIXES['search']}:*",  # Invalidate all search results
            f"{cls.CACHE_PREFIXES['filter']}:*",  # Invalidate all filter results
        ]
        
        for pattern in patterns:
            cls.invalidate_cache_pattern(pattern)
    
    @classmethod
    def invalidate_category_caches(cls, category_id: int):
        """
        Invalidate all caches related to a specific category
        """
        patterns = [
            f"{cls.CACHE_PREFIXES['category']}:*",
            f"{cls.CACHE_PREFIXES['filter']}:*category*{category_id}*",
            f"{cls.CACHE_PREFIXES['search']}:*",
        ]
        
        for pattern in patterns:
            cls.invalidate_cache_pattern(pattern)
    
    @classmethod
    def invalidate_brand_caches(cls, brand_id: int):
        """
        Invalidate all caches related to a specific brand
        """
        patterns = [
            f"{cls.CACHE_PREFIXES['brand']}:*",
            f"{cls.CACHE_PREFIXES['filter']}:*brand*{brand_id}*",
            f"{cls.CACHE_PREFIXES['search']}:*",
        ]
        
        for pattern in patterns:
            cls.invalidate_cache_pattern(pattern)


class EnterpriseProductCache:
    """
    Product-specific caching with smart invalidation
    """
    
    @staticmethod
    def get_product_list_cache_key(filters: Dict, ordering: str = '', page: int = 1, page_size: int = 20) -> str:
        """
        Generate cache key for product list with filters
        """
        filter_hash = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:16]
        return EnterpriseCacheManager.generate_cache_key(
            'product', 'list', filter_hash, ordering, page, page_size
        )
    
    @staticmethod
    def get_product_detail_cache_key(product_id: int) -> str:
        """
        Generate cache key for product detail
        """
        return EnterpriseCacheManager.generate_cache_key('product', 'detail', product_id)
    
    @staticmethod
    def get_search_cache_key(query: str, filters: Dict, ordering: str = '', page: int = 1) -> str:
        """
        Generate cache key for search results
        """
        query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
        filter_hash = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:16]
        return EnterpriseCacheManager.generate_cache_key(
            'search', query_hash, filter_hash, ordering, page
        )


# Cache invalidation signal handlers

@receiver(post_save, sender=Product)
def invalidate_product_cache_on_save(sender, instance, **kwargs):
    """
    Invalidate product-related caches when a product is saved
    """
    EnterpriseCacheManager.invalidate_product_caches(instance.id)
    
    # Also invalidate category and brand caches if they changed
    if instance.category_id:
        EnterpriseCacheManager.invalidate_category_caches(instance.category_id)
    if instance.brand_id:
        EnterpriseCacheManager.invalidate_brand_caches(instance.brand_id)


@receiver(post_delete, sender=Product)
def invalidate_product_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate product-related caches when a product is deleted
    """
    EnterpriseCacheManager.invalidate_product_caches(instance.id)


@receiver(post_save, sender=ProductCategory)
def invalidate_category_cache_on_save(sender, instance, **kwargs):
    """
    Invalidate category-related caches when a category is saved
    """
    EnterpriseCacheManager.invalidate_category_caches(instance.id)


@receiver(post_delete, sender=ProductCategory)
def invalidate_category_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate category-related caches when a category is deleted
    """
    EnterpriseCacheManager.invalidate_category_caches(instance.id)


@receiver(post_save, sender=Brand)
def invalidate_brand_cache_on_save(sender, instance, **kwargs):
    """
    Invalidate brand-related caches when a brand is saved
    """
    EnterpriseCacheManager.invalidate_brand_caches(instance.id)


@receiver(post_delete, sender=Brand)
def invalidate_brand_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate brand-related caches when a brand is deleted
    """
    EnterpriseCacheManager.invalidate_brand_caches(instance.id)


@receiver(post_save, sender=ProductReview)
def invalidate_product_cache_on_review_save(sender, instance, **kwargs):
    """
    Invalidate product cache when a review is added/updated
    """
    EnterpriseCacheManager.invalidate_product_caches(instance.product_id)


@receiver(post_save, sender=ProductVariant)
def invalidate_product_cache_on_variant_save(sender, instance, **kwargs):
    """
    Invalidate product cache when a variant is added/updated
    """
    EnterpriseCacheManager.invalidate_product_caches(instance.product_id)


# Cache warming functions

def warm_popular_products_cache():
    """
    Pre-warm cache for popular products (can be run as a scheduled task)
    """
    from .models import Product
    from .serializers import PublicProductListSerializer
    
    # Get popular products (most recently created as a proxy for popularity)
    popular_products = Product.objects.filter(
        status__in=['approved', 'published'],
        is_publish=True
    ).order_by('-created_at')[:100]
    
    # Cache the serialized data
    cache_key = EnterpriseCacheManager.generate_cache_key('product', 'popular_list')
    serializer = PublicProductListSerializer(popular_products, many=True)
    EnterpriseCacheManager.set_cached_data('product_list', cache_key, serializer.data, timeout=900)


def warm_categories_cache():
    """
    Pre-warm cache for categories
    """
    from .models import ProductCategory
    from .serializers import ProductCategorySerializer
    
    categories = ProductCategory.objects.filter(
        status__in=['approved', 'published'],
        is_publish=True
    ).order_by('name')
    
    cache_key = EnterpriseCacheManager.generate_cache_key('category', 'all')
    serializer = ProductCategorySerializer(categories, many=True)
    EnterpriseCacheManager.set_cached_data('category_list', cache_key, serializer.data, timeout=900)


def warm_brands_cache():
    """
    Pre-warm cache for brands
    """
    from .models import Brand
    from .serializers import BrandSerializer
    
    brands = Brand.objects.filter(
        status__in=['approved', 'published'],
        is_publish=True
    ).order_by('name')
    
    cache_key = EnterpriseCacheManager.generate_cache_key('brand', 'all')
    serializer = BrandSerializer(brands, many=True)
    EnterpriseCacheManager.set_cached_data('brand_list', cache_key, serializer.data, timeout=900)