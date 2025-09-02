"""
Supplier-specific order views
Suppliers can view orders containing their products and manage fulfillment
"""

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import Order, OrderItem
from .serializers import OrderSerializer
from ecommerce.permissions import IsSupplierOrAdmin


class SupplierOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Supplier-specific order management
    Suppliers can only see orders containing their products
    """
    serializer_class = OrderSerializer
    permission_classes = [IsSupplierOrAdmin]
    
    def get_queryset(self):
        """
        Return orders that contain products created by this supplier
        """
        if self.request.user.role == 'admin':
            return Order.objects.all()
        
        # For suppliers, only show orders with their products
        return Order.objects.filter(
            items__product__created_by=self.request.user
        ).distinct().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_ready_to_ship(self, request, pk=None):
        """Mark supplier's items in order as ready to ship"""
        order = self.get_object()
        
        # Check if supplier has products in this order
        supplier_items = order.items.filter(
            product__created_by=request.user
        )
        
        if not supplier_items.exists():
            return Response(
                {'error': 'You do not have products in this order'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update notes to indicate supplier readiness
        with transaction.atomic():
            order.notes = order.notes + f"\n{timezone.now().strftime('%Y-%m-%d %H:%M')} - Supplier {request.user.email} marked items as ready to ship"
            order.save()
        
        return Response({
            'status': 'success',
            'message': 'Items marked as ready to ship',
            'order_id': order.id,
            'order_number': order.order_number
        })
    
    @action(detail=False, methods=['get'])
    def my_orders_summary(self, request):
        """Get summary of orders for this supplier"""
        queryset = self.get_queryset()
        
        summary = {
            'total_orders': queryset.count(),
            'pending_orders': queryset.filter(status='pending').count(),
            'processing_orders': queryset.filter(status='processing').count(),
            'shipped_orders': queryset.filter(status='shipped').count(),
            'delivered_orders': queryset.filter(status='delivered').count(),
            'recent_orders': queryset[:10].values(
                'id', 'order_number', 'status', 'created_at', 'total'
            )
        }
        
        return Response(summary)


class SupplierOrderStatsView(APIView):
    """Supplier order statistics"""
    permission_classes = [IsSupplierOrAdmin]
    
    def get(self, request):
        """Get order statistics for supplier"""
        if request.user.role == 'admin':
            # Admin sees all stats
            orders = Order.objects.all()
        else:
            # Supplier sees only their orders
            orders = Order.objects.filter(
                items__product__created_by=request.user
            ).distinct()
        
        # Calculate stats
        total_orders = orders.count()
        total_revenue = sum(
            order.total for order in orders.filter(payment_status='paid')
        )
        
        # Monthly stats
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders = orders.filter(created_at__gte=thirty_days_ago)
        
        stats = {
            'total_orders': total_orders,
            'total_revenue': f"{total_revenue:.2f}",
            'recent_orders': recent_orders.count(),
            'status_breakdown': {
                'pending': orders.filter(status='pending').count(),
                'processing': orders.filter(status='processing').count(),
                'shipped': orders.filter(status='shipped').count(),
                'delivered': orders.filter(status='delivered').count(),
                'cancelled': orders.filter(status='cancelled').count(),
            },
            'payment_status': {
                'pending': orders.filter(payment_status='pending').count(),
                'paid': orders.filter(payment_status='paid').count(),
                'failed': orders.filter(payment_status='failed').count(),
            }
        }
        
        return Response(stats)