# inventory/offline_serializers.py
"""
Serializers for offline sales management
"""

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from products.models import Product, ProductVariant
from .models import Warehouse
from .offline_sales import OfflineSale, OfflineSaleItem, OfflineSaleManager


class OfflineSaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_details = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OfflineSaleItem
        fields = [
            'id', 'product', 'product_name', 'variant', 'variant_details',
            'quantity', 'unit_price', 'discount_per_item', 'total_price',
            'batch_number', 'expiry_date'
        ]

    def get_variant_details(self, obj):
        if obj.variant:
            return {
                'size': obj.variant.size,
                'weight': obj.variant.weight,
                'additional_price': str(obj.variant.additional_price)
            }
        return None


class OfflineSaleSerializer(serializers.ModelSerializer):
    items = OfflineSaleItemSerializer(many=True, read_only=True)
    vendor_name = serializers.CharField(source='vendor.full_name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = OfflineSale
        fields = [
            'id', 'sale_number', 'vendor', 'vendor_name', 'warehouse', 'warehouse_name',
            'customer_name', 'customer_phone', 'customer_email',
            'subtotal', 'tax_amount', 'discount_amount', 'total_amount',
            'payment_method', 'payment_reference', 'notes',
            'sale_date', 'created_at', 'is_cancelled', 'cancelled_reason',
            'items'
        ]
        read_only_fields = [
            'sale_number', 'subtotal', 'tax_amount', 'total_amount',
            'created_at', 'vendor_name', 'warehouse_name'
        ]


class CreateOfflineSaleSerializer(serializers.Serializer):
    """
    Serializer for creating offline sales with items
    """
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())
    
    # Customer details (optional)
    customer_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    
    # Payment details
    payment_method = serializers.ChoiceField(
        choices=OfflineSale.PAYMENT_METHODS,
        default='cash'
    )
    payment_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    discount_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, 
        required=False, default=0
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    # Items
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        write_only=True
    )

    def validate_items(self, items):
        """Validate items data"""
        validated_items = []
        
        for item_data in items:
            # Required fields
            if 'product_id' not in item_data:
                raise serializers.ValidationError("product_id is required for each item")
            if 'quantity' not in item_data:
                raise serializers.ValidationError("quantity is required for each item")
            if 'unit_price' not in item_data:
                raise serializers.ValidationError("unit_price is required for each item")
            
            # Validate product exists
            try:
                product = Product.objects.get(id=item_data['product_id'])
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with id {item_data['product_id']} not found")
            
            # Validate variant if provided
            variant = None
            if 'variant_id' in item_data and item_data['variant_id']:
                try:
                    variant = ProductVariant.objects.get(
                        id=item_data['variant_id'],
                        product=product
                    )
                except ProductVariant.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Variant with id {item_data['variant_id']} not found for product {product.name}"
                    )
            
            # Validate quantity
            quantity = item_data['quantity']
            if not isinstance(quantity, int) or quantity <= 0:
                raise serializers.ValidationError("Quantity must be a positive integer")
            
            # Validate unit_price
            try:
                unit_price = float(item_data['unit_price'])
                if unit_price < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise serializers.ValidationError("unit_price must be a positive number")
            
            validated_item = {
                'product': product,
                'variant': variant,
                'quantity': quantity,
                'unit_price': unit_price,
                'discount_per_item': float(item_data.get('discount_per_item', 0)),
                'batch_number': item_data.get('batch_number', ''),
                'expiry_date': item_data.get('expiry_date'),
            }
            
            validated_items.append(validated_item)
        
        return validated_items

    def create(self, validated_data):
        """Create offline sale using manager"""
        items_data = validated_data.pop('items')
        vendor = self.context['request'].user
        warehouse = validated_data.pop('warehouse')
        
        # Prepare customer data
        customer_data = {
            'name': validated_data.get('customer_name', ''),
            'phone': validated_data.get('customer_phone', ''),
            'email': validated_data.get('customer_email', ''),
        }
        
        # Prepare payment data
        payment_data = {
            'method': validated_data.get('payment_method', 'cash'),
            'reference': validated_data.get('payment_reference', ''),
            'notes': validated_data.get('notes', ''),
        }
        
        # Create sale
        sale = OfflineSaleManager.create_offline_sale(
            vendor=vendor,
            warehouse=warehouse,
            items_data=items_data,
            customer_data=customer_data,
            payment_data=payment_data
        )
        
        # Apply discount if provided
        if validated_data.get('discount_amount'):
            sale.discount_amount = validated_data['discount_amount']
            sale.calculate_totals()
        
        return sale


class VendorInventorySerializer(serializers.Serializer):
    """
    Serializer for vendor-specific inventory view
    """
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    variant_id = serializers.IntegerField(allow_null=True)
    variant_details = serializers.JSONField(allow_null=True)
    quantity = serializers.IntegerField()
    low_stock_threshold = serializers.IntegerField()
    is_low_stock = serializers.BooleanField()
    batch_number = serializers.CharField()
    expiry_date = serializers.DateField(allow_null=True)
    warehouse_name = serializers.CharField()


class OfflineSaleReportSerializer(serializers.Serializer):
    """
    Serializer for offline sales reports
    """
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    warehouse = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(),
        required=False,
        allow_null=True
    )
    
    def validate(self, data):
        if data['date_from'] > data['date_to']:
            raise serializers.ValidationError("date_from must be before date_to")
        return data
