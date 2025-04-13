# serializers.py
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


class ProductCategorySerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ProductCategory
        exclude = ['slug']
        read_only_fields = ('created_at', 'status', 'is_publish')


class ProductSubCategorySerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ProductSubCategory
        exclude = ['slug']
        read_only_fields = ('created_at', 'status', 'is_publish')


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'
        read_only_fields = ('created_at',)


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Product
        exclude = ['slug']
        read_only_fields = ('created_at', 'status', 'is_publish')


# serializers.py
class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProductReview
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False}  # Not required in input
        }

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
