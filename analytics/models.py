# analytics/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from products.models import Product, ProductCategory
from orders.models import Order
from decimal import Decimal
import uuid

User = get_user_model()

class AnalyticsEvent(models.Model):
    EVENT_TYPES = (
        ('page_view', 'Page View'),
        ('product_view', 'Product View'),
        ('category_view', 'Category View'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('checkout_start', 'Checkout Started'),
        ('checkout_complete', 'Checkout Completed'),
        ('search', 'Search'),
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('account_created', 'Account Created'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    path = models.CharField(max_length=255)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['session_key']),
        ]
        verbose_name = "Analytics Event"
        verbose_name_plural = "Analytics Events"

    def __str__(self):
        return f"{self.get_event_type_display()} at {self.created_at}"


class ProductView(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='analytics_views'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Product View"
        verbose_name_plural = "Product Views"

    def __str__(self):
        return f"View of {self.product.name}"


class SalesReport(models.Model):
    REPORT_PERIODS = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    )

    period_type = models.CharField(max_length=10, choices=REPORT_PERIODS)
    start_date = models.DateField()
    end_date = models.DateField()
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_products_sold = models.PositiveIntegerField(default=0)
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = ('period_type', 'start_date', 'end_date')
        verbose_name = "Sales Report"
        verbose_name_plural = "Sales Reports"

    def __str__(self):
        return f"{self.get_period_type_display()} Report ({self.start_date} to {self.end_date})"

    def calculate_metrics(self):
        """Calculate all metrics for the report period"""
        orders = Order.objects.filter(
            created_at__date__gte=self.start_date,
            created_at__date__lte=self.end_date,
            payment_status='paid'
        )

        # Basic counts
        self.total_orders = orders.count()
        self.total_revenue = orders.aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

        # Products sold
        self.total_products_sold = orders.aggregate(
            total=Sum('items__quantity')
        )['total'] or 0

        # Customer metrics
        customer_counts = orders.values('user').annotate(
            order_count=Count('id')
        ).order_by()

        self.new_customers = customer_counts.filter(order_count=1).count()
        self.returning_customers = customer_counts.filter(order_count__gt=1).count()

        # Average order value
        self.average_order_value = self.total_revenue / self.total_orders if self.total_orders else Decimal('0.00')

        # Additional data
        self.data = {
            'top_products': self._get_top_products(orders),
            'top_categories': self._get_top_categories(orders),
            'sales_by_day': self._get_sales_by_day(orders),
            'payment_methods': self._get_payment_methods(orders),
        }

    def _get_top_products(self, orders):
        """Get top 5 selling products"""
        return list(
            orders.values('items__product__name')
            .annotate(
                total_sold=Sum('items__quantity'),
                total_revenue=Sum(F('items__price') * F('items__quantity'))
            )
            .order_by('-total_sold')[:5]
        )

    def _get_top_categories(self, orders):
        """Get top 5 selling categories"""
        return list(
            orders.values('items__product__category__name')
            .annotate(
                total_sold=Sum('items__quantity'),
                total_revenue=Sum(F('items__price') * F('items__quantity'))
            )
            .order_by('-total_sold')[:5]
        )

    def _get_sales_by_day(self, orders):
        """Get sales breakdown by day"""
        return list(
            orders.annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(
                total_orders=Count('id'),
                total_revenue=Sum('total')
            )
            .order_by('date')
        )

    def _get_payment_methods(self, orders):
        """Get payment method distribution"""
        return list(
            orders.values('payment_method')
            .annotate(
                count=Count('id'),
                percentage=Count('id') * 100.0 / self.total_orders
            )
            .order_by('-count')
        )


class UserActivity(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    last_login = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    total_logins = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    favorite_categories = models.ManyToManyField(
        ProductCategory,
        blank=True
    )
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"

    def __str__(self):
        return f"Activity for {self.user.email}"

    def update_activity(self):
        """Update activity metrics for the user"""
        self.total_logins = AnalyticsEvent.objects.filter(
            user=self.user,
            event_type='login'
        ).count()

        orders = Order.objects.filter(user=self.user, payment_status='paid')
        self.total_orders = orders.count()
        self.total_spent = orders.aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

        # Update favorite categories
        favorite_categories = ProductCategory.objects.filter(
            products__order_items__order__user=self.user
        ).annotate(
            order_count=Count('products__order_items')
        ).order_by('-order_count')[:3]

        self.favorite_categories.set(favorite_categories)

        # Update additional data
        self.data = {
            'last_orders': self._get_last_orders(),
            'activity_timeline': self._get_activity_timeline(),
        }

    def _get_last_orders(self):
        """Get last 5 orders"""
        return list(
            Order.objects.filter(user=self.user)
            .order_by('-created_at')[:5]
            .values('order_number', 'created_at', 'total', 'status')
        )

    def _get_activity_timeline(self):
        """Get recent user activity"""
        return list(
            AnalyticsEvent.objects.filter(user=self.user)
            .order_by('-created_at')[:20]
            .values('event_type', 'created_at', 'path')
        )


class InventoryAlert(models.Model):
    ALERT_TYPES = (
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('expiring_soon', 'Expiring Soon'),
        ('slow_moving', 'Slow Moving'),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_alerts'
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    current_quantity = models.PositiveIntegerField()
    threshold = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Inventory Alert"
        verbose_name_plural = "Inventory Alerts"

    def __str__(self):
        return f"{self.get_alert_type_display()} Alert for {self.product.name}"

    def resolve(self, user=None):
        """Mark alert as resolved"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()