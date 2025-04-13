from rest_framework import serializers

from products.models import Product, ProductVariant
from .models import Wishlist, WishlistItem
from products.serializers import ProductSerializer, ProductVariantSerializer

class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True, required=False)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        source='variant',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = WishlistItem
        fields = [
            'id', 'product', 'variant', 'product_id', 'variant_id',
            'added_at', 'notes'
        ]
        read_only_fields = ['added_at']

class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = [
            'id', 'name', 'user', 'items', 'item_count',
            'created_at', 'updated_at', 'is_default'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_item_count(self, obj):
        return obj.items.count()

class CreateWishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['name', 'is_default']
        extra_kwargs = {
            'is_default': {'required': False}
        }

class UpdateWishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['name', 'is_default']