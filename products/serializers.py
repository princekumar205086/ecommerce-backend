from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ProductCategory, ProductSubCategory, Product, ProductReview,
    Brand, ProductVariant
)

User = get_user_model()


class BrandSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ('created_at',)
        extra_kwargs = {
            'name': {'required': True}
        }


class ProductCategorySerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ProductCategory
        exclude = ['slug']
        read_only_fields = ('created_at', 'status', 'is_publish')
        extra_kwargs = {
            'name': {'required': True}
        }


class ProductSubCategorySerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    category = serializers.PrimaryKeyRelatedField(queryset=ProductCategory.objects.all())

    class Meta:
        model = ProductSubCategory
        exclude = ['slug']
        read_only_fields = ('created_at', 'status', 'is_publish')
        extra_kwargs = {
            'name': {'required': True},
            'category': {'required': True}
        }


class ProductVariantSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'size', 'weight', 'additional_price', 'total_price', 'created_at']
        read_only_fields = ('created_at', 'total_price')
        extra_kwargs = {
            'product': {'required': True},
            'additional_price': {'min_value': 0}
        }

    def get_total_price(self, obj):
        return obj.total_price

    def validate(self, data):
        # Check if variant with same attributes already exists
        if ProductVariant.objects.filter(
                product=data['product'],
                size=data.get('size'),
                weight=data.get('weight')
        ).exists():
            raise serializers.ValidationError(
                "A product variant with these specifications already exists",
                code='unique'
            )
        return data


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    category = serializers.PrimaryKeyRelatedField(queryset=ProductCategory.objects.all())
    subcategory = serializers.PrimaryKeyRelatedField(
        queryset=ProductSubCategory.objects.all(),
        required=False,
        allow_null=True
    )
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Product
        exclude = ['slug']
        read_only_fields = ('created_at', 'status', 'is_publish')
        extra_kwargs = {
            'price': {'min_value': 0},
            'stock': {'min_value': 0}
        }

    def validate(self, data):
        """Validate subcategory belongs to category"""
        category = data.get('category')
        subcategory = data.get('subcategory')

        if subcategory and subcategory.category != category:
            raise serializers.ValidationError({
                'subcategory': 'Subcategory must belong to the selected category'
            })
        return data


class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = ProductReview
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'is_published', 'user')

    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate(self, data):
        """Validate user hasn't already reviewed this product"""
        request = self.context.get('request')
        if request and self.instance is None:  # Only for create operations
            if ProductReview.objects.filter(
                    product=data['product'],
                    user=request.user
            ).exists():
                raise serializers.ValidationError("You have already reviewed this product")
        return data
