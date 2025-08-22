from django.contrib.auth import get_user_model
from rest_framework import serializers
from PIL import Image
from io import BytesIO
import os
import uuid

from .models import (
    Brand, ProductCategory, Product, ProductImage,
    ProductVariant, SupplierProductPrice,
    ProductReview, ProductAuditLog
)
from accounts.models import upload_to_imagekit

User = get_user_model()


# Brand
class BrandSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ('created_at',)

    def create(self, validated_data):
        image_file = validated_data.pop('image_file', None)
        if image_file:
            try:
                # Read file content into bytes
                if hasattr(image_file, 'read'):
                    image_file.seek(0)
                    file_bytes = image_file.read()
                else:
                    with open(image_file, 'rb') as f:
                        file_bytes = f.read()
                
                # Validate image using PIL
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as e:
                    raise serializers.ValidationError({'image_file': f'Invalid image file: {str(e)}'})
                
                # Generate unique filename
                original_filename = getattr(image_file, 'name', 'brand.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    raise serializers.ValidationError({'image_file': 'Unsupported image format. Please upload JPG, JPEG, PNG, GIF, or WEBP.'})
                
                filename = f"brand_{uuid.uuid4()}{ext}"
                
                # Upload using universal function
                image_url = upload_to_imagekit(file_bytes, filename, folder="products/brands")
                
                if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                    raise serializers.ValidationError({'image_file': 'Image upload to ImageKit failed. Please try again.'})
                
                validated_data['image'] = image_url
                
            except serializers.ValidationError:
                raise
            except Exception as e:
                raise serializers.ValidationError({'image_file': f'Error processing image: {str(e)}'})
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image_file', None)
        if image_file:
            try:
                # Read file content into bytes
                if hasattr(image_file, 'read'):
                    image_file.seek(0)
                    file_bytes = image_file.read()
                else:
                    with open(image_file, 'rb') as f:
                        file_bytes = f.read()
                
                # Validate image using PIL
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as e:
                    raise serializers.ValidationError({'image_file': f'Invalid image file: {str(e)}'})
                
                # Generate unique filename
                original_filename = getattr(image_file, 'name', 'brand.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    raise serializers.ValidationError({'image_file': 'Unsupported image format. Please upload JPG, JPEG, PNG, GIF, or WEBP.'})
                
                filename = f"brand_{uuid.uuid4()}{ext}"
                
                # Upload using universal function
                image_url = upload_to_imagekit(file_bytes, filename, folder="products/brands")
                
                if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                    raise serializers.ValidationError({'image_file': 'Image upload to ImageKit failed. Please try again.'})
                
                validated_data['image'] = image_url
                
            except serializers.ValidationError:
                raise
            except Exception as e:
                raise serializers.ValidationError({'image_file': f'Error processing image: {str(e)}'})
        
        return super().update(instance, validated_data)


# Category
class ProductCategorySerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    parent = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(), required=False, allow_null=True
    )
    icon_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = ProductCategory
        fields = [
            'id', 'name', 'parent', 'created_by',
            'created_at', 'status', 'is_publish', 'icon', 'icon_file'
        ]
        read_only_fields = ('created_at', 'status', 'is_publish')

    def create(self, validated_data):
        icon_file = validated_data.pop('icon_file', None)
        if icon_file:
            try:
                # Read file content into bytes
                if hasattr(icon_file, 'read'):
                    icon_file.seek(0)
                    file_bytes = icon_file.read()
                else:
                    with open(icon_file, 'rb') as f:
                        file_bytes = f.read()
                
                # Validate image using PIL
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as e:
                    raise serializers.ValidationError({'icon_file': f'Invalid image file: {str(e)}'})
                
                # Generate unique filename
                original_filename = getattr(icon_file, 'name', 'category.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    raise serializers.ValidationError({'icon_file': 'Unsupported image format. Please upload JPG, JPEG, PNG, GIF, or WEBP.'})
                
                filename = f"category_{uuid.uuid4()}{ext}"
                
                # Upload using universal function
                image_url = upload_to_imagekit(file_bytes, filename, folder="products/categories")
                
                if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                    raise serializers.ValidationError({'icon_file': 'Image upload to ImageKit failed. Please try again.'})
                
                validated_data['icon'] = image_url
                
            except serializers.ValidationError:
                raise
            except Exception as e:
                raise serializers.ValidationError({'icon_file': f'Error processing image: {str(e)}'})
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        icon_file = validated_data.pop('icon_file', None)
        if icon_file:
            try:
                # Read file content into bytes
                if hasattr(icon_file, 'read'):
                    icon_file.seek(0)
                    file_bytes = icon_file.read()
                else:
                    with open(icon_file, 'rb') as f:
                        file_bytes = f.read()
                
                # Validate image using PIL
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as e:
                    raise serializers.ValidationError({'icon_file': f'Invalid image file: {str(e)}'})
                
                # Generate unique filename
                original_filename = getattr(icon_file, 'name', 'category.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    raise serializers.ValidationError({'icon_file': 'Unsupported image format. Please upload JPG, JPEG, PNG, GIF, or WEBP.'})
                
                filename = f"category_{uuid.uuid4()}{ext}"
                
                # Upload using universal function
                image_url = upload_to_imagekit(file_bytes, filename, folder="products/categories")
                
                if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                    raise serializers.ValidationError({'icon_file': 'Image upload to ImageKit failed. Please try again.'})
                
                validated_data['icon'] = image_url
                
            except serializers.ValidationError:
                raise
            except Exception as e:
                raise serializers.ValidationError({'icon_file': f'Error processing image: {str(e)}'})
        
        return super().update(instance, validated_data)


# Product Image
class ProductImageSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'image_file']

    def create(self, validated_data):
        image_file = validated_data.pop('image_file', None)
        if image_file:
            try:
                # Read file content into bytes
                if hasattr(image_file, 'read'):
                    image_file.seek(0)
                    file_bytes = image_file.read()
                else:
                    with open(image_file, 'rb') as f:
                        file_bytes = f.read()
                
                # Validate image using PIL
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as e:
                    raise serializers.ValidationError({'image_file': f'Invalid image file: {str(e)}'})
                
                # Generate unique filename
                original_filename = getattr(image_file, 'name', 'product.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    raise serializers.ValidationError({'image_file': 'Unsupported image format. Please upload JPG, JPEG, PNG, GIF, or WEBP.'})
                
                filename = f"product_image_{uuid.uuid4()}{ext}"
                
                # Upload using universal function
                image_url = upload_to_imagekit(file_bytes, filename, folder="products/images")
                
                if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                    raise serializers.ValidationError({'image_file': 'Image upload to ImageKit failed. Please try again.'})
                
                validated_data['image'] = image_url
                
            except serializers.ValidationError:
                raise
            except Exception as e:
                raise serializers.ValidationError({'image_file': f'Error processing image: {str(e)}'})
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image_file', None)
        if image_file:
            try:
                # Read file content into bytes
                if hasattr(image_file, 'read'):
                    image_file.seek(0)
                    file_bytes = image_file.read()
                else:
                    with open(image_file, 'rb') as f:
                        file_bytes = f.read()
                
                # Validate image using PIL
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as e:
                    raise serializers.ValidationError({'image_file': f'Invalid image file: {str(e)}'})
                
                # Generate unique filename
                original_filename = getattr(image_file, 'name', 'product.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    raise serializers.ValidationError({'image_file': 'Unsupported image format. Please upload JPG, JPEG, PNG, GIF, or WEBP.'})
                
                filename = f"product_image_{uuid.uuid4()}{ext}"
                
                # Upload using universal function
                image_url = upload_to_imagekit(file_bytes, filename, folder="products/images")
                
                if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                    raise serializers.ValidationError({'image_file': 'Image upload to ImageKit failed. Please try again.'})
                
                validated_data['image'] = image_url
                
            except serializers.ValidationError:
                raise
            except Exception as e:
                raise serializers.ValidationError({'image_file': f'Error processing image: {str(e)}'})
        
        return super().update(instance, validated_data)


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
        # Only validate uniqueness if we have the required fields
        if 'product' in data and ('size' in data or 'weight' in data):
            query = ProductVariant.objects.filter(
                product=data['product'],
                size=data.get('size'),
                weight=data.get('weight')
            )
            # Exclude current instance during update
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise serializers.ValidationError("Variant with these specifications already exists.")
        return data


# Base Product Serializer
class BaseProductSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=ProductCategory.objects.all())
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), required=False, allow_null=True)
    image_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'brand',
            'price', 'stock', 'product_type', 'created_by',
            'created_at', 'updated_at', 'status', 'is_publish',
            'variants', 'images', 'image', 'image_file'
        ]
        read_only_fields = ('created_at', 'updated_at', 'status', 'is_publish')

    def create(self, validated_data):
        image_file = validated_data.pop('image_file', None)
        if image_file:
            try:
                # Read file content into bytes
                if hasattr(image_file, 'read'):
                    image_file.seek(0)
                    file_bytes = image_file.read()
                else:
                    with open(image_file, 'rb') as f:
                        file_bytes = f.read()
                
                # Validate image using PIL
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as e:
                    raise serializers.ValidationError({'image_file': f'Invalid image file: {str(e)}'})
                
                # Generate unique filename
                original_filename = getattr(image_file, 'name', 'product.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    raise serializers.ValidationError({'image_file': 'Unsupported image format. Please upload JPG, JPEG, PNG, GIF, or WEBP.'})
                
                filename = f"product_{uuid.uuid4()}{ext}"
                
                # Upload using universal function
                image_url = upload_to_imagekit(file_bytes, filename, folder="products/main")
                
                if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                    raise serializers.ValidationError({'image_file': 'Image upload to ImageKit failed. Please try again.'})
                
                validated_data['image'] = image_url
                
            except serializers.ValidationError:
                raise
            except Exception as e:
                raise serializers.ValidationError({'image_file': f'Error processing image: {str(e)}'})
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image_file', None)
        if image_file:
            try:
                # Read file content into bytes
                if hasattr(image_file, 'read'):
                    image_file.seek(0)
                    file_bytes = image_file.read()
                else:
                    with open(image_file, 'rb') as f:
                        file_bytes = f.read()
                
                # Validate image using PIL
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as e:
                    raise serializers.ValidationError({'image_file': f'Invalid image file: {str(e)}'})
                
                # Generate unique filename
                original_filename = getattr(image_file, 'name', 'product.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    raise serializers.ValidationError({'image_file': 'Unsupported image format. Please upload JPG, JPEG, PNG, GIF, or WEBP.'})
                
                filename = f"product_{uuid.uuid4()}{ext}"
                
                # Upload using universal function
                image_url = upload_to_imagekit(file_bytes, filename, folder="products/main")
                
                if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                    raise serializers.ValidationError({'image_file': 'Image upload to ImageKit failed. Please try again.'})
                
                validated_data['image'] = image_url
                
            except serializers.ValidationError:
                raise
            except Exception as e:
                raise serializers.ValidationError({'image_file': f'Error processing image: {str(e)}'})
        
        return super().update(instance, validated_data)


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
        
        # Only validate uniqueness if we have the required fields
        if 'product' in data:
            query = SupplierProductPrice.objects.filter(
                supplier=user,
                product=data['product'],
                pincode=data.get('pincode'),
                district=data.get('district')
            )
            # Exclude current instance during update
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
                
            if query.exists():
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
