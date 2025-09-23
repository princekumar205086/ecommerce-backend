import time
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
