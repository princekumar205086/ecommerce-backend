from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import BaseProductSerializer, ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = BaseProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'variant', 'quantity', 'total_price']
        read_only_fields = ['id', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price


class AddToCartSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    quantity = serializers.IntegerField(default=1, min_value=1)

    class Meta:
        model = CartItem
        fields = ['product_id', 'variant_id', 'quantity']


class UpdateCartItemSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ['quantity']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'user',
            'items',
            'total_items',
            'total_price',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'user',
            'total_items',
            'total_price',
            'created_at',
            'updated_at'
        ]

    def get_total_price(self, obj):
        return obj.total_price

    def get_total_items(self, obj):
        return obj.total_items
