from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from products.models import Product, ProductVariant

User = settings.AUTH_USER_MODEL


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Shopping Cart"
        verbose_name_plural = "Shopping Carts"

    def __str__(self):
        return f"Cart {self.id} - {self.user.email}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        """Empty the cart"""
        self.items.all().delete()


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product', 'variant')
        ordering = ['-id']
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    def __str__(self):
        if self.variant:
            return f"{self.quantity} x {self.product.name} ({self.variant.size})"
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        if self.variant:
            return (float(self.product.price) + float(self.variant.additional_price)) * self.quantity
        return float(self.product.price) * self.quantity

    def clean(self):
        if self.variant and self.variant.product != self.product:
            raise ValidationError("Variant must belong to the selected product")

        if self.quantity < 1:
            raise ValidationError("Quantity must be at least 1")

        # Check stock availability only when creating new items
        if not self.pk:  # Only check stock for new items, not updates
            if self.variant:
                if self.quantity > self.variant.stock:
                    raise ValidationError(f"Only {self.variant.stock} items available in stock")
            else:
                if self.quantity > self.product.stock:
                    raise ValidationError(f"Only {self.product.stock} items available in stock")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
