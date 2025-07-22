# inventory/offline_views.py
"""
Views for offline sales management
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from ecommerce.permissions import IsSupplierOrAdmin
from .models import InventoryItem, Warehouse
from .offline_sales import OfflineSale, OfflineSaleItem, OfflineSaleManager
from .offline_serializers import (
    OfflineSaleSerializer,
    CreateOfflineSaleSerializer,
    VendorInventorySerializer,
    OfflineSaleReportSerializer
)


class CreateOfflineSaleView(generics.CreateAPIView):
    """
    Create a new offline sale
    Only suppliers can create offline sales
    """
    serializer_class = CreateOfflineSaleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Only suppliers can create offline sales"""
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Ensure only suppliers can create sales
        if self.request.user.role != 'supplier':
            raise permissions.PermissionDenied("Only suppliers can create offline sales")
        
        # The serializer handles the creation via OfflineSaleManager
        return serializer.save()

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            # Return the created sale with full details
            sale = response.data
            sale_obj = OfflineSale.objects.get(id=sale.id if hasattr(sale, 'id') else sale['id'])
            serializer = OfflineSaleSerializer(sale_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class OfflineSaleListView(generics.ListAPIView):
    """
    List offline sales
    Suppliers see only their sales, admins see all
    """
    serializer_class = OfflineSaleSerializer
    permission_classes = [IsSupplierOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['warehouse', 'payment_method', 'is_cancelled']
    search_fields = ['sale_number', 'customer_name', 'customer_phone']
    ordering_fields = ['created_at', 'total_amount', 'sale_date']
    ordering = ['-created_at']

    def get_queryset(self):
        # Add this check for schema generation
        if getattr(self, 'swagger_fake_view', False):
            from .offline_sales import OfflineSale
            return OfflineSale.objects.none()
            
        user = self.request.user
        queryset = OfflineSale.objects.select_related('vendor', 'warehouse').prefetch_related('items')
        
        if user.role == 'supplier':
            queryset = queryset.filter(vendor=user)
        
        return queryset


class OfflineSaleDetailView(generics.RetrieveAPIView):
    """
    Get details of a specific offline sale
    """
    serializer_class = OfflineSaleSerializer
    permission_classes = [IsSupplierOrAdmin]

    def get_queryset(self):
        # Add this check for schema generation
        if getattr(self, 'swagger_fake_view', False):
            from .offline_sales import OfflineSale
            return OfflineSale.objects.none()
            
        user = self.request.user
        queryset = OfflineSale.objects.select_related('vendor', 'warehouse').prefetch_related('items')
        
        if user.role == 'supplier':
            queryset = queryset.filter(vendor=user)
        
        return queryset


class CancelOfflineSaleView(APIView):
    """
    Cancel an offline sale and restore inventory
    """
    permission_classes = [IsSupplierOrAdmin]

    def post(self, request, sale_id):
        try:
            user = request.user
            
            # Get the sale
            if user.role == 'supplier':
                sale = OfflineSale.objects.get(id=sale_id, vendor=user)
            else:
                sale = OfflineSale.objects.get(id=sale_id)
            
            reason = request.data.get('reason', 'Cancelled by user')
            
            # Cancel the sale
            OfflineSaleManager.cancel_offline_sale(sale, reason)
            
            return Response({
                'message': 'Sale cancelled successfully',
                'sale_number': sale.sale_number
            }, status=status.HTTP_200_OK)
            
        except OfflineSale.DoesNotExist:
            return Response(
                {'error': 'Sale not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class VendorInventoryView(APIView):
    """
    Real-time inventory view for vendors
    Shows current stock levels for their assigned warehouses
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.role != 'supplier':
            return Response(
                {'error': 'Only suppliers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get inventory items for warehouses the vendor has access to
        # You can customize this logic based on your vendor-warehouse relationship
        inventory_items = InventoryItem.objects.select_related(
            'product', 'variant', 'warehouse'
        ).filter(
            quantity__gt=0  # Only show items with stock
        )
        
        # Build response data
        inventory_data = []
        for item in inventory_items:
            variant_details = None
            if item.variant:
                variant_details = {
                    'size': item.variant.size,
                    'weight': item.variant.weight,
                    'additional_price': str(item.variant.additional_price)
                }
            
            inventory_data.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'variant_id': item.variant.id if item.variant else None,
                'variant_details': variant_details,
                'quantity': item.quantity,
                'low_stock_threshold': item.low_stock_threshold,
                'is_low_stock': item.is_low_stock,
                'batch_number': item.batch_number,
                'expiry_date': item.expiry_date,
                'warehouse_name': item.warehouse.name
            })
        
        serializer = VendorInventorySerializer(inventory_data, many=True)
        return Response(serializer.data)


class OfflineSalesReportView(APIView):
    """
    Generate sales reports for offline sales
    """
    permission_classes = [IsSupplierOrAdmin]

    def post(self, request):
        serializer = OfflineSaleReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        date_from = serializer.validated_data['date_from']
        date_to = serializer.validated_data['date_to']
        warehouse = serializer.validated_data.get('warehouse')
        
        user = request.user
        
        # Build queryset
        queryset = OfflineSale.objects.filter(
            sale_date__date__gte=date_from,
            sale_date__date__lte=date_to,
            is_cancelled=False
        )
        
        if user.role == 'supplier':
            queryset = queryset.filter(vendor=user)
        
        if warehouse:
            queryset = queryset.filter(warehouse=warehouse)
        
        # Calculate aggregates
        totals = queryset.aggregate(
            total_sales=Sum('total_amount'),
            total_transactions=Count('id'),
            total_items_sold=Sum('items__quantity')
        )
        
        # Group by payment method
        payment_breakdown = queryset.values('payment_method').annotate(
            count=Count('id'),
            amount=Sum('total_amount')
        )
        
        # Top selling products
        top_products = OfflineSaleItem.objects.filter(
            sale__in=queryset
        ).values(
            'product__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-total_quantity')[:10]
        
        # Daily breakdown
        daily_sales = queryset.extra(
            select={'day': 'date(sale_date)'}
        ).values('day').annotate(
            count=Count('id'),
            amount=Sum('total_amount')
        ).order_by('day')
        
        return Response({
            'period': {
                'from': date_from,
                'to': date_to
            },
            'summary': {
                'total_sales': totals['total_sales'] or 0,
                'total_transactions': totals['total_transactions'] or 0,
                'total_items_sold': totals['total_items_sold'] or 0,
                'average_transaction': (
                    totals['total_sales'] / totals['total_transactions'] 
                    if totals['total_transactions'] else 0
                )
            },
            'payment_breakdown': list(payment_breakdown),
            'top_products': list(top_products),
            'daily_sales': list(daily_sales)
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def real_time_stock_check(request):
    """
    Real-time stock check for a specific product/variant in a warehouse
    """
    product_id = request.GET.get('product_id')
    variant_id = request.GET.get('variant_id')
    warehouse_id = request.GET.get('warehouse_id')
    
    if not product_id or not warehouse_id:
        return Response(
            {'error': 'product_id and warehouse_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        inventory_item = InventoryItem.objects.get(
            product_id=product_id,
            variant_id=variant_id if variant_id else None,
            warehouse_id=warehouse_id
        )
        
        return Response({
            'product_id': product_id,
            'variant_id': variant_id,
            'warehouse_id': warehouse_id,
            'current_stock': inventory_item.quantity,
            'low_stock_threshold': inventory_item.low_stock_threshold,
            'is_low_stock': inventory_item.is_low_stock,
            'last_updated': inventory_item.last_updated
        })
        
    except InventoryItem.DoesNotExist:
        return Response({
            'product_id': product_id,
            'variant_id': variant_id,
            'warehouse_id': warehouse_id,
            'current_stock': 0,
            'message': 'No inventory record found'
        })


@api_view(['GET'])
@permission_classes([IsSupplierOrAdmin])
def vendor_dashboard_stats(request):
    """
    Dashboard statistics for vendors
    """
    user = request.user
    
    if user.role != 'supplier':
        return Response(
            {'error': 'Only suppliers can access this endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Today's sales
    today = timezone.now().date()
    today_sales = OfflineSale.objects.filter(
        vendor=user,
        sale_date__date=today,
        is_cancelled=False
    ).aggregate(
        count=Count('id'),
        amount=Sum('total_amount')
    )
    
    # This week's sales
    week_start = today - timedelta(days=today.weekday())
    week_sales = OfflineSale.objects.filter(
        vendor=user,
        sale_date__date__gte=week_start,
        is_cancelled=False
    ).aggregate(
        count=Count('id'),
        amount=Sum('total_amount')
    )
    
    # Low stock alerts
    low_stock_count = InventoryItem.objects.filter(
        quantity__lte=F('low_stock_threshold')
    ).count()
    
    return Response({
        'today': {
            'sales_count': today_sales['count'] or 0,
            'sales_amount': today_sales['amount'] or 0
        },
        'this_week': {
            'sales_count': week_sales['count'] or 0,
            'sales_amount': week_sales['amount'] or 0
        },
        'low_stock_alerts': low_stock_count,
        'last_updated': timezone.now()
    })
