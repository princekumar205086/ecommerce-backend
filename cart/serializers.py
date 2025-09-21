from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import BaseProductSerializer, ProductVariantSerializer
from products.models import Product, ProductVariant
from django.core.exceptions import ValidationError


class CartItemSerializer(serializers.ModelSerializer):
    """Enhanced serializer for cart items with better variant information"""
    product = BaseProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    available_stock = serializers.SerializerMethodField()
    variant_display = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'variant', 'quantity', 'unit_price', 
            'total_price', 'available_stock', 'variant_display', 'is_available'
        ]
        read_only_fields = ['id', 'unit_price', 'total_price', 'available_stock', 'variant_display', 'is_available']

    def get_unit_price(self, obj):
        """Get the unit price including variant additional price"""
        base_price = float(obj.product.price)
        if obj.variant:
            base_price += float(obj.variant.additional_price)
        return base_price

    def get_total_price(self, obj):
        return obj.total_price

    def get_available_stock(self, obj):
        """Get available stock for this item"""
        if obj.variant:
            return obj.variant.stock
        return obj.product.stock

    def get_variant_display(self, obj):
        """Get formatted variant display text"""
        if obj.variant:
            # Use the variant's __str__ method which handles attributes properly
            return str(obj.variant)
        return "Default"

    def get_is_available(self, obj):
        """Check if the item is still available in requested quantity"""
        available_stock = self.get_available_stock(obj)
        return available_stock >= obj.quantity


class AddToCartSerializer(serializers.Serializer):
    """Enhanced serializer for adding items to cart with better validation"""
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate_product_id(self, value):
        """Validate that product exists and is available"""
        try:
            product = Product.objects.get(id=value)
            if product.status != 'published':
                raise serializers.ValidationError("This product is not available")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")

    def validate_variant_id(self, value):
        """Validate that variant exists if provided"""
        if value is not None:
            try:
                variant = ProductVariant.objects.get(id=value)
                if variant.status != 'approved':
                    raise serializers.ValidationError("This variant is not available")
                return value
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Variant not found")
        return value

    def validate(self, data):
        """Cross-field validation"""
        product_id = data['product_id']
        variant_id = data.get('variant_id')
        quantity = data['quantity']

        try:
            product = Product.objects.get(id=product_id)
            
            # If variant is provided, validate it belongs to the product
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id)
                    if variant.product_id != product_id:
                        raise serializers.ValidationError("Variant does not belong to the selected product")
                    
                    # Check stock availability for variant
                    if quantity > variant.stock:
                        raise serializers.ValidationError(
                            f"Only {variant.stock} items available for this variant"
                        )
                except ProductVariant.DoesNotExist:
                    raise serializers.ValidationError("Invalid variant")
            else:
                # Check stock availability for product
                if quantity > product.stock:
                    raise serializers.ValidationError(
                        f"Only {product.stock} items available"
                    )

        except Product.DoesNotExist:
            raise serializers.ValidationError("Invalid product")

        return data


class UpdateCartItemSerializer(serializers.ModelSerializer):
    """Enhanced serializer for updating cart items with stock validation"""
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ['quantity']

    def validate_quantity(self, value):
        """Validate quantity against available stock"""
        if hasattr(self, 'instance') and self.instance:
            cart_item = self.instance
            available_stock = cart_item.variant.stock if cart_item.variant else cart_item.product.stock
            
            if value > available_stock:
                raise serializers.ValidationError(
                    f"Only {available_stock} items available in stock"
                )
        return value


class CartSerializer(serializers.ModelSerializer):
    """Enhanced cart serializer with better information and summary"""
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    has_unavailable_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'items', 'items_count', 'total_items', 'total_price',
            'has_unavailable_items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'items_count', 'total_items', 'total_price',
            'has_unavailable_items', 'created_at', 'updated_at'
        ]

    def get_total_price(self, obj):
        return obj.total_price

    def get_total_items(self, obj):
        return obj.total_items

    def get_items_count(self, obj):
        """Get number of unique items in cart"""
        return obj.items.count()

    def get_has_unavailable_items(self, obj):
        """Check if cart has any unavailable items"""
        for item in obj.items.all():
            available_stock = item.variant.stock if item.variant else item.product.stock
            if available_stock < item.quantity:
                return True
        return False
