from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models import Sum, F, DecimalField
from django.db import transaction
from decimal import Decimal
from django.core.exceptions import ValidationError
from accounts.models import User
from products.models import Product, ProductVariant
from coupon.models import Coupon


class Order(models.Model):
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )

    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
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
        on_delete=models.PROTECT,
        related_name='orders'
    )
    order_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS,
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        null=True,
        blank=True
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    shipping_charge = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    coupon_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipping_address = models.JSONField()
    billing_address = models.JSONField()
    notes = models.TextField(blank=True)
    
    # New fields for admin management
    shipping_partner = models.CharField(max_length=100, blank=True, null=True)
    tracking_id = models.CharField(max_length=100, blank=True, null=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        timestamp = timezone.now().strftime('%Y%m%d')
        last_order = Order.objects.filter(
            order_number__startswith=timestamp
        ).order_by('order_number').last()

        if last_order:
            seq = int(last_order.order_number[-4:]) + 1
        else:
            seq = 1

        return f"{timestamp}{seq:04d}"

    def calculate_totals(self):
        """Calculate all financial fields with proper rounding"""
        with transaction.atomic():
            items = self.items.select_related('product', 'variant').all()

            # Calculate subtotal
            self.subtotal = sum(
                item.total_price for item in items
            ).quantize(Decimal('0.00'))

            # Calculate tax (10% for example)
            self.tax = (self.subtotal * Decimal('0.10')).quantize(Decimal('0.00'))

            # Apply coupon if valid
            self.coupon_discount = Decimal('0.00')
            if self.coupon:
                is_valid, _ = self.coupon.is_valid(self.user, self.subtotal)
                if is_valid:
                    self.coupon_discount = self.coupon.apply_discount(
                        self.subtotal
                    ).quantize(Decimal('0.00'))

            # Convert float fields to Decimal
            shipping_charge = Decimal(self.shipping_charge).quantize(Decimal('0.00'))
            discount = Decimal(self.discount).quantize(Decimal('0.00'))

            # Calculate final total
            self.total = (
                    self.subtotal +
                    self.tax +
                    shipping_charge -
                    discount -
                    self.coupon_discount
            ).quantize(Decimal('0.00'))

    @staticmethod
    def create_from_cart(cart, shipping_address, billing_address, payment_method=None):
        """
        Create an order from a cart with stock validation
        Returns: Order object
        Raises: ValidationError if stock is insufficient
        """
        with transaction.atomic():
            # Lock cart items for processing
            cart_items = cart.items.select_related(
                'product', 'variant'
            ).select_for_update()

            # Validate stock before creating order
            for item in cart_items:
                available_stock = item.variant.stock if item.variant else item.product.stock
                if item.quantity > available_stock:
                    raise ValidationError(
                        f"Not enough stock for {item.product.name}. "
                        f"Available: {available_stock}, Requested: {item.quantity}"
                    )

            # Create order
            order = Order.objects.create(
                user=cart.user,
                shipping_address=shipping_address,
                billing_address=billing_address,
                payment_method=payment_method
            )

            # Create order items and update stock
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,
                    quantity=cart_item.quantity,
                    price=cart_item.variant.total_price if cart_item.variant else cart_item.product.price
                )

                # Update stock
                if cart_item.variant:
                    cart_item.variant.stock -= cart_item.quantity
                    cart_item.variant.save()
                else:
                    cart_item.product.stock -= cart_item.quantity
                    cart_item.product.save()

            # Clear cart
            cart.clear()

            # Calculate totals
            order.calculate_totals()
            order.save()

            return order

    def can_cancel(self):
        return self.status in ['pending', 'processing']

    def get_status_history(self):
        return self.status_changes.order_by('-created_at')

    def accept_order(self):
        """Accept order (admin only)"""
        if self.status == 'pending':
            self.status = 'processing'
            self.save()
            # Create status change record
            OrderStatusChange.objects.create(
                order=self,
                status='processing',
                changed_by=None,  # Will be set by the view
                notes='Order accepted by admin'
            )
            return True
        return False

    def reject_order(self, reason=""):
        """Reject order (admin only)"""
        if self.status in ['pending', 'processing']:
            self.status = 'cancelled'
            self.save()
            # Create status change record
            OrderStatusChange.objects.create(
                order=self,
                status='cancelled',
                changed_by=None,  # Will be set by the view
                notes=f'Order rejected by admin. Reason: {reason}'
            )
            return True
        return False

    def assign_shipping(self, shipping_partner, tracking_id=""):
        """Assign shipping partner and tracking (admin only)"""
        if self.status == 'processing':
            self.status = 'shipped'
            self.shipping_partner = shipping_partner
            self.tracking_id = tracking_id
            self.save()
            # Create status change record
            OrderStatusChange.objects.create(
                order=self,
                status='shipped',
                changed_by=None,  # Will be set by the view
                notes=f'Order shipped via {shipping_partner}. Tracking: {tracking_id}'
            )
            return True
        return False

    def mark_delivered(self):
        """Mark order as delivered (admin only)"""
        if self.status == 'shipped':
            self.status = 'delivered'
            self.delivered_at = timezone.now()
            self.payment_status = 'paid'
            self.save()
            # Create status change record
            OrderStatusChange.objects.create(
                order=self,
                status='delivered',
                changed_by=None,  # Will be set by the view
                notes='Order marked as delivered'
            )
            return True
        return False


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.order_number})"

    def clean(self):
        if self.variant and self.variant.product != self.product:
            raise ValidationError("Variant does not belong to selected product")

        # Check stock availability when creating new items
        if not self.pk:
            available_stock = self.variant.stock if self.variant else self.product.stock
            if self.quantity > available_stock:
                raise ValidationError(
                    f"Only {available_stock} items available in stock"
                )

    @property
    def total_price(self):
        return (self.price * self.quantity).quantize(Decimal('0.00'))


class OrderStatusChange(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_changes'
    )
    status = models.CharField(
        max_length=20,
        choices=Order.ORDER_STATUS
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order Status Change"
        verbose_name_plural = "Order Status Changes"

    def __str__(self):
        return f"Order #{self.order.order_number} changed to {self.status}"
