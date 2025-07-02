from django.db import models, transaction
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from products.models import Product, ProductVariant


class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_details = models.TextField(blank=True)
    gstin = models.CharField(max_length=15, blank=True, verbose_name="GSTIN")
    license_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='inventory_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='inventory_items')
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_items')
    batch_number = models.CharField(max_length=100, blank=True)
    hsn_code = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'variant', 'warehouse', 'batch_number')
        indexes = [
            models.Index(fields=['product', 'warehouse', 'batch_number']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['supplier']),
        ]

    def __str__(self):
        return f"{self.product.name} ({self.variant or 'default'}) @ {self.warehouse.name}"

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold


class InventoryTransaction(models.Model):
    IN = "IN"
    OUT = "OUT"
    ADJUSTMENT = "ADJ"

    TYPE_CHOICES = [
        (IN, "Stock In (Purchase/Restock)"),
        (OUT, "Stock Out (Sale/Usage)"),
        (ADJUSTMENT, "Adjustment"),
    ]

    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    txn_type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Optional link to source object (e.g., a Purchase or Sale record)
    source_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    source_object_id = models.PositiveIntegerField(null=True, blank=True)
    source = GenericForeignKey('source_content_type', 'source_object_id')

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['txn_type']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.get_txn_type_display()} | {self.quantity} units of {self.inventory_item}"

    def apply_transaction(self):
        with transaction.atomic():
            item = InventoryItem.objects.select_for_update().get(id=self.inventory_item.id)

            if self.txn_type == self.IN:
                item.quantity += self.quantity
            elif self.txn_type == self.OUT:
                if item.quantity < self.quantity:
                    raise ValueError(f"Not enough stock: {item.quantity} available, requested {self.quantity}")
                item.quantity -= self.quantity
            elif self.txn_type == self.ADJUSTMENT:
                # Do nothing — for manual stock correction
                pass

            item.save()
