import uuid
from decimal import Decimal
from typing import Dict

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from taggit.managers import TaggableManager

# ---------- Constants ----------
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


# ---------- Catalog / Core Models ----------

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.URLField(default='', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.URLField(default='', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_publish = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=PRODUCT_STATUSES, default='pending')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Lean core product model. Type-specific fields moved to detail models.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)  # primary base sku for product
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    description = models.TextField(blank=True)
    image = models.URLField(default='', blank=True, null=True)  # product default image
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_publish = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=PRODUCT_STATUSES, default='pending')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='medicine')

    # base price and stock (used if no variant selected)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    stock = models.PositiveIntegerField(default=0)

    # generic JSON specifications
    specifications = models.JSONField(default=dict, blank=True)
    tags = TaggableManager(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'is_publish']),
            models.Index(fields=['product_type']),
        ]

    def __str__(self):
        return self.name

    def get_effective_price(self, variant=None):
        if variant:
            if variant.price and variant.price != Decimal('0.00'):
                return variant.price
            return (self.price or Decimal('0.00')) + (variant.additional_price or Decimal('0.00'))
        return self.price


# ---------- Product Type Detail Models ----------

class MedicineDetails(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="medicine_details")
    composition = models.CharField(max_length=255, blank=True)
    quantity = models.CharField(max_length=50, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    expiry_date = models.DateField(blank=True, null=True)
    batch_number = models.CharField(max_length=100)  # ✅ Mandatory now
    prescription_required = models.BooleanField(default=False)
    form = models.CharField(max_length=50, blank=True)
    pack_size = models.CharField(max_length=50, blank=True)


class EquipmentDetails(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="equipment_details")
    model_number = models.CharField(max_length=100, blank=True)
    warranty_period = models.CharField(max_length=50, blank=True)
    usage_type = models.CharField(max_length=100, blank=True)
    technical_specifications = models.TextField(blank=True)
    power_requirement = models.CharField(max_length=100, blank=True)
    equipment_type = models.CharField(max_length=100, blank=True)


class PathologyDetails(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="pathology_details")
    compatible_tests = models.TextField(blank=True)
    chemical_composition = models.TextField(blank=True)
    storage_condition = models.TextField(blank=True)


# ---------- Attribute / Variant System ----------

class ProductAttribute(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey(ProductAttribute, related_name="values", on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = ('attribute', 'value')

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    attributes = models.ManyToManyField(ProductAttributeValue, related_name='variants', blank=True)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    additional_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['product', 'is_active']),
        ]

    def __str__(self):
        attr_vals = ", ".join([str(v) for v in self.attributes.all()])
        return f"{self.product.name} - {attr_vals}" if attr_vals else f"{self.product.name} - default"

    @property
    def total_price(self):
        if self.price and self.price != Decimal('0.00'):
            return self.price
        return (self.product.price or Decimal('0.00')) + (self.additional_price or Decimal('0.00'))


# ---------- Images ----------

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images', blank=True, null=True)
    image = models.URLField()
    alt_text = models.CharField(max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        if self.variant:
            return f"Image for {self.product.name} ({self.variant.sku or self.variant.id})"
        return f"Image for {self.product.name}"


# ---------- Supplier Pricing ----------

class SupplierProductPrice(models.Model):
    supplier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supplier_prices')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='supplier_prices')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    pincode = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    district = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('supplier', 'product_variant', 'pincode', 'district')


# ---------- Reviews ----------

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

    def __str__(self):
        return f"{self.get_rating_display()} by {self.user} for {self.product.name}"

    def save(self, *args, **kwargs):
        self.is_published = self.rating >= 3
        super().save(*args, **kwargs)


# ---------- Audit Log ----------

class ProductAuditLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='audit_logs')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changes = models.JSONField(default=dict)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} changes at {self.changed_at}"


# ---------- Signals ----------

def _unique_slugify(instance, value, queryset, slug_field='slug'):
    base_slug = slugify(value)[:50] or str(uuid.uuid4())[:8]
    slug = base_slug
    counter = 1
    lookup = {slug_field: slug}
    while queryset.filter(**lookup).exclude(pk=getattr(instance, 'pk', None)).exists():
        slug = f"{base_slug}-{counter}"
        lookup[slug_field] = slug
        counter += 1
    return slug


@receiver(pre_save, sender=ProductCategory)
@receiver(pre_save, sender=Product)
def generate_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = _unique_slugify(instance, getattr(instance, 'name', ''), sender.objects)


@receiver(pre_save, sender=Product)
def generate_product_sku(sender, instance, **kwargs):
    if not instance.sku:
        base_sku = slugify(instance.name)[:20].upper() or "PRD"
        unique_suffix = str(uuid.uuid4())[:8].upper()
        sku_candidate = f"{base_sku}-{unique_suffix}"
        counter = 1
        while sender.objects.filter(sku=sku_candidate).exclude(pk=instance.pk).exists():
            sku_candidate = f"{base_sku}-{unique_suffix}-{counter}"
            counter += 1
        instance.sku = sku_candidate


@receiver(pre_save, sender=ProductVariant)
def generate_variant_sku(sender, instance, **kwargs):
    if not instance.sku:
        base = (instance.product.sku or slugify(instance.product.name)[:10].upper() or "PRD").upper()
        suffix = str(uuid.uuid4())[:8].upper()
        sku_candidate = f"{base}-{suffix}"
        counter = 1
        while sender.objects.filter(sku=sku_candidate).exclude(pk=instance.pk).exists():
            sku_candidate = f"{base}-{suffix}-{counter}"
            counter += 1
        instance.sku = sku_candidate


@receiver(pre_save, sender=Product)
def track_product_changes(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    tracked_fields = [
        'price', 'stock', 'status', 'is_publish', 'name', 'category', 'brand', 'product_type'
    ]

    diffs: Dict[str, list] = {}
    for field in tracked_fields:
        old_val = getattr(old, field)
        new_val = getattr(instance, field)
        if isinstance(old_val, models.Model):
            old_val_repr = getattr(old_val, 'pk', str(old_val))
        else:
            old_val_repr = old_val
        if isinstance(new_val, models.Model):
            new_val_repr = getattr(new_val, 'pk', str(new_val))
        else:
            new_val_repr = new_val

        if old_val_repr != new_val_repr:
            diffs[field] = [str(old_val_repr), str(new_val_repr)]

    if diffs:
        ProductAuditLog.objects.create(
            product=instance,
            changed_by=getattr(instance, '_changed_by', None),
            changes=diffs
        )
