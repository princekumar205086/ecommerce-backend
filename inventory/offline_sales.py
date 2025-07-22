# inventory/offline_sales.py
"""
Offline Sales Management System for Vendors
This module handles in-store/offline sales by vendors and ensures real-time inventory sync
"""

from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from products.models import Product, ProductVariant
from .models import InventoryItem, InventoryTransaction, Warehouse

User = get_user_model()


class OfflineSale(models.Model):
    """
    Model to track offline/in-store sales made by vendors
    """
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer'),
        ('other', 'Other'),
    ]

    # Sale identification
    sale_number = models.CharField(max_length=50, unique=True, editable=False)
    vendor = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='offline_sales',
        limit_choices_to={'role': 'supplier'}
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='offline_sales'
    )
    
    # Customer details (optional for walk-in customers)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)
    
    # Sale details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    sale_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status tracking
    is_cancelled = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vendor', 'sale_date']),
            models.Index(fields=['warehouse', 'sale_date']),
            models.Index(fields=['sale_number']),
        ]

    def __str__(self):
        return f"Sale #{self.sale_number} by {self.vendor.full_name}"

    def save(self, *args, **kwargs):
        if not self.sale_number:
            self.sale_number = self.generate_sale_number()
        super().save(*args, **kwargs)

    def generate_sale_number(self):
        """Generate unique sale number"""
        from django.utils.crypto import get_random_string
        prefix = f"OS{timezone.now().strftime('%y%m%d')}"
        suffix = get_random_string(6, allowed_chars='0123456789')
        return f"{prefix}{suffix}"

    def calculate_totals(self):
        """Calculate sale totals from line items"""
        items = self.items.all()
        self.subtotal = sum(item.total_price for item in items)
        # Apply tax calculation (you can customize this)
        self.tax_amount = (self.subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.save()


class OfflineSaleItem(models.Model):
    """
    Individual items sold in an offline sale
    """
    sale = models.ForeignKey(
        OfflineSale,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='offline_sale_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='offline_sale_items'
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_per_item = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Batch tracking for medicines
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('sale', 'product', 'variant', 'batch_number')

    def __str__(self):
        variant_info = f" ({self.variant})" if self.variant else ""
        return f"{self.quantity}x {self.product.name}{variant_info}"

    @property
    def total_price(self):
        """Calculate total price for this line item"""
        unit_total = self.unit_price - self.discount_per_item
        return (unit_total * self.quantity).quantize(Decimal('0.01'))

    def clean(self):
        """Validate stock availability before saving"""
        if self.variant and self.variant.product != self.product:
            raise ValidationError("Variant does not belong to selected product")
        
        # Check stock availability
        try:
            inventory_item = InventoryItem.objects.get(
                product=self.product,
                variant=self.variant,
                warehouse=self.sale.warehouse
            )
            if self.quantity > inventory_item.quantity:
                raise ValidationError(
                    f"Insufficient stock. Available: {inventory_item.quantity}, "
                    f"Requested: {self.quantity}"
                )
        except InventoryItem.DoesNotExist:
            raise ValidationError(
                f"No inventory found for {self.product.name} in {self.sale.warehouse.name}"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class OfflineSaleManager:
    """
    Manager class for handling offline sales operations and inventory updates
    """
    
    @staticmethod
    def create_offline_sale(vendor, warehouse, items_data, customer_data=None, payment_data=None):
        """
        Create an offline sale with automatic inventory deduction
        
        Args:
            vendor: User object (supplier)
            warehouse: Warehouse object
            items_data: List of dicts with product, variant, quantity, unit_price
            customer_data: Dict with customer details (optional)
            payment_data: Dict with payment method and reference (optional)
        
        Returns:
            OfflineSale object
        """
        with transaction.atomic():
            # Create the sale
            sale = OfflineSale.objects.create(
                vendor=vendor,
                warehouse=warehouse,
                customer_name=customer_data.get('name', '') if customer_data else '',
                customer_phone=customer_data.get('phone', '') if customer_data else '',
                customer_email=customer_data.get('email', '') if customer_data else '',
                payment_method=payment_data.get('method', 'cash') if payment_data else 'cash',
                payment_reference=payment_data.get('reference', '') if payment_data else '',
                notes=payment_data.get('notes', '') if payment_data else '',
            )
            
            # Create sale items and update inventory
            for item_data in items_data:
                # Create sale item
                sale_item = OfflineSaleItem.objects.create(
                    sale=sale,
                    product=item_data['product'],
                    variant=item_data.get('variant'),
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    discount_per_item=item_data.get('discount_per_item', Decimal('0.00')),
                    batch_number=item_data.get('batch_number', ''),
                    expiry_date=item_data.get('expiry_date'),
                )
                
                # Update inventory immediately
                OfflineSaleManager.update_inventory_for_sale(sale_item)
            
            # Calculate totals
            sale.calculate_totals()
            
            return sale

    @staticmethod
    def update_inventory_for_sale(sale_item):
        """
        Update inventory and create inventory transaction for offline sale
        """
        with transaction.atomic():
            # Get inventory item
            inventory_item = InventoryItem.objects.select_for_update().get(
                product=sale_item.product,
                variant=sale_item.variant,
                warehouse=sale_item.sale.warehouse,
                batch_number=sale_item.batch_number if sale_item.batch_number else ''
            )
            
            # Check stock
            if inventory_item.quantity < sale_item.quantity:
                raise ValidationError(
                    f"Insufficient stock for {sale_item.product.name}. "
                    f"Available: {inventory_item.quantity}, Required: {sale_item.quantity}"
                )
            
            # Create inventory transaction
            inventory_transaction = InventoryTransaction.objects.create(
                inventory_item=inventory_item,
                txn_type=InventoryTransaction.OUT,
                quantity=sale_item.quantity,
                unit_cost=sale_item.unit_price,
                performed_by=sale_item.sale.vendor,
                notes=f"Offline sale #{sale_item.sale.sale_number}",
                source_content_type=ContentType.objects.get_for_model(OfflineSale),
                source_object_id=sale_item.sale.id
            )
            
            # Apply the transaction (this will update the inventory quantity)
            inventory_transaction.apply_transaction()

    @staticmethod
    def cancel_offline_sale(sale, reason=""):
        """
        Cancel an offline sale and restore inventory
        """
        if sale.is_cancelled:
            raise ValidationError("Sale is already cancelled")
            
        with transaction.atomic():
            # Restore inventory for each item
            for item in sale.items.all():
                inventory_item = InventoryItem.objects.select_for_update().get(
                    product=item.product,
                    variant=item.variant,
                    warehouse=sale.warehouse,
                    batch_number=item.batch_number if item.batch_number else ''
                )
                
                # Create reversal transaction
                InventoryTransaction.objects.create(
                    inventory_item=inventory_item,
                    txn_type=InventoryTransaction.IN,
                    quantity=item.quantity,
                    unit_cost=item.unit_price,
                    performed_by=sale.vendor,
                    notes=f"Cancellation of offline sale #{sale.sale_number}: {reason}",
                    source_content_type=ContentType.objects.get_for_model(OfflineSale),
                    source_object_id=sale.id
                ).apply_transaction()
            
            # Mark sale as cancelled
            sale.is_cancelled = True
            sale.cancelled_at = timezone.now()
            sale.cancelled_reason = reason
            sale.save()
