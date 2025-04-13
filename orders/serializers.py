from rest_framework import serializers
from .models import Order
from cart.models import CartItem
from cart.serializers import CartItemSerializer

class OrderSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'total', 'shipping_address', 'payment_method', 'is_paid', 'paid_at', 'status', 'created_at']
