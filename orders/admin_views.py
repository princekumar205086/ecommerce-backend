from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from .models import Order
from .serializers import OrderSerializer


class AcceptOrderView(APIView):
    """Accept an order"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        with transaction.atomic():
            order.status = 'processing'
            order.notes = request.data.get('notes', '') + f"\nOrder accepted by admin {request.user.email}"
            order.save()
            
        return Response({
            'status': 'success',
            'message': 'Order accepted and moved to processing',
            'order_id': order.id,
            'order_number': order.order_number,
            'new_status': order.status
        })


class RejectOrderView(APIView):
    """Reject an order"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        reason = request.data.get('reason', 'No reason provided')
        
        with transaction.atomic():
            order.status = 'cancelled'
            order.notes = request.data.get('notes', '') + f"\nOrder rejected by admin {request.user.email}. Reason: {reason}"
            order.save()
            
        return Response({
            'status': 'success',
            'message': 'Order rejected',
            'order_id': order.id,
            'order_number': order.order_number,
            'new_status': order.status,
            'reason': reason
        })


class AssignShippingView(APIView):
    """Assign order to shipping partner"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        shipping_partner = request.data.get('shipping_partner', 'BlueDart')
        tracking_id = request.data.get('tracking_id', '')
        
        with transaction.atomic():
            order.status = 'shipped'
            order.shipping_partner = shipping_partner
            order.tracking_id = tracking_id
            order.notes = request.data.get('notes', '') + f"\nOrder assigned to {shipping_partner} by {request.user.email}"
            order.save()
            
        return Response({
            'status': 'success',
            'message': f'Order assigned to {shipping_partner}',
            'order_id': order.id,
            'order_number': order.order_number,
            'shipping_partner': shipping_partner,
            'tracking_id': tracking_id,
            'new_status': order.status
        })


class MarkDeliveredView(APIView):
    """Mark order as delivered"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
            
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        with transaction.atomic():
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            order.notes = request.data.get('notes', '') + f"\nOrder marked as delivered by {request.user.email}"
            order.save()
            
        return Response({
            'status': 'success',
            'message': 'Order marked as delivered',
            'order_id': order.id,
            'order_number': order.order_number,
            'delivered_at': order.delivered_at,
            'new_status': order.status
        })


class AdminOrderViewSet(viewsets.ModelViewSet):
    """Admin-only order management endpoints"""
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Admin can see all orders"""
        return Order.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def accept_order(self, request, pk=None):
        """Accept an order and move to processing"""
        order = self.get_object()
        
        with transaction.atomic():
            order.status = 'processing'
            order.notes = request.data.get('notes', '') + f"\nOrder accepted by admin {request.user.email}"
            order.save()
            
            # Log status change
            order.add_status_change('processing', f"Order accepted by {request.user.email}")
            
        return Response({
            'status': 'success',
            'message': 'Order accepted and moved to processing',
            'order_id': order.id,
            'order_number': order.order_number,
            'new_status': order.status
        })
    
    @action(detail=True, methods=['post'])
    def reject_order(self, request, pk=None):
        """Reject an order with reason"""
        order = self.get_object()
        reason = request.data.get('reason', 'No reason provided')
        
        with transaction.atomic():
            order.status = 'cancelled'
            order.notes = request.data.get('notes', '') + f"\nOrder rejected by admin {request.user.email}. Reason: {reason}"
            order.save()
            
            # Log status change
            order.add_status_change('cancelled', f"Order rejected by {request.user.email}. Reason: {reason}")
            
            # Restore stock if order was processing
            order.restore_stock()
            
        return Response({
            'status': 'success',
            'message': 'Order rejected and stock restored',
            'order_id': order.id,
            'order_number': order.order_number,
            'new_status': order.status,
            'reason': reason
        })
    
    @action(detail=True, methods=['post'])
    def assign_shipping(self, request, pk=None):
        """Assign order to shipping partner (like Shiprocket)"""
        order = self.get_object()
        shipping_partner = request.data.get('shipping_partner', 'Shiprocket')
        tracking_id = request.data.get('tracking_id', '')
        
        with transaction.atomic():
            order.status = 'shipped'
            order.shipping_partner = shipping_partner
            order.tracking_id = tracking_id
            order.notes = request.data.get('notes', '') + f"\nOrder assigned to {shipping_partner} by {request.user.email}"
            order.save()
            
            # Log status change
            order.add_status_change('shipped', f"Order shipped via {shipping_partner}. Tracking: {tracking_id}")
            
        return Response({
            'status': 'success',
            'message': f'Order assigned to {shipping_partner}',
            'order_id': order.id,
            'order_number': order.order_number,
            'shipping_partner': shipping_partner,
            'tracking_id': tracking_id,
            'new_status': order.status
        })
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """Mark order as delivered"""
        order = self.get_object()
        
        with transaction.atomic():
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            order.notes = request.data.get('notes', '') + f"\nOrder marked as delivered by {request.user.email}"
            order.save()
            
            # Log status change
            order.add_status_change('delivered', f"Order delivered. Confirmed by {request.user.email}")
            
        return Response({
            'status': 'success',
            'message': 'Order marked as delivered',
            'order_id': order.id,
            'order_number': order.order_number,
            'delivered_at': order.delivered_at,
            'new_status': order.status
        })
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get order statistics for admin dashboard"""
        from django.db.models import Count, Sum
        
        stats = {
            'total_orders': Order.objects.count(),
            'pending_orders': Order.objects.filter(status='pending').count(),
            'processing_orders': Order.objects.filter(status='processing').count(),
            'shipped_orders': Order.objects.filter(status='shipped').count(),
            'delivered_orders': Order.objects.filter(status='delivered').count(),
            'cancelled_orders': Order.objects.filter(status='cancelled').count(),
            'total_revenue': Order.objects.filter(
                payment_status='paid'
            ).aggregate(Sum('total'))['total__sum'] or 0,
            'pending_payments': Order.objects.filter(payment_status='pending').count(),
        }
        
        return Response(stats)