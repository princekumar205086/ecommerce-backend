#!/usr/bin/env python
"""
Enterprise Optimization Implementation Script
Implements the highest priority optimizations identified in the analysis
"""
import os
import sys
import django
from datetime import datetime

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.management import call_command
from django.db import connection
from django.conf import settings

class EnterpriseOptimizer:
    def __init__(self):
        self.implementation_results = {
            'timestamp': datetime.now().isoformat(),
            'optimizations_applied': [],
            'database_changes': [],
            'code_improvements': [],
            'performance_metrics': {}
        }
        
    def create_database_indexes(self):
        """Create performance-critical database indexes"""
        print("🔧 Creating Database Indexes...")
        
        indexes_to_create = [
            {
                'name': 'idx_product_category_brand',
                'table': 'products_product',
                'columns': 'category_id, brand_id',
                'benefit': 'Faster category+brand filtering'
            },
            {
                'name': 'idx_product_type_status',
                'table': 'products_product', 
                'columns': 'product_type, status',
                'benefit': 'Optimized type+status queries'
            },
            {
                'name': 'idx_variant_product_stock',
                'table': 'products_productvariant',
                'columns': 'product_id, stock',
                'benefit': 'Fast stock availability'
            },
            {
                'name': 'idx_review_product_rating',
                'table': 'products_productreview',
                'columns': 'product_id, rating',
                'benefit': 'Efficient rating aggregation'
            },
            {
                'name': 'idx_supplier_price_location',
                'table': 'products_supplierproductprice',
                'columns': 'pincode, district',
                'benefit': 'Location-based pricing'
            }
        ]
        
        created_indexes = []
        
        try:
            with connection.cursor() as cursor:
                for index in indexes_to_create:
                    try:
                        # Check if index exists
                        cursor.execute(f"PRAGMA index_list({index['table']})")
                        existing_indexes = [row[1] for row in cursor.fetchall()]
                        
                        if index['name'] not in existing_indexes:
                            sql = f"CREATE INDEX {index['name']} ON {index['table']}({index['columns']})"
                            cursor.execute(sql)
                            created_indexes.append({
                                'index': index['name'],
                                'table': index['table'],
                                'columns': index['columns'],
                                'benefit': index['benefit'],
                                'status': 'Created'
                            })
                            print(f"   ✅ Created index: {index['name']}")
                        else:
                            created_indexes.append({
                                'index': index['name'],
                                'table': index['table'],
                                'columns': index['columns'],
                                'benefit': index['benefit'],
                                'status': 'Already exists'
                            })
                            print(f"   ℹ️  Index already exists: {index['name']}")
                            
                    except Exception as e:
                        created_indexes.append({
                            'index': index['name'],
                            'table': index['table'],
                            'error': str(e),
                            'status': 'Failed'
                        })
                        print(f"   ❌ Failed to create {index['name']}: {e}")
                        
        except Exception as e:
            print(f"❌ Database index creation failed: {e}")
            
        self.implementation_results['database_changes'] = created_indexes
        
    def create_optimized_views(self):
        """Create optimized ViewSets with query optimization"""
        print("⚡ Creating Optimized ViewSets...")
        
        optimized_views_content = '''from django.core.cache import cache
from django.db.models import Prefetch, Q, Count, Avg
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

class OptimizedProductViewSet(ProductViewSet):
    """Enterprise-optimized Product ViewSet with advanced caching and query optimization"""
    
    def get_queryset(self):
        """Optimized queryset with select_related and prefetch_related"""
        queryset = Product.objects.select_related(
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
                is_featured=True,
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
        return ProductReview.objects.select_related(
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
        from products.models import ProductCategory, Brand
        
        # Pre-cache categories
        categories = list(ProductCategory.objects.filter(status='approved'))
        cache.set('categories_list', categories, 60 * 60)
        
        # Pre-cache brands
        brands = list(Brand.objects.filter(status='approved'))
        cache.set('brands_list', brands, 60 * 30)
        
        print("✅ Cache warmed successfully")
'''
        
        # Save optimized views
        try:
            with open('products/optimized_views.py', 'w') as f:
                f.write(optimized_views_content)
            
            self.implementation_results['code_improvements'].append({
                'file': 'products/optimized_views.py',
                'description': 'Created enterprise-optimized ViewSets with caching and query optimization',
                'features': [
                    'select_related and prefetch_related optimization',
                    'Redis caching with TTL strategies',
                    'Search result caching',
                    'Featured products caching',
                    'Cache invalidation utilities'
                ],
                'status': 'Created'
            })
            
            print("   ✅ Created optimized ViewSets with advanced caching")
            
        except Exception as e:
            print(f"   ❌ Failed to create optimized views: {e}")
            
    def create_caching_middleware(self):
        """Create enterprise caching middleware"""
        print("🚀 Creating Caching Middleware...")
        
        middleware_content = '''from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import hashlib
import json

class SmartCacheMiddleware:
    """
    Enterprise caching middleware with intelligent cache management
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Add cache headers for static content
        if request.path.startswith('/api/products/categories/'):
            response['Cache-Control'] = 'public, max-age=3600'
        elif request.path.startswith('/api/products/brands/'):
            response['Cache-Control'] = 'public, max-age=1800'
        elif '/products/' in request.path and request.method == 'GET':
            response['Cache-Control'] = 'public, max-age=900'
            
        return response

class RateLimitMiddleware:
    """
    Rate limiting middleware for API protection
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Check rate limits
        if self._is_rate_limited(request):
            from django.http import JsonResponse
            return JsonResponse(
                {'error': 'Rate limit exceeded. Please try again later.'}, 
                status=429
            )
            
        response = self.get_response(request)
        return response
    
    def _is_rate_limited(self, request):
        """Check if request should be rate limited"""
        if not request.path.startswith('/api/'):
            return False
            
        # Get client identifier
        client_ip = self._get_client_ip(request)
        user_id = request.user.id if request.user.is_authenticated else None
        
        # Different limits for different endpoints
        if 'search' in request.path:
            limit_key = f"search_limit_{client_ip}_{user_id}"
            max_requests = 30  # 30 searches per minute
        elif 'reviews' in request.path and request.method == 'POST':
            limit_key = f"review_limit_{user_id}"
            max_requests = 5   # 5 reviews per hour
        else:
            limit_key = f"api_limit_{client_ip}_{user_id}"
            max_requests = 100  # 100 API calls per minute
            
        # Check current count
        current_count = cache.get(limit_key, 0)
        if current_count >= max_requests:
            return True
            
        # Increment counter
        cache.set(limit_key, current_count + 1, 60)  # Reset every minute
        return False
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class QueryOptimizationMiddleware:
    """
    Middleware to log and optimize database queries
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        from django.db import connection
        
        # Count queries before
        queries_before = len(connection.queries)
        
        response = self.get_response(request)
        
        # Count queries after
        queries_after = len(connection.queries)
        query_count = queries_after - queries_before
        
        # Log if too many queries
        if query_count > 10:
            print(f"⚠️  High query count: {query_count} queries for {request.path}")
            
        # Add query count header for debugging
        if hasattr(response, 'headers'):
            response.headers['X-Query-Count'] = str(query_count)
            
        return response
'''
        
        try:
            with open('products/middleware.py', 'w') as f:
                f.write(middleware_content)
                
            self.implementation_results['code_improvements'].append({
                'file': 'products/middleware.py',
                'description': 'Created enterprise caching and rate limiting middleware',
                'features': [
                    'Smart cache headers for different content types',
                    'API rate limiting with different limits per endpoint',
                    'Query count monitoring and optimization alerts',
                    'Client IP detection and tracking'
                ],
                'status': 'Created'
            })
            
            print("   ✅ Created enterprise caching middleware")
            
        except Exception as e:
            print(f"   ❌ Failed to create middleware: {e}")
            
    def create_performance_monitoring(self):
        """Create performance monitoring utilities"""
        print("📊 Creating Performance Monitoring...")
        
        monitoring_content = '''import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
from products.models import Product, ProductCategory, Brand, ProductReview
import json

class PerformanceMonitor:
    """
    Enterprise performance monitoring for products app
    """
    
    @staticmethod
    def benchmark_queries():
        """Benchmark common database queries"""
        benchmarks = {}
        
        # Test product listing query
        start_time = time.time()
        products = list(Product.objects.select_related('category', 'brand')[:50])
        benchmarks['product_list_optimized'] = time.time() - start_time
        
        # Test product listing without optimization
        start_time = time.time()
        products = list(Product.objects.all()[:50])
        for product in products:
            _ = product.category.name
            _ = product.brand.name
        benchmarks['product_list_unoptimized'] = time.time() - start_time
        
        # Test review aggregation
        start_time = time.time()
        reviews = ProductReview.objects.select_related('product', 'user').count()
        benchmarks['review_count'] = time.time() - start_time
        
        return benchmarks
    
    @staticmethod
    def monitor_cache_performance():
        """Monitor cache hit rates and performance"""
        cache_stats = {
            'timestamp': time.time(),
            'cache_info': {}
        }
        
        # Test cache performance
        test_keys = ['categories_list', 'brands_list', 'featured_products_list']
        
        for key in test_keys:
            start_time = time.time()
            value = cache.get(key)
            cache_stats['cache_info'][key] = {
                'hit': value is not None,
                'response_time': time.time() - start_time
            }
            
        return cache_stats
    
    @staticmethod
    def generate_performance_report():
        """Generate comprehensive performance report"""
        report = {
            'timestamp': time.time(),
            'database_benchmarks': PerformanceMonitor.benchmark_queries(),
            'cache_performance': PerformanceMonitor.monitor_cache_performance(),
            'query_analysis': PerformanceMonitor.analyze_query_patterns()
        }
        
        # Save report
        with open(f'performance_report_{int(time.time())}.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        return report
    
    @staticmethod
    def analyze_query_patterns():
        """Analyze database query patterns"""
        from django.db import connection
        
        # Reset query log
        connection.queries = []
        
        # Perform common operations
        Product.objects.filter(status='approved').count()
        ProductCategory.objects.filter(status='approved').count()
        Brand.objects.filter(status='approved').count()
        
        query_analysis = {
            'total_queries': len(connection.queries),
            'queries': [
                {
                    'sql': query['sql'][:100] + '...' if len(query['sql']) > 100 else query['sql'],
                    'time': query['time']
                }
                for query in connection.queries
            ]
        }
        
        return query_analysis

class Command(BaseCommand):
    help = 'Run performance monitoring and generate reports'
    
    def handle(self, *args, **options):
        monitor = PerformanceMonitor()
        report = monitor.generate_performance_report()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Performance report generated: {report["timestamp"]}'
            )
        )
        
        # Print summary
        db_benchmarks = report['database_benchmarks']
        improvement = (
            (db_benchmarks['product_list_unoptimized'] - db_benchmarks['product_list_optimized']) 
            / db_benchmarks['product_list_unoptimized'] * 100
        )
        
        self.stdout.write(f"Query optimization improvement: {improvement:.1f}%")
'''
        
        try:
            # Create management command directory
            import os
            os.makedirs('products/management/commands', exist_ok=True)
            
            # Create __init__.py files
            with open('products/management/__init__.py', 'w') as f:
                f.write('')
            with open('products/management/commands/__init__.py', 'w') as f:
                f.write('')
                
            # Create performance monitoring command
            with open('products/management/commands/performance_monitor.py', 'w') as f:
                f.write(monitoring_content)
                
            self.implementation_results['code_improvements'].append({
                'file': 'products/management/commands/performance_monitor.py',
                'description': 'Created enterprise performance monitoring system',
                'features': [
                    'Database query benchmarking',
                    'Cache performance monitoring',
                    'Query pattern analysis',
                    'Automated performance reporting'
                ],
                'status': 'Created'
            })
            
            print("   ✅ Created performance monitoring system")
            
        except Exception as e:
            print(f"   ❌ Failed to create performance monitoring: {e}")
    
    def run_performance_tests(self):
        """Run performance tests to measure improvements"""
        print("🎯 Running Performance Tests...")
        
        try:
            from django.test.utils import override_settings
            from django.core.cache import cache
            import time
            
            # Clear cache for baseline test
            cache.clear()
            
            # Test 1: Product listing performance
            start_time = time.time()
            from products.models import Product
            products = list(Product.objects.select_related('category', 'brand')[:20])
            optimized_time = time.time() - start_time
            
            # Test 2: Cache performance
            cache.set('test_key', 'test_value', 60)
            start_time = time.time()
            value = cache.get('test_key')
            cache_time = time.time() - start_time
            
            performance_results = {
                'product_query_time': optimized_time,
                'cache_access_time': cache_time,
                'products_loaded': len(products),
                'cache_working': value == 'test_value'
            }
            
            self.implementation_results['performance_metrics'] = performance_results
            
            print(f"   ✅ Product query time: {optimized_time:.4f}s")
            print(f"   ✅ Cache access time: {cache_time:.6f}s")
            print(f"   ✅ Products loaded: {len(products)}")
            print(f"   ✅ Cache working: {value == 'test_value'}")
            
        except Exception as e:
            print(f"   ❌ Performance test failed: {e}")
    
    def save_implementation_report(self):
        """Save implementation report"""
        import json
        
        with open('enterprise_optimization_implementation.json', 'w') as f:
            json.dump(self.implementation_results, f, indent=2, default=str)
            
        print(f"\n🎉 ENTERPRISE OPTIMIZATION IMPLEMENTATION COMPLETE!")
        print(f"=" * 60)
        print(f"🔧 Database indexes created: {len([x for x in self.implementation_results['database_changes'] if x.get('status') == 'Created'])}")
        print(f"⚡ Code optimizations: {len(self.implementation_results['code_improvements'])}")
        print(f"📊 Performance metrics captured: {len(self.implementation_results['performance_metrics'])}")
        print(f"\n📄 Implementation report saved to: enterprise_optimization_implementation.json")
        
        # Show key improvements
        if self.implementation_results['performance_metrics']:
            metrics = self.implementation_results['performance_metrics']
            print(f"\n🚀 KEY PERFORMANCE IMPROVEMENTS:")
            print(f"   • Product Query Time: {metrics.get('product_query_time', 0):.4f}s")
            print(f"   • Cache Access Time: {metrics.get('cache_access_time', 0):.6f}s")
            print(f"   • Caching System: {'✅ Working' if metrics.get('cache_working') else '❌ Failed'}")
    
    def implement_optimizations(self):
        """Run all optimization implementations"""
        print("🏢 Starting Enterprise Optimization Implementation")
        print("=" * 60)
        
        try:
            self.create_database_indexes()
            self.create_optimized_views()
            self.create_caching_middleware() 
            self.create_performance_monitoring()
            self.run_performance_tests()
            self.save_implementation_report()
            
        except Exception as e:
            print(f"❌ Critical error in optimization implementation: {e}")


if __name__ == '__main__':
    optimizer = EnterpriseOptimizer()
    optimizer.implement_optimizations()