# inventory/real_time_sync.py
"""
Real-time stock synchronization service
This handles immediate stock updates across online and offline channels
"""

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

from .models import InventoryItem, InventoryTransaction

logger = logging.getLogger(__name__)


class RealTimeStockManager:
    """
    Centralized manager for real-time stock operations
    Ensures consistency between online and offline sales
    """
    
    @staticmethod
    def update_stock(product, variant, warehouse, quantity_change, transaction_type, 
                    performed_by, source_object=None, notes="", unit_cost=None, batch_number=""):
        """
        Update stock in real-time with proper transaction logging
        
        Args:
            product: Product instance
            variant: ProductVariant instance (can be None)
            warehouse: Warehouse instance
            quantity_change: int (positive for IN, negative for OUT)
            transaction_type: str ('IN', 'OUT', 'ADJ')
            performed_by: User instance
            source_object: Related object (Order, OfflineSale, etc.)
            notes: str
            unit_cost: Decimal (optional)
            batch_number: str (for medicines)
        
        Returns:
            InventoryTransaction instance
        
        Raises:
            ValidationError: If insufficient stock for OUT transactions
        """
        with transaction.atomic():
            # Get or create inventory item
            inventory_item, created = InventoryItem.objects.select_for_update().get_or_create(
                product=product,
                variant=variant,
                warehouse=warehouse,
                batch_number=batch_number,
                defaults={
                    'quantity': 0,
                    'low_stock_threshold': 10
                }
            )
            
            # For OUT transactions, check stock availability
            if transaction_type == InventoryTransaction.OUT:
                available_stock = inventory_item.quantity
                required_stock = abs(quantity_change)
                
                if available_stock < required_stock:
                    raise ValidationError(
                        f"Insufficient stock for {product.name}. "
                        f"Available: {available_stock}, Required: {required_stock}"
                    )
            
            # Create transaction record
            source_content_type = None
            source_object_id = None
            if source_object:
                source_content_type = ContentType.objects.get_for_model(source_object)
                source_object_id = source_object.id
            
            inventory_transaction = InventoryTransaction.objects.create(
                inventory_item=inventory_item,
                txn_type=transaction_type,
                quantity=abs(quantity_change),
                unit_cost=unit_cost,
                performed_by=performed_by,
                notes=notes,
                source_content_type=source_content_type,
                source_object_id=source_object_id
            )
            
            # Apply the transaction
            inventory_transaction.apply_transaction()
            
            # Log the operation
            logger.info(
                f"Stock updated: {product.name} | "
                f"Warehouse: {warehouse.name} | "
                f"Change: {quantity_change} | "
                f"New Stock: {inventory_item.quantity} | "
                f"By: {performed_by.email}"
            )
            
            return inventory_transaction

    @staticmethod
    def bulk_stock_update(stock_operations, performed_by, source_object=None):
        """
        Perform multiple stock operations atomically
        
        Args:
            stock_operations: List of dicts with stock operation details
            performed_by: User instance
            source_object: Related object for all operations
        
        Returns:
            List of InventoryTransaction instances
        """
        with transaction.atomic():
            transactions = []
            
            for operation in stock_operations:
                inventory_transaction = RealTimeStockManager.update_stock(
                    product=operation['product'],
                    variant=operation.get('variant'),
                    warehouse=operation['warehouse'],
                    quantity_change=operation['quantity_change'],
                    transaction_type=operation['transaction_type'],
                    performed_by=performed_by,
                    source_object=source_object,
                    notes=operation.get('notes', ''),
                    unit_cost=operation.get('unit_cost'),
                    batch_number=operation.get('batch_number', '')
                )
                transactions.append(inventory_transaction)
            
            return transactions

    @staticmethod
    def get_real_time_stock(product, variant=None, warehouse=None, batch_number=""):
        """
        Get current real-time stock level
        
        Args:
            product: Product instance
            variant: ProductVariant instance (optional)
            warehouse: Warehouse instance (optional)
            batch_number: str (optional)
        
        Returns:
            Dict with stock information
        """
        try:
            if warehouse:
                inventory_item = InventoryItem.objects.get(
                    product=product,
                    variant=variant,
                    warehouse=warehouse,
                    batch_number=batch_number
                )
                return {
                    'current_stock': inventory_item.quantity,
                    'low_stock_threshold': inventory_item.low_stock_threshold,
                    'is_low_stock': inventory_item.is_low_stock,
                    'last_updated': inventory_item.last_updated,
                    'warehouse': warehouse.name
                }
            else:
                # Return total stock across all warehouses
                inventory_items = InventoryItem.objects.filter(
                    product=product,
                    variant=variant,
                    batch_number=batch_number
                )
                
                total_stock = sum(item.quantity for item in inventory_items)
                warehouses = [
                    {
                        'warehouse': item.warehouse.name,
                        'stock': item.quantity,
                        'is_low_stock': item.is_low_stock
                    }
                    for item in inventory_items
                ]
                
                return {
                    'total_stock': total_stock,
                    'warehouse_breakdown': warehouses,
                    'last_updated': timezone.now()
                }
                
        except InventoryItem.DoesNotExist:
            return {
                'current_stock': 0,
                'message': 'No inventory record found'
            }

    @staticmethod
    def sync_product_stock_field(inventory_item):
        """
        Sync the Product.stock field with InventoryItem quantities
        This ensures backward compatibility with existing code
        """
        with transaction.atomic():
            from django.db import models
            product = inventory_item.product
            variant = inventory_item.variant
            
            if variant:
                # Update variant stock
                total_variant_stock = InventoryItem.objects.filter(
                    product=product,
                    variant=variant
                ).aggregate(
                    total=models.Sum('quantity')
                )['total'] or 0
                
                variant.stock = total_variant_stock
                variant.save()
            else:
                # Update product stock (sum of all variants and default)
                total_product_stock = InventoryItem.objects.filter(
                    product=product
                ).aggregate(
                    total=models.Sum('quantity')
                )['total'] or 0
                
                product.stock = total_product_stock
                product.save()

    @staticmethod
    def check_low_stock_alerts():
        """
        Check for low stock items and create alerts
        """
        from analytics.models import InventoryAlert
        from django.db import models
        
        low_stock_items = InventoryItem.objects.filter(
            quantity__lte=models.F('low_stock_threshold')
        ).select_related('product', 'warehouse')
        
        for item in low_stock_items:
            # Check if alert already exists
            existing_alert = InventoryAlert.objects.filter(
                product=item.product,
                alert_type='low_stock',
                is_resolved=False
            ).first()
            
            if not existing_alert:
                InventoryAlert.objects.create(
                    product=item.product,
                    alert_type='low_stock',
                    current_quantity=item.quantity,
                    threshold=item.low_stock_threshold,
                    message=f"Low stock alert for {item.product.name} in {item.warehouse.name}. Current stock: {item.quantity}"
                )
                
                logger.warning(f"Low stock alert created for {item.product.name}")


# Signal handlers for real-time sync
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=InventoryTransaction)
def sync_stock_on_transaction(sender, instance, created, **kwargs):
    """
    Sync product stock fields when inventory transactions are created
    """
    if created:
        RealTimeStockManager.sync_product_stock_field(instance.inventory_item)
        
        # Check for low stock alerts
        RealTimeStockManager.check_low_stock_alerts()


# WebSocket support for real-time updates (optional)
class StockWebSocketManager:
    """
    WebSocket manager for real-time stock updates
    This can be used to push stock changes to connected clients
    """
    
    @staticmethod
    def broadcast_stock_update(product_id, variant_id, warehouse_id, new_stock):
        """
        Broadcast stock update to WebSocket clients
        Implement this based on your WebSocket setup (channels, socket.io, etc.)
        """
        # Example implementation with Django Channels
        # from channels.layers import get_channel_layer
        # from asgiref.sync import async_to_sync
        
        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     f"stock_updates_{warehouse_id}",
        #     {
        #         "type": "stock_update",
        #         "product_id": product_id,
        #         "variant_id": variant_id,
        #         "warehouse_id": warehouse_id,
        #         "new_stock": new_stock,
        #         "timestamp": timezone.now().isoformat()
        #     }
        # )
        
        logger.info(f"Stock update broadcast: Product {product_id}, Stock: {new_stock}")


# Middleware for real-time stock validation
class RealTimeStockMiddleware:
    """
    Middleware to ensure stock consistency across requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add real-time stock validation for cart operations
        if request.path.startswith('/api/cart/') and request.method in ['POST', 'PUT', 'PATCH']:
            # You can add cart-specific stock validation here
            pass
        
        return response
