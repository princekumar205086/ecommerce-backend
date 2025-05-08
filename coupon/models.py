# coupons/models.py
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import User
from django.utils.timezone import now, timedelta


def default_valid_to():
    return now() + timedelta(days=30)


class Coupon(models.Model):
    COUPON_TYPES = (
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
    )

    APPLICABLE_TO = (
        ('all', 'All Products'),
        ('pathology', 'Pathology Products Only'),
        ('doctor', 'Doctor Products Only'),
        ('medical', 'Medical Products Only'),
    )

    # Core Coupon Fields
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique coupon code for customers to enter"
    )
    description = models.TextField(
        blank=True,
        help_text="Internal description of the coupon"
    )

    # Discount Configuration
    coupon_type = models.CharField(
        max_length=20,
        choices=COUPON_TYPES,
        default='percentage'
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Percentage or fixed amount based on coupon_type",
        default=10.00
    )
    max_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum discount amount (for percentage coupons)"
    )
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Minimum cart value required to apply this coupon"
    )

    # Applicability
    applicable_to = models.CharField(
        max_length=20,
        choices=APPLICABLE_TO,
        default='all',
        help_text="Which product types this coupon applies to"
    )

    # Validity Period
    valid_from = models.DateTimeField(
        default=timezone.now,
        help_text="When the coupon becomes active"
    )
    valid_to = models.DateTimeField(
        help_text="When the coupon expires",
        default=default_valid_to
    )

    # Usage Tracking
    max_uses = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of times this coupon can be used"
    )
    used_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="How many times this coupon has been used"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this coupon is currently active"
    )

    # User Assignment
    assigned_to_all = models.BooleanField(
        default=True,
        help_text="If True, coupon is available to all users"
    )
    assigned_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='assigned_coupons',
        help_text="Specific users this coupon is assigned to (if not assigned_to_all)"
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        editable=False
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,  # Changed from CASCADE for data protection
        related_name='created_coupons',
        null=True,  # Temporary for migration
        blank=True,  # Temporary for migration
        editable=False
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['valid_from', 'valid_to']),
            models.Index(fields=['is_active']),
            models.Index(fields=['coupon_type']),
        ]
        permissions = [
            ('can_generate_coupons', 'Can generate coupon codes'),
        ]

    def __str__(self):
        return f"{self.code} ({self.get_coupon_type_display()} off)"

    def clean(self):
        """Additional model validation"""
        errors = {}

        if self.valid_to <= self.valid_from:
            errors['valid_to'] = "Valid to date must be after valid from date"

        if self.coupon_type == 'percentage' and self.discount_value > 100:
            errors['discount_value'] = "Percentage discount cannot exceed 100%"

        if self.max_discount and self.coupon_type == 'fixed_amount':
            errors['max_discount'] = "Max discount only applicable to percentage coupons"

        if errors:
            raise ValidationError(errors)

    def is_valid(self, user=None, cart_total=0):
        """
        Comprehensive coupon validation check
        Returns: (is_valid: bool, message: str)
        """
        now = timezone.now()
        validation_checks = [
            (self.is_active, "Coupon is not active"),
            (now >= self.valid_from, "Coupon not yet valid"),
            (now <= self.valid_to, "Coupon has expired"),
            (self.used_count < self.max_uses, "Coupon usage limit reached"),
            (cart_total >= self.min_order_amount,
             f"Minimum order amount not met (₹{self.min_order_amount} required)"),
            (self.assigned_to_all or (user and self.assigned_users.filter(pk=user.pk).exists()),
             "Coupon not assigned to this user"),
        ]

        for condition, message in validation_checks:
            if not condition:
                return False, message
        return True, "Valid coupon"

    def apply_discount(self, amount):
        """
        Calculate discount amount safely
        Args:
            amount: Decimal - the amount to apply discount to
        Returns:
            Decimal - the discount amount
        """
        if self.coupon_type == 'percentage':
            discount = (amount * Decimal(self.discount_value) / Decimal('100')).quantize(Decimal('0.00'))
            if self.max_discount:
                return min(discount, self.max_discount)
            return discount
        return min(Decimal(self.discount_value), amount).quantize(Decimal('0.00'))

    def record_usage(self, user, order_id=None, discount_amount=0):
        """
        Record coupon usage in a transaction-safe way
        """
        from django.db import transaction

        with transaction.atomic():
            self.refresh_from_db()
            if self.used_count >= self.max_uses:
                raise ValidationError("Coupon usage limit reached")

            CouponUsage.objects.create(
                coupon=self,
                user=user,
                order_id=order_id,
                discount_amount=discount_amount
            )
            self.used_count = models.F('used_count') + 1
            self.save()


class CouponUsage(models.Model):
    """Tracks each instance of coupon usage"""
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='coupon_usages'
    )
    order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    applied_at = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )

    class Meta:
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"
        unique_together = ('coupon', 'order_id')
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['user', 'applied_at']),
        ]

    def __str__(self):
        self.date_ = f"{self.user.email} used {self.coupon.code} on {self.applied_at.date()}"
        return self.date_
