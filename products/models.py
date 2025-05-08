from decimal import Decimal

from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.conf import settings

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
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_publish = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'slug': self.slug})


class ProductSubCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_publish = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        verbose_name_plural = "Product Subcategories"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category.name} > {self.name}"

    def get_absolute_url(self):
        return reverse('subcategory-detail', kwargs={'slug': self.slug})


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')  # Explicit Decimal default
    )
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True,
        default='products/default.png'
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.CASCADE,
        related_name='products'
    )
    subcategory = models.ForeignKey(
        ProductSubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default='medical'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='products'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_publish = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'category'],
                name='unique_product_name_per_category'
            )
        ]
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'is_publish']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product-detail', kwargs={'slug': self.slug})

    def is_in_stock(self):
        return self.stock > 0

    def clean(self):
        if self.subcategory and self.subcategory.category != self.category:
            raise ValidationError(
                "Subcategory must belong to the selected category"
            )


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    size = models.CharField(max_length=50, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    additional_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'size', 'weight'],
                name='unique_product_variant'
            )
        ]
        ordering = ['-additional_price']

    def __str__(self):
        return f"{self.product.name} - {self.size or ''} {self.weight or ''}".strip()

    def clean(self):
        if not self.size and not self.weight:
            raise ValidationError("Either size or weight must be provided")

        if self.stock < 0:
            raise ValidationError("Stock cannot be negative")

    @property
    def total_price(self):
        return float(self.product.price) + float(self.additional_price)

    def is_in_stock(self):
        return self.stock > 0


class ProductReview(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_reviews"
    )
    rating = models.IntegerField(
        choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='unique_user_review_per_product'
            )
        ]
        ordering = ['-created_at']
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        return f"{self.get_rating_display()} by {self.user.email} for {self.product.name}"

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError("Rating must be between 1 and 5")

    def save(self, *args, **kwargs):
        self.full_clean()
        # Auto-publish positive reviews
        self.is_published = self.rating >= 4
        super().save(*args, **kwargs)


@receiver(pre_save, sender=ProductCategory)
@receiver(pre_save, sender=ProductSubCategory)
@receiver(pre_save, sender=Product)
def generate_slug(sender, instance, *args, **kwargs):
    if not instance.slug:
        base_slug = slugify(instance.name)
        instance.slug = base_slug
        counter = 1
        while sender.objects.filter(slug=instance.slug).exists():
            instance.slug = f"{base_slug}-{counter}"
            counter += 1
