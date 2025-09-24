# accounts/middleware.py
import time
import logging
from collections import defaultdict
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
import json

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    """
    Enterprise-level rate limiting middleware
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            '/api/accounts/login/': {'requests': 5, 'window': 300},  # 5 requests per 5 minutes
            '/api/accounts/register/': {'requests': 3, 'window': 300},  # 3 requests per 5 minutes
            '/api/accounts/otp/request/': {'requests': 3, 'window': 300},  # 3 OTP requests per 5 minutes
            '/api/accounts/password/reset-request/': {'requests': 3, 'window': 900},  # 3 requests per 15 minutes
        }

    def __call__(self, request):
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check if endpoint is rate limited
        endpoint = request.path
        if endpoint in self.rate_limits:
            if self.is_rate_limited(client_ip, endpoint):
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please try again later.',
                    'retry_after': self.rate_limits[endpoint]['window']
                }, status=429)

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_rate_limited(self, client_ip, endpoint):
        """Check if client is rate limited for endpoint"""
        config = self.rate_limits[endpoint]
        cache_key = f"rate_limit:{client_ip}:{endpoint}"
        
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= config['requests']:
            return True
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, config['window'])
        return False


class SecurityHeadersMiddleware:
    """
    Add security headers to responses
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


class RequestLoggingMiddleware:
    """
    Enhanced request logging for audit and monitoring
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('accounts.audit')

    def __call__(self, request):
        start_time = time.time()
        
        # Log request
        if request.path.startswith('/api/accounts/'):
            self.log_request(request)
        
        response = self.get_response(request)
        
        # Log response
        if request.path.startswith('/api/accounts/'):
            duration = time.time() - start_time
            self.log_response(request, response, duration)
        
        return response

    def log_request(self, request):
        """Log incoming request"""
        user_info = 'Anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f"{request.user.email} ({request.user.role})"
        
        self.logger.info(
            f"REQUEST: {request.method} {request.path} | User: {user_info} | IP: {self.get_client_ip(request)}"
        )
        
        # Log sensitive endpoint access
        sensitive_endpoints = ['/login/', '/register/', '/password/', '/otp/']
        if any(endpoint in request.path for endpoint in sensitive_endpoints):
            self.logger.warning(
                f"SENSITIVE_ACCESS: {request.method} {request.path} | User: {user_info} | IP: {self.get_client_ip(request)}"
            )

    def log_response(self, request, response, duration):
        """Log response details"""
        user_info = 'Anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f"{request.user.email} ({request.user.role})"
        
        log_message = (
            f"RESPONSE: {request.method} {request.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration:.3f}s | "
            f"User: {user_info}"
        )
        
        if response.status_code >= 400:
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip