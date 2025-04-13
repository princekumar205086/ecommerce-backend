from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product
from django.core.exceptions import ValidationError

User = get_user_model()

class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, related_name='wishlisted_by')
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Ensure no duplicate products are added
        if self.products.distinct().count() != self.products.count():
            raise ValidationError("Duplicate products are not allowed in the wishlist.")

    def __str__(self):
        return f"{self.user.email if hasattr(self.user, 'email') else self.user}'s Wishlist"