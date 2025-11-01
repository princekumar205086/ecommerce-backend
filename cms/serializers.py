# cms/serializers.py
from rest_framework import serializers
from PIL import Image
from io import BytesIO
import os
import uuid

from .models import (
    Page, Banner, BlogPost, BlogCategory,
    BlogTag, FAQ, Testimonial, CarouselBanner
)
from accounts.serializers import UserSerializer
from accounts.models import upload_to_imagekit

class PageSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    template_display = serializers.CharField(
        source='get_template_display',
        read_only=True
    )
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Page.objects.filter(status='published'),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Page
        fields = [
            'id',
            'title',
            'slug',
            'content',
            'excerpt',
            'status',
            'status_display',
            'template',
            'template_display',
            'seo_title',
            'seo_description',
            'seo_keywords',
            'created_by',
            'updated_by',
            'created_at',
            'updated_at',
            'published_at',
            'is_featured',
            'show_in_nav',
            'parent',
            'order'
        ]
        read_only_fields = [
            'slug',
            'created_by',
            'updated_by',
            'created_at',
            'updated_at',
            'published_at'
        ]


class BannerSerializer(serializers.ModelSerializer):
    position_display = serializers.CharField(
        source='get_position_display',
        read_only=True
    )
    is_active_now = serializers.BooleanField(read_only=True)

    class Meta:
        model = Banner
        fields = [
            'id',
            'title',
            'image',
            'mobile_image',
            'link',
            'text',
            'button_text',
            'position',
            'position_display',
            'is_active',
            'is_active_now',
            'start_date',
            'end_date',
            'order',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']


class BlogTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogTag
        fields = [
            'id',
            'name',
            'slug',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']


class BlogPostSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    author = UserSerializer(read_only=True)
    categories = BlogCategorySerializer(many=True, read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=BlogCategory.objects.all(),
        write_only=True,
        many=True,
        source='categories',
        required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=BlogTag.objects.all(),
        write_only=True,
        many=True,
        source='tags',
        required=False
    )

    class Meta:
        model = BlogPost
        fields = [
            'id',
            'title',
            'slug',
            'content',
            'excerpt',
            'featured_image',
            'status',
            'status_display',
            'author',
            'categories',
            'tags',
            'category_ids',
            'tag_ids',
            'seo_title',
            'seo_description',
            'seo_keywords',
            'created_at',
            'updated_at',
            'published_at',
            'is_featured',
            'view_count'
        ]
        read_only_fields = [
            'slug',
            'author',
            'created_at',
            'updated_at',
            'published_at',
            'view_count'
        ]


class FAQSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )

    class Meta:
        model = FAQ
        fields = [
            'id',
            'question',
            'answer',
            'category',
            'category_display',
            'order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TestimonialSerializer(serializers.ModelSerializer):
    rating_display = serializers.CharField(
        source='get_rating_display',
        read_only=True
    )

    class Meta:
        model = Testimonial
        fields = [
            'id',
            'author_name',
            'author_title',
            'content',
            'image',
            'rating',
            'rating_display',
            'is_featured',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CarouselBannerSerializer(serializers.ModelSerializer):
    # Maximum allowed upload size for carousel images (bytes)
    MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    image_file = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = CarouselBanner
        fields = [
            'id',
            'title',
            'image',
            'image_file',
            'link',
            'caption',
            'order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'image': {'required': False}
        }

    def validate_image_file(self, value):
        """Validate uploaded image file size and type."""
        if not value:
            return value

        # Check file size
        try:
            size = value.size
        except Exception:
            size = 0

        if size > self.MAX_IMAGE_SIZE:
            raise serializers.ValidationError('Image file too large. Maximum size allowed is 2 MB.')

        # Check extension
        filename = getattr(value, 'name', '')
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError('Unsupported image format. Allowed types: JPG, PNG, GIF, WEBP.')

        # Validate image using PIL
        try:
            image_file_copy = BytesIO(value.read())
            value.seek(0)  # Reset for later reading
            img = Image.open(image_file_copy)
            img.verify()
        except Exception as e:
            raise serializers.ValidationError(f'Invalid image file: {str(e)}')

        return value

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
                
                # Generate unique filename
                original_filename = getattr(image_file, 'name', 'carousel.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in self.ALLOWED_EXTENSIONS:
                    ext = '.jpg'
                
                filename = f"carousel_{uuid.uuid4()}{ext}"
                
                # Upload to ImageKit
                image_url = upload_to_imagekit(file_bytes, filename, folder="carousel_banners")
                
                if image_url and isinstance(image_url, str):
                    validated_data['image'] = image_url
                
            except Exception as e:
                # If upload fails, don't crash - just continue
                pass
        
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
                
                # Generate unique filename
                original_filename = getattr(image_file, 'name', 'carousel.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in self.ALLOWED_EXTENSIONS:
                    ext = '.jpg'
                
                filename = f"carousel_{uuid.uuid4()}{ext}"
                
                # Upload to ImageKit
                image_url = upload_to_imagekit(file_bytes, filename, folder="carousel_banners")
                
                if image_url and isinstance(image_url, str):
                    validated_data['image'] = image_url
                
            except Exception as e:
                # If upload fails, don't crash - just continue
                pass
        
        return super().update(instance, validated_data)