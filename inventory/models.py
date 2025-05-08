from django.db import models
from django.conf import settings
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
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'variant', 'warehouse')

    def __str__(self):
        return f"{self.product.name} ({self.variant or 'default'}) @ {self.warehouse.name}"

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

class InventoryTransaction(models.Model):
    IN = "IN"
    OUT = "OUT"
    TYPE_CHOICES = [
        (IN, "Stock In"),
        (OUT, "Stock Out"),
    ]
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    txn_type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.txn_type} {self.quantity} ({self.inventory_item})"