from django.contrib.auth import get_user_model
from rest_framework import serializers
from PIL import Image
from io import BytesIO
import os
import uuid

from .models import (
    Brand, ProductCategory, Product, ProductImage,
    ProductVariant, SupplierProductPrice, ProductReview, ProductAuditLog,
    MedicineDetails, EquipmentDetails, PathologyDetails,
    ProductAttribute, ProductAttributeValue
)
from accounts.models import upload_to_imagekit

User = get_user_model()


# Simple Brand Serializer for nested representation
class SimpleBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'image']


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


# Simple Category Serializer for nested representation
class SimpleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'icon', 'slug']


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
        fields = ['id', 'image', 'alt_text', 'order', 'variant', 'image_file']

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


# Product Attributes
class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ['id', 'name']


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    
    class Meta:
        model = ProductAttributeValue
        fields = ['id', 'attribute', 'attribute_name', 'value']
# Product Variant
class ProductVariantSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()
    attributes = ProductAttributeValueSerializer(many=True, read_only=True)
    attribute_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'sku', 'price', 'additional_price', 'total_price',
            'stock', 'is_active', 'attributes', 'attribute_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at', 'total_price', 'sku')

    def get_total_price(self, obj):
        return obj.total_price

    def create(self, validated_data):
        attribute_ids = validated_data.pop('attribute_ids', [])
        variant = super().create(validated_data)
        
        if attribute_ids:
            attribute_values = ProductAttributeValue.objects.filter(id__in=attribute_ids)
            variant.attributes.set(attribute_values)
        
        return variant

    def update(self, instance, validated_data):
        attribute_ids = validated_data.pop('attribute_ids', None)
        variant = super().update(instance, validated_data)
        
        if attribute_ids is not None:
            attribute_values = ProductAttributeValue.objects.filter(id__in=attribute_ids)
            variant.attributes.set(attribute_values)
        
        return variant


# Product Type Detail Serializers
class MedicineDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineDetails
        fields = [
            'composition', 'quantity', 'manufacturer', 'expiry_date',
            'batch_number', 'prescription_required', 'form', 'pack_size'
        ]


class EquipmentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentDetails
        fields = [
            'model_number', 'warranty_period', 'usage_type',
            'technical_specifications', 'power_requirement', 'equipment_type'
        ]


class PathologyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathologyDetails
        fields = [
            'compatible_tests', 'chemical_composition', 'storage_condition'
        ]


# Base Product Serializer (for admin/write operations)
class BaseProductSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=ProductCategory.objects.all())
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), required=False, allow_null=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    image_file = serializers.ImageField(write_only=True, required=False)
    
    # Type-specific details
    medicine_details = MedicineDetailsSerializer(read_only=True)
    equipment_details = EquipmentDetailsSerializer(read_only=True)
    pathology_details = PathologyDetailsSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'description', 'category', 'category_id', 'category_name',
            'brand', 'brand_name', 'price', 'stock', 'product_type', 'created_by',
            'created_at', 'updated_at', 'status', 'is_publish', 'specifications',
            'variants', 'images', 'image', 'image_file',
            'medicine_details', 'equipment_details', 'pathology_details'
        ]
        read_only_fields = ('created_at', 'updated_at', 'status', 'is_publish', 'slug', 'sku')


# Public Product Serializer (for frontend with nested objects)
class PublicProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    category = SimpleCategorySerializer(read_only=True)
    brand = SimpleBrandSerializer(read_only=True)
    
    # Type-specific details
    medicine_details = MedicineDetailsSerializer(read_only=True)
    equipment_details = EquipmentDetailsSerializer(read_only=True)
    pathology_details = PathologyDetailsSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'description', 'category', 'brand', 
            'price', 'stock', 'product_type', 'created_at', 'updated_at', 
            'status', 'is_publish', 'specifications', 'variants', 'images', 'image',
            'medicine_details', 'equipment_details', 'pathology_details'
        ]

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
    medicine_details = MedicineDetailsSerializer()

    class Meta(BaseProductSerializer.Meta):
        pass

    def create(self, validated_data):
        medicine_details_data = validated_data.pop('medicine_details', {})
        product = super().create(validated_data)
        
        if medicine_details_data:
            MedicineDetails.objects.create(product=product, **medicine_details_data)
        
        return product

    def update(self, instance, validated_data):
        medicine_details_data = validated_data.pop('medicine_details', None)
        product = super().update(instance, validated_data)
        
        if medicine_details_data is not None:
            medicine_details, created = MedicineDetails.objects.get_or_create(product=product)
            for attr, value in medicine_details_data.items():
                setattr(medicine_details, attr, value)
            medicine_details.save()
        
        return product


# Equipment Product Serializer
class EquipmentBaseProductSerializer(BaseProductSerializer):
    equipment_details = EquipmentDetailsSerializer()

    class Meta(BaseProductSerializer.Meta):
        pass

    def create(self, validated_data):
        equipment_details_data = validated_data.pop('equipment_details', {})
        product = super().create(validated_data)
        
        if equipment_details_data:
            EquipmentDetails.objects.create(product=product, **equipment_details_data)
        
        return product

    def update(self, instance, validated_data):
        equipment_details_data = validated_data.pop('equipment_details', None)
        product = super().update(instance, validated_data)
        
        if equipment_details_data is not None:
            equipment_details, created = EquipmentDetails.objects.get_or_create(product=product)
            for attr, value in equipment_details_data.items():
                setattr(equipment_details, attr, value)
            equipment_details.save()
        
        return product


# Pathology Product Serializer
class PathologyBaseProductSerializer(BaseProductSerializer):
    pathology_details = PathologyDetailsSerializer()

    class Meta(BaseProductSerializer.Meta):
        pass

    def create(self, validated_data):
        pathology_details_data = validated_data.pop('pathology_details', {})
        product = super().create(validated_data)
        
        if pathology_details_data:
            PathologyDetails.objects.create(product=product, **pathology_details_data)
        
        return product

    def update(self, instance, validated_data):
        pathology_details_data = validated_data.pop('pathology_details', None)
        product = super().update(instance, validated_data)
        
        if pathology_details_data is not None:
            pathology_details, created = PathologyDetails.objects.get_or_create(product=product)
            for attr, value in pathology_details_data.items():
                setattr(pathology_details, attr, value)
            pathology_details.save()
        
        return product


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
        if 'product_variant' in data:
            query = SupplierProductPrice.objects.filter(
                supplier=user,
                product_variant=data['product_variant'],
                pincode=data.get('pincode'),
                district=data.get('district')
            )
            # Exclude current instance during update
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
                
            if query.exists():
                raise serializers.ValidationError("Price already exists for this product variant in the specified region.")
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
