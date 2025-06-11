from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from taggit.managers import TaggableManager

# Constants
PRODUCT_STATUSES = (
    ('pending', 'Pending'),
    ('reviewed', 'Reviewed'),
    ('rejected', 'Rejected'),
    ('published', 'Published'),
)

PRODUCT_TYPES = (
    ('medicine', 'Medicine'),
    ('equipment', 'Doctor Equipment'),
    ('pathology', 'Pathology Product'),
)

RATING_CHOICES = [(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)]


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_publish = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=PRODUCT_STATUSES, default='pending')

    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', default='products/default.png', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_publish = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=PRODUCT_STATUSES, default='pending')

    # Key Field
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='medicine')

    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    stock = models.PositiveIntegerField(default=0)

    # --- Fields for Medicines ---
    composition = models.CharField(max_length=255, blank=True)
    quantity = models.CharField(max_length=50, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    expiry_date = models.DateField(blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True)
    prescription_required = models.BooleanField(default=False)
    form = models.CharField(max_length=50, blank=True)
    pack_size = models.CharField(max_length=50, blank=True)

    # --- Fields for Doctor Equipment ---
    model_number = models.CharField(max_length=100, blank=True)
    warranty_period = models.CharField(max_length=50, blank=True)
    usage_type = models.CharField(max_length=100, blank=True)
    technical_specifications = models.TextField(blank=True)
    power_requirement = models.CharField(max_length=100, blank=True)
    equipment_type = models.CharField(max_length=100, blank=True)

    # --- Fields for Pathology Products ---
    compatible_tests = models.TextField(blank=True)
    chemical_composition = models.TextField(blank=True)
    storage_condition = models.TextField(blank=True)

    # Common
    specifications = models.JSONField(default=dict, blank=True)
    tags = TaggableManager(blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = (
            'name', 'composition', 'quantity', 'category', 'form', 'pack_size'
        )
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'is_publish']),
        ]

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class SupplierProductPrice(models.Model):
    supplier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supplier_prices')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='supplier_prices')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pincode = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    district = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('supplier', 'product', 'pincode', 'district')
        indexes = [
            models.Index(fields=['product', 'pincode']),
            models.Index(fields=['product', 'district']),
        ]


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'size', 'weight')
        ordering = ['-additional_price']

    def __str__(self):
        return f"{self.product.name} - {self.size or ''} {self.weight or ''}".strip()

    @property
    def total_price(self):
        return self.product.price + self.additional_price


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        return f"{self.get_rating_display()} by {self.user} for {self.product.name}"

    def save(self, *args, **kwargs):
        self.is_published = self.rating >= 3
        super().save(*args, **kwargs)


class ProductAuditLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='audit_logs')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = "Product Audit Log"
        verbose_name_plural = "Product Audit Logs"

    def __str__(self):
        return f"{self.product.name} - {self.field_name} changed"


# Slug Generator
@receiver(pre_save, sender=ProductCategory)
@receiver(pre_save, sender=Product)
def generate_slug(sender, instance, **kwargs):
    if not instance.slug:
        base_slug = slugify(instance.name or "")
        if not base_slug:
            base_slug = f"{sender.__name__.lower()}-{instance.pk or ''}"
        slug = base_slug
        counter = 1
        while sender.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        instance.slug = slug


# Track field changes
@receiver(pre_save, sender=Product)
def track_product_changes(sender, instance, **kwargs):
    if not instance.pk:
        return  # Skip new instances
    try:
        old = Product.objects.get(pk=instance.pk)
    except Product.DoesNotExist:
        return

    tracked_fields = ['price', 'stock', 'status']
    for field in tracked_fields:
        old_val = getattr(old, field)
        new_val = getattr(instance, field)
        if old_val != new_val:
            ProductAuditLog.objects.create(
                product=instance,
                changed_by=getattr(instance, '_changed_by', None),
                field_name=field,
                old_value=str(old_val),
                new_value=str(new_val)
            )
