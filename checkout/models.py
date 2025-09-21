from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from accounts.models import User


class Address(models.Model):
    """Address model for shipping and billing"""
    ADDRESS_TYPES = (
        ('home', 'Home'),
        ('office', 'Office'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='home')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='India')
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state}"

    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            Address.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class CheckoutSession(models.Model):
    """Temporary checkout session to store checkout process data"""
    SESSION_STATUS = (
        ('initiated', 'Initiated'),
        ('address_selected', 'Address Selected'),
        ('payment_method_selected', 'Payment Method Selected'),
        ('order_created', 'Order Created'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_METHODS = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('net_banking', 'Net Banking'),
        ('upi', 'UPI'),
        ('cod', 'Cash on Delivery'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='checkout_sessions'
    )
    session_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=30, choices=SESSION_STATUS, default='initiated')
    
    # Cart snapshot
    cart_items_snapshot = models.JSONField(default=dict)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Address information
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipping_checkouts'
    )
    billing_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='billing_checkouts'
    )
    
    # Payment information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, null=True, blank=True)
    
    # Pricing breakdown
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Applied coupon
    coupon_code = models.CharField(max_length=50, null=True, blank=True)
    
    # Order reference (once created)
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkout_session'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "Checkout Session"
        verbose_name_plural = "Checkout Sessions"
        ordering = ['-created_at']

    def __str__(self):
        return f"Checkout {self.session_id} - {self.user.email} ({self.status})"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def calculate_totals(self):
        """Calculate all pricing components"""
        # Calculate tax (18% GST)
        self.tax_amount = self.subtotal * Decimal('0.18')
        
        # Calculate shipping (free for orders > 500)
        self.shipping_charge = Decimal('50.00') if self.subtotal < Decimal('500.00') else Decimal('0.00')
        
        # Calculate total
        self.total_amount = (
            self.subtotal + 
            self.shipping_charge + 
            self.tax_amount - 
            self.discount_amount - 
            self.coupon_discount
        )

    def save(self, *args, **kwargs):
        if not self.expires_at:
            from django.utils import timezone
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(hours=2)  # 2 hour expiry
        
        self.calculate_totals()
        super().save(*args, **kwargs)
