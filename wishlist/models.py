from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()

class Wishlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlists'
    )
    name = models.CharField(max_length=100, default='My Wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_wishlist_name_per_user'
            ),
            models.UniqueConstraint(
                fields=['user', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_wishlist_per_user'
            )
        ]

    def __str__(self):
        return f"{self.user.email}'s Wishlist: {self.name}"

    def clean(self):
        if self.is_default and Wishlist.objects.filter(
            user=self.user,
            is_default=True
        ).exclude(pk=self.pk).exists():
            raise ValidationError("User can have only one default wishlist")


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(
                fields=['wishlist', 'product'],
                condition=models.Q(variant__isnull=True),
                name='unique_product_in_wishlist'
            ),
            models.UniqueConstraint(
                fields=['wishlist', 'product', 'variant'],
                condition=models.Q(variant__isnull=False),
                name='unique_product_variant_in_wishlist'
            )
        ]

    def clean(self):
        if self.variant and self.variant.product != self.product:
            raise ValidationError("Variant must belong to the selected product")

        # Check for existing item with same product/variant
        existing = WishlistItem.objects.filter(
            wishlist=self.wishlist,
            product=self.product,
            variant=self.variant
        ).exclude(pk=self.pk).exists()

        if existing:
            raise ValidationError("This item already exists in the wishlist")