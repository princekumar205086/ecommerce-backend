from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from cart.models import Cart
from coupon.models import Coupon
from .models import Order, OrderItem, OrderStatusChange
from products.serializers import ProductSerializer, ProductVariantSerializer
from coupon.serializers import CouponSerializer
from accounts.serializers import UserSerializer
from decimal import Decimal


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'variant', 'quantity',
            'price', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'price', 'created_at']

    def get_total_price(self, obj):
        return obj.total_price


class OrderStatusChangeSerializer(serializers.ModelSerializer):
    changed_by = UserSerializer(read_only=True)

    class Meta:
        model = OrderStatusChange
        fields = ['id', 'status', 'changed_by', 'notes', 'created_at']
        read_only_fields = ['id', 'changed_by', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_changes = OrderStatusChangeSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    coupon = CouponSerializer(read_only=True)
    current_status = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'current_status',
            'payment_status', 'payment_method', 'subtotal', 'tax',
            'shipping_charge', 'discount', 'coupon', 'coupon_discount',
            'total', 'created_at', 'updated_at', 'shipping_address',
            'billing_address', 'notes', 'items', 'status_changes'
        ]
        read_only_fields = [
            'id', 'order_number', 'created_at', 'updated_at',
            'subtotal', 'tax', 'total', 'coupon_discount'
        ]

    def get_current_status(self, obj):
        latest_status = obj.status_changes.order_by('-created_at').first()
        return {
            'status': obj.get_status_display(),
            'timestamp': latest_status.created_at if latest_status else obj.updated_at,
            'changed_by': latest_status.changed_by.email if latest_status and latest_status.changed_by else None
        }


class CreateOrderSerializer(serializers.ModelSerializer):
    cart_id = serializers.IntegerField(
        required=False,
        help_text="ID of the cart to convert to order"
    )
    coupon_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Order
        fields = [
            'shipping_address', 'billing_address',
            'payment_method', 'notes', 'cart_id', 'coupon_code'
        ]

    def validate(self, data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context missing")

        if 'cart_id' in data:
            try:
                cart = request.user.carts.get(id=data['cart_id'])
                if not cart.items.exists():
                    raise serializers.ValidationError("Cart is empty")
            except Cart.DoesNotExist:
                raise serializers.ValidationError("Invalid cart ID")

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        cart_id = validated_data.pop('cart_id', None)
        coupon_code = validated_data.pop('coupon_code', None)

        if cart_id:
            # Create from cart
            cart = request.user.carts.get(id=cart_id)
            try:
                order = Order.create_from_cart(
                    cart=cart,
                    shipping_address=validated_data['shipping_address'],
                    billing_address=validated_data['billing_address'],
                    payment_method=validated_data.get('payment_method')
                )

                # Apply coupon if valid
                if coupon_code:
                    try:
                        order.coupon = Coupon.objects.get(code=coupon_code)
                        is_valid, _ = order.coupon.is_valid(request.user, order.subtotal)
                        if is_valid:
                            order.coupon_discount = order.coupon.apply_discount(order.subtotal)
                            order.calculate_totals()
                    except Coupon.DoesNotExist:
                        pass

                order.save()
                return order

            except ValidationError as e:
                raise serializers.ValidationError({'cart': str(e)})

        raise serializers.ValidationError("Cart ID is required for order creation")


class UpdateOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status', 'notes']
