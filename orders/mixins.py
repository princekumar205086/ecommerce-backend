# orders/mixins.py
from django.db.models import Q, Count, F
from django.db import models


class MedixMallOrderFilterMixin:
    """
    Mixin to filter orders based on user's MedixMall mode preference
    When user has medixmall_mode=True (from profile or session), only show orders with medicine products only
    """
    
    def get_medixmall_mode(self, request):
        """Get MedixMall mode from user profile or session"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return getattr(request.user, 'medixmall_mode', False)
        else:
            return request.session.get('medixmall_mode', False)
    
    def get_queryset(self):
        # Get the base queryset
        if hasattr(super(), 'get_queryset'):
            queryset = super().get_queryset()
        else:
            from .models import Order
            queryset = Order.objects.all()
        
        # Apply MedixMall filtering for both authenticated and anonymous users
        # For anonymous users, orders are typically filtered by session or not available
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            # Admin users see all orders regardless of MedixMall mode
            if getattr(self.request.user, 'role', None) == 'admin':
                return queryset
            
            # Regular users: filter based on their MedixMall mode
            if self.get_medixmall_mode(self.request):
                # Only show orders that contain ONLY medicine products
                # This means all items in the order must be medicine type
                queryset = queryset.filter(
                    items__product__product_type='medicine'
                ).annotate(
                    # Count total items
                    total_items=Count('items'),
                    # Count medicine items
                    medicine_items=Count(
                        'items', 
                        filter=Q(items__product__product_type='medicine')
                    )
                ).filter(
                    # Only include orders where all items are medicine
                    total_items=F('medicine_items')
                ).distinct()
        
        return queryset


class MedixMallOrderContextMixin:
    """
    Mixin to add MedixMall mode context to order responses
    """
    
    def get_medixmall_mode(self, request):
        """Get MedixMall mode from user profile or session"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return getattr(request.user, 'medixmall_mode', False)
        else:
            return request.session.get('medixmall_mode', False)
    
    def finalize_response(self, request, response, *args, **kwargs):
        """Add MedixMall mode info to response headers"""
        response = super().finalize_response(request, response, *args, **kwargs)
        
        medixmall_mode = self.get_medixmall_mode(request)
        response['X-MedixMall-Mode'] = 'true' if medixmall_mode else 'false'
        
        return response