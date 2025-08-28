"""
Shipping Models for ShipRocket Integration
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json

User = get_user_model()

class ShippingProvider(models.Model):
    """Shipping provider configuration"""
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    api_config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class ShippingRate(models.Model):
    """Store shipping rates for different zones"""
    provider = models.ForeignKey(ShippingProvider, on_delete=models.CASCADE)
    courier_name = models.CharField(max_length=100)
    courier_id = models.CharField(max_length=50)
    pickup_pincode = models.CharField(max_length=10)
    delivery_pincode = models.CharField(max_length=10)
    weight = models.DecimalField(max_digits=8, decimal_places=2)  # in kg
    freight_charge = models.DecimalField(max_digits=10, decimal_places=2)
    cod_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    total_charge = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_days = models.CharField(max_length=50, blank=True)
    is_cod_available = models.BooleanField(default=False)
    is_prepaid_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['courier_id', 'pickup_pincode', 'delivery_pincode', 'weight']
    
    def __str__(self):
        return f"{self.courier_name} - {self.pickup_pincode} to {self.delivery_pincode}"

class Shipment(models.Model):
    """Shipment tracking and management"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('pickup_generated', 'Pickup Generated'),
        ('manifested', 'Manifested'),
        ('dispatched', 'Dispatched'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]
    
    # Basic Information
    order_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipments')
    
    # ShipRocket Data
    shiprocket_order_id = models.CharField(max_length=100, blank=True, null=True)
    shiprocket_shipment_id = models.CharField(max_length=100, blank=True, null=True)
    awb_code = models.CharField(max_length=100, blank=True, null=True)
    courier_company_id = models.CharField(max_length=50, blank=True, null=True)
    courier_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Shipping Details
    pickup_location = models.CharField(max_length=100, default='Primary')
    pickup_address = models.TextField()
    pickup_pincode = models.CharField(max_length=10)
    
    # Customer Details
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    
    # Delivery Address
    delivery_address = models.TextField()
    delivery_city = models.CharField(max_length=100)
    delivery_state = models.CharField(max_length=100)
    delivery_pincode = models.CharField(max_length=10)
    delivery_country = models.CharField(max_length=100, default='India')
    
    # Package Details
    weight = models.DecimalField(max_digits=8, decimal_places=2)  # in kg
    length = models.DecimalField(max_digits=8, decimal_places=2)  # in cm
    breadth = models.DecimalField(max_digits=8, decimal_places=2)  # in cm
    height = models.DecimalField(max_digits=8, decimal_places=2)  # in cm
    
    # Financial Details
    cod_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='Prepaid')
    
    # Status and Tracking
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    current_location = models.CharField(max_length=200, blank=True, null=True)
    estimated_delivery_date = models.DateTimeField(blank=True, null=True)
    actual_delivery_date = models.DateTimeField(blank=True, null=True)
    
    # Additional Data
    items_data = models.JSONField(default=list)  # Store order items
    tracking_data = models.JSONField(default=dict)  # Store tracking updates
    shiprocket_response = models.JSONField(default=dict)  # Store API responses
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['awb_code']),
            models.Index(fields=['status']),
            models.Index(fields=['delivery_pincode']),
        ]
    
    def __str__(self):
        return f"Shipment {self.order_id} - {self.status}"
    
    def is_delivered(self):
        return self.status == 'delivered'
    
    def is_in_transit(self):
        return self.status in ['dispatched', 'in_transit', 'out_for_delivery']
    
    def can_cancel(self):
        return self.status in ['pending', 'confirmed', 'pickup_generated']
    
    def get_tracking_url(self):
        if self.awb_code:
            return f"https://shiprocket.co/tracking/{self.awb_code}"
        return None

class ShippingEvent(models.Model):
    """Track shipping events and status updates"""
    
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    location = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField()
    event_time = models.DateTimeField()
    source = models.CharField(max_length=50, default='shiprocket')  # shiprocket, webhook, manual
    raw_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-event_time']
        indexes = [
            models.Index(fields=['shipment', 'event_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.shipment.order_id} - {self.status} at {self.event_time}"

class PickupRequest(models.Model):
    """Track pickup requests"""
    
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('scheduled', 'Scheduled'),
        ('picked_up', 'Picked Up'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name='pickup_request')
    pickup_date = models.DateField()
    pickup_time = models.CharField(max_length=50)  # e.g., "10:00-14:00"
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='requested')
    pickup_boy_name = models.CharField(max_length=100, blank=True, null=True)
    pickup_boy_phone = models.CharField(max_length=15, blank=True, null=True)
    comments = models.TextField(blank=True)
    shiprocket_pickup_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Pickup for {self.shipment.order_id} on {self.pickup_date}"

class ReturnRequest(models.Model):
    """Handle return requests"""
    
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pickup_scheduled', 'Pickup Scheduled'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('delivered_to_origin', 'Delivered to Origin'),
        ('cancelled', 'Cancelled'),
    ]
    
    REASON_CHOICES = [
        ('defective', 'Defective Product'),
        ('wrong_item', 'Wrong Item Delivered'),
        ('size_issue', 'Size Issue'),
        ('quality_issue', 'Quality Issue'),
        ('not_needed', 'No Longer Needed'),
        ('damaged', 'Damaged in Transit'),
        ('other', 'Other'),
    ]
    
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='return_requests')
    return_order_id = models.CharField(max_length=100, unique=True)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    reason_description = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='initiated')
    
    # Return Details
    return_awb = models.CharField(max_length=100, blank=True, null=True)
    return_pickup_date = models.DateField(blank=True, null=True)
    return_tracking_data = models.JSONField(default=dict)
    
    # Financial
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    is_refund_processed = models.BooleanField(default=False)
    refund_date = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Return {self.return_order_id} for {self.shipment.order_id}"