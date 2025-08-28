"""
Shipping Serializers
"""

from rest_framework import serializers
from .models import Shipment, ShippingRate, ShippingEvent, PickupRequest, ReturnRequest


class ShippingRateSerializer(serializers.ModelSerializer):
    """Serializer for shipping rates"""
    
    class Meta:
        model = ShippingRate
        fields = [
            'id', 'courier_name', 'courier_id', 'pickup_pincode',
            'delivery_pincode', 'weight', 'freight_charge', 'cod_charge',
            'other_charges', 'total_charge', 'delivery_days',
            'is_cod_available', 'is_prepaid_available'
        ]


class ShippingEventSerializer(serializers.ModelSerializer):
    """Serializer for shipping events"""
    
    class Meta:
        model = ShippingEvent
        fields = [
            'id', 'event_type', 'status', 'location', 'description',
            'event_time', 'source'
        ]


class PickupRequestSerializer(serializers.ModelSerializer):
    """Serializer for pickup requests"""
    
    class Meta:
        model = PickupRequest
        fields = [
            'id', 'pickup_date', 'pickup_time', 'status',
            'pickup_boy_name', 'pickup_boy_phone', 'comments'
        ]


class ReturnRequestSerializer(serializers.ModelSerializer):
    """Serializer for return requests"""
    
    class Meta:
        model = ReturnRequest
        fields = [
            'id', 'return_order_id', 'reason', 'reason_description',
            'status', 'return_awb', 'return_pickup_date',
            'refund_amount', 'is_refund_processed', 'refund_date',
            'created_at'
        ]


class ShipmentSerializer(serializers.ModelSerializer):
    """Serializer for shipment details"""
    
    events = ShippingEventSerializer(many=True, read_only=True)
    pickup_request = PickupRequestSerializer(read_only=True)
    return_requests = ReturnRequestSerializer(many=True, read_only=True)
    tracking_url = serializers.CharField(source='get_tracking_url', read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    is_delivered = serializers.BooleanField(read_only=True)
    is_in_transit = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'order_id', 'user', 'shiprocket_order_id', 'shiprocket_shipment_id',
            'awb_code', 'courier_company_id', 'courier_name', 'pickup_location',
            'pickup_address', 'pickup_pincode', 'customer_name', 'customer_email',
            'customer_phone', 'delivery_address', 'delivery_city', 'delivery_state',
            'delivery_pincode', 'delivery_country', 'weight', 'length', 'breadth',
            'height', 'cod_amount', 'shipping_charges', 'total_amount', 'payment_method',
            'status', 'current_location', 'estimated_delivery_date', 'actual_delivery_date',
            'items_data', 'created_at', 'updated_at', 'shipped_at', 'delivered_at',
            'tracking_url', 'can_cancel', 'is_delivered', 'is_in_transit',
            'events', 'pickup_request', 'return_requests'
        ]
        read_only_fields = [
            'id', 'shiprocket_order_id', 'shiprocket_shipment_id', 'awb_code',
            'courier_company_id', 'created_at', 'updated_at', 'shipped_at',
            'delivered_at'
        ]


class CreateShipmentSerializer(serializers.Serializer):
    """Serializer for creating shipments"""
    
    # Order Information
    order_id = serializers.CharField(max_length=100)
    order_date = serializers.DateTimeField(required=False)
    comment = serializers.CharField(max_length=500, required=False, default='E-commerce order')
    
    # Customer Information
    customer_name = serializers.CharField(max_length=200)
    customer_last_name = serializers.CharField(max_length=200, required=False, default='')
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=15)
    
    # Billing Address
    billing_address = serializers.CharField(max_length=500)
    billing_address_2 = serializers.CharField(max_length=500, required=False, default='')
    billing_city = serializers.CharField(max_length=100)
    billing_state = serializers.CharField(max_length=100)
    billing_pincode = serializers.CharField(max_length=10)
    billing_country = serializers.CharField(max_length=100, default='India')
    
    # Shipping Address (optional, defaults to billing)
    shipping_is_billing = serializers.BooleanField(default=True)
    shipping_customer_name = serializers.CharField(max_length=200, required=False)
    shipping_last_name = serializers.CharField(max_length=200, required=False, default='')
    shipping_address = serializers.CharField(max_length=500, required=False)
    shipping_address_2 = serializers.CharField(max_length=500, required=False, default='')
    shipping_city = serializers.CharField(max_length=100, required=False)
    shipping_state = serializers.CharField(max_length=100, required=False)
    shipping_pincode = serializers.CharField(max_length=10, required=False)
    shipping_country = serializers.CharField(max_length=100, required=False, default='India')
    shipping_email = serializers.EmailField(required=False)
    shipping_phone = serializers.CharField(max_length=15, required=False)
    
    # Package Details
    weight = serializers.DecimalField(max_digits=8, decimal_places=2)
    length = serializers.DecimalField(max_digits=8, decimal_places=2, default=10)
    breadth = serializers.DecimalField(max_digits=8, decimal_places=2, default=10)
    height = serializers.DecimalField(max_digits=8, decimal_places=2, default=5)
    
    # Financial Details
    sub_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_charges = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    cod_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = serializers.ChoiceField(choices=['Prepaid', 'COD'], default='Prepaid')
    
    # Items
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of order items with name, sku, quantity, price, etc."
    )
    
    def validate_items(self, value):
        """Validate items structure"""
        required_fields = ['name', 'quantity', 'price']
        for item in value:
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(f"Item missing required field: {field}")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # If shipping is not same as billing, shipping fields are required
        if not data.get('shipping_is_billing', True):
            shipping_required = [
                'shipping_customer_name', 'shipping_address', 'shipping_city',
                'shipping_state', 'shipping_pincode', 'shipping_email', 'shipping_phone'
            ]
            for field in shipping_required:
                if not data.get(field):
                    raise serializers.ValidationError(f"{field} is required when shipping address is different")
        
        # Validate COD amount for COD orders
        if data.get('payment_method') == 'COD' and data.get('cod_amount', 0) <= 0:
            raise serializers.ValidationError("COD amount must be greater than 0 for COD orders")
        
        return data


class TrackingSerializer(serializers.ModelSerializer):
    """Serializer for tracking information"""
    
    tracking_url = serializers.CharField(source='get_tracking_url', read_only=True)
    latest_event = serializers.SerializerMethodField()
    
    class Meta:
        model = Shipment
        fields = [
            'order_id', 'awb_code', 'courier_name', 'status',
            'current_location', 'estimated_delivery_date', 'actual_delivery_date',
            'created_at', 'shipped_at', 'delivered_at', 'tracking_url',
            'latest_event'
        ]
    
    def get_latest_event(self, obj):
        """Get the latest shipping event"""
        latest_event = obj.events.first()
        if latest_event:
            return {
                'status': latest_event.status,
                'location': latest_event.location,
                'description': latest_event.description,
                'event_time': latest_event.event_time
            }
        return None


class SimpleShipmentSerializer(serializers.ModelSerializer):
    """Simple serializer for shipment lists"""
    
    tracking_url = serializers.CharField(source='get_tracking_url', read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'order_id', 'awb_code', 'courier_name', 'status',
            'customer_name', 'delivery_city', 'delivery_pincode',
            'total_amount', 'payment_method', 'created_at',
            'estimated_delivery_date', 'tracking_url'
        ]


class BulkTrackingSerializer(serializers.Serializer):
    """Serializer for bulk tracking requests"""
    
    order_ids = serializers.ListField(
        child=serializers.CharField(max_length=100),
        max_length=50,
        help_text="List of order IDs to track (max 50)"
    )
    
    def validate_order_ids(self, value):
        """Validate order IDs"""
        if len(value) > 50:
            raise serializers.ValidationError("Maximum 50 order IDs allowed")
        return value