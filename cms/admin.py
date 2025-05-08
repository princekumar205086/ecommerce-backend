# cms/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Page, Banner, BlogPost, BlogCategory,
    BlogTag, FAQ, Testimonial
)

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'status',
        'show_in_nav',
        'is_featured',
        'order',
        'created_at'
    ]
    list_filter = ['status', 'is_featured', 'show_in_nav', 'template']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'published_at']
    fieldsets = (
        (None, {
            'fields': (
                'title',
                'slug',
                'content',
                'excerpt',
                'status',
                'template'
            )
        }),
        ('SEO', {
            'fields': (
                'seo_title',
                'seo_description',
                'seo_keywords'
            ),
            'classes': ('collapse',)
        }),
        ('Navigation', {
            'fields': (
                'show_in_nav',
                'is_featured',
                'parent',
                'order'
            )
        }),
        ('Dates', {
            'fields': (
                'created_at',
                'updated_at',
                'published_at'
            ),
            'classes': ('collapse',)
        })
    )
    actions = ['make_published', 'make_draft']

    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(
            request,
            f"{updated} pages were successfully marked as published."
        )
    make_published.short_description = "Mark selected pages as published"

    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(
            request,
            f"{updated} pages were successfully marked as draft."
        )
    make_draft.short_description = "Mark selected pages as draft"


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'position',
        'is_active',
        'start_date',
        'end_date',
        'order'
    ]
    list_filter = ['position', 'is_active']
    search_fields = ['title', 'text']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'status',
        'author',
        'is_featured',
        'view_count',
        'published_at'
    ]
    list_filter = ['status', 'is_featured', 'categories', 'tags']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['categories', 'tags']
    readonly_fields = [
        'created_at',
        'updated_at',
        'published_at',
        'view_count'
    ]
    fieldsets = (
        (None, {
            'fields': (
                'title',
                'slug',
                'content',
                'excerpt',
                'featured_image',
                'status',
                'author'
            )
        }),
        ('SEO', {
            'fields': (
                'seo_title',
                'seo_description',
                'seo_keywords'
            ),
            'classes': ('collapse',)
        }),
        ('Categories & Tags', {
            'fields': (
                'categories',
                'tags'
            )
        }),
        ('Featured', {
            'fields': ('is_featured',)
        }),
        ('Statistics', {
            'fields': (
                'view_count',
                'created_at',
                'updated_at',
                'published_at'
            ),
            'classes': ('collapse',)
        })
    )
    actions = ['make_published', 'make_featured']

    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(
            request,
            f"{updated} blog posts were successfully marked as published."
        )
    make_published.short_description = "Mark selected posts as published"

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(
            request,
            f"{updated} blog posts were successfully marked as featured."
        )
    make_featured.short_description = "Mark selected posts as featured"

    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = [
        'question',
        'category',
        'is_active',
        'order'
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = [
        'author_name',
        'rating',
        'is_featured',
        'is_active',
        'created_at'
    ]
    list_filter = ['rating', 'is_featured', 'is_active']
    search_fields = ['author_name', 'content']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['make_featured']

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(
            request,
            f"{updated} testimonials were successfully marked as featured."
        )
    make_featured.short_description = "Mark selected testimonials as featured"