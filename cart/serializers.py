from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        ref_name = "CartProduct"  # Explicitly set a unique ref_name

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']


class AddToCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['product', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_items', 'total', 'created_at']

    def get_total(self, obj):
        return sum(item.product.price * item.quantity for item in obj.items.all())

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())

