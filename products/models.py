from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now

User = get_user_model()

STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('reviewed', 'Reviewed'),
    ('rejected', 'Rejected'),
    ('published', 'Published'),
)

PRODUCT_TYPE_CHOICES = (
    ('pathology', 'Pathology Product'),
    ('doctor', 'Doctor Product'),
    ('medical', 'Medical Product'),
)


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # Default user ID
    created_at = models.DateTimeField(auto_now_add=True)  # Removed default

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # Default user ID
    created_at = models.DateTimeField(auto_now_add=True)  # Removed default
    is_publish = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return self.name


class ProductSubCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, default=1)  # Default category ID
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # Default user ID
    created_at = models.DateTimeField(auto_now_add=True)  # Removed default
    is_publish = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Default price
    stock = models.IntegerField(default=0)  # Default stock
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, default=1)  # Default category ID
    subcategory = models.ForeignKey(ProductSubCategory, on_delete=models.CASCADE, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='medical')  # Default type
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # Default user ID
    created_at = models.DateTimeField(auto_now_add=True)  # Removed default
    is_publish = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants',
                                default=1)  # Default product ID
    size = models.CharField(max_length=50, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Default additional price

    def __str__(self):
        return f"Variant of {self.product.name}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews',
                                default=1)  # Default product ID
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # Default user ID
    rating = models.IntegerField(default=1)  # Default rating
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Removed default

    def __str__(self):
        return f"Review by {self.user.email} on {self.product.name}"


# Slug Auto-generation
@receiver(pre_save, sender=ProductCategory)
@receiver(pre_save, sender=ProductSubCategory)
@receiver(pre_save, sender=Product)
def generate_slug(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)
