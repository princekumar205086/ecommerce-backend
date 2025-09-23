from django.core.cache import cache
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
            print(f"High query count: {query_count} queries for {request.path}")
            
        # Add query count header for debugging
        if hasattr(response, 'headers'):
            response['X-Query-Count'] = str(query_count)
            
        return response
