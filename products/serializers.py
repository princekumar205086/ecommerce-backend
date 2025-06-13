from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Brand, ProductCategory, Product, ProductImage,
    ProductVariant, SupplierProductPrice,
    ProductReview, ProductAuditLog
)

User = get_user_model()


# Brand
class BrandSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ('created_at',)


# Category
class ProductCategorySerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    parent = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = ProductCategory
        fields = [
            'id', 'name', 'parent', 'created_by',
            'created_at', 'status', 'is_publish'
        ]
        read_only_fields = ('created_at', 'status', 'is_publish')


# Product Image
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text']


# Product Variant
class ProductVariantSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'size', 'weight',
            'additional_price', 'total_price',
            'stock', 'created_at'
        ]
        read_only_fields = ('created_at', 'total_price')

    def get_total_price(self, obj):
        return obj.product.price + obj.additional_price

    def validate(self, data):
        if ProductVariant.objects.filter(
                product=data['product'],
                size=data.get('size'),
                weight=data.get('weight')
        ).exists():
            raise serializers.ValidationError("Variant with these specifications already exists.")
        return data


# Base Product Serializer
class BaseProductSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=ProductCategory.objects.all())
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'brand',
            'price', 'stock', 'product_type', 'created_by',
            'created_at', 'updated_at', 'status', 'is_publish',
            'variants', 'images'
        ]
        read_only_fields = ('created_at', 'updated_at', 'status', 'is_publish')


# Medicine Product Serializer
class MedicineBaseProductSerializer(BaseProductSerializer):
    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            'composition', 'quantity', 'manufacturer',
            'expiry_date', 'batch_number', 'prescription_required',
            'form', 'pack_size'
        ]


# Equipment Product Serializer
class EquipmentBaseProductSerializer(BaseProductSerializer):
    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            'model_number', 'warranty_period', 'usage_type',
            'technical_specifications', 'power_requirement',
            'equipment_type'
        ]


# Pathology Product Serializer (fixed)
class PathologyBaseProductSerializer(BaseProductSerializer):
    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            'compatible_tests',
            'chemical_composition',
            'storage_condition'
        ]


# Supplier Price
class SupplierProductPriceSerializer(serializers.ModelSerializer):
    supplier = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SupplierProductPrice
        fields = '__all__'
        read_only_fields = ('created_at',)

    def validate(self, data):
        user = self.context['request'].user
        if SupplierProductPrice.objects.filter(
                supplier=user,
                product=data['product'],
                pincode=data.get('pincode'),
                district=data.get('district')
        ).exists():
            raise serializers.ValidationError("Price already exists for this product in the specified region.")
        return data


# Review
class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProductReview
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'is_published', 'user')

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate(self, data):
        request = self.context.get('request')
        if request and not self.instance:
            if ProductReview.objects.filter(product=data['product'], user=request.user).exists():
                raise serializers.ValidationError("You have already reviewed this product.")
        return data


# Audit Log
class ProductAuditLogSerializer(serializers.ModelSerializer):
    changed_by = serializers.StringRelatedField(read_only=True)
    product = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProductAuditLog
        fields = '__all__'
