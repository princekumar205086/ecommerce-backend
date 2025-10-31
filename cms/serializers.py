# cms/serializers.py
from rest_framework import serializers
from .models import (
    Page, Banner, BlogPost, BlogCategory,
    BlogTag, FAQ, Testimonial, CarouselBanner
)
from accounts.serializers import UserSerializer

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
    class Meta:
        model = CarouselBanner
        fields = [
            'id',
            'title',
            'image',
            'link',
            'caption',
            'order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']