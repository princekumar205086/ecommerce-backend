from django.contrib import admin
from .models import (
    Product, ProductCategory, Brand, ProductImage, ProductVariant,
    MedicineDetails, EquipmentDetails, PathologyDetails,
    ProductAttribute, ProductAttributeValue, SupplierProductPrice,
    ProductReview, ProductAuditLog
)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'status', 'is_publish', 'created_at']
    list_filter = ['status', 'is_publish', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class MedicineDetailsInline(admin.StackedInline):
    model = MedicineDetails
    extra = 0


class EquipmentDetailsInline(admin.StackedInline):
    model = EquipmentDetails
    extra = 0


class PathologyDetailsInline(admin.StackedInline):
    model = PathologyDetails
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'brand', 'product_type', 'price', 'mrp', 'stock', 'status', 'is_publish']
    list_filter = ['product_type', 'status', 'is_publish', 'category', 'brand', 'created_at']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]
    
    def get_inlines(self, request, obj):
        inlines = [ProductImageInline, ProductVariantInline]
        if obj:
            if obj.product_type == 'medicine':
                inlines.append(MedicineDetailsInline)
            elif obj.product_type == 'equipment':
                inlines.append(EquipmentDetailsInline)
            elif obj.product_type == 'pathology':
                inlines.append(PathologyDetailsInline)
        return inlines


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value']
    list_filter = ['attribute']
    search_fields = ['value']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'sku', 'price', 'mrp', 'stock', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['product__name', 'sku']


@admin.register(SupplierProductPrice)
class SupplierProductPriceAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'product_variant', 'price', 'mrp', 'pincode', 'district']
    list_filter = ['created_at']
    search_fields = ['supplier__username', 'product_variant__product__name']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_published', 'created_at']
    list_filter = ['rating', 'is_published', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']


@admin.register(ProductAuditLog)
class ProductAuditLogAdmin(admin.ModelAdmin):
    list_display = ['product', 'changed_by', 'changed_at']
    list_filter = ['changed_at']
    search_fields = ['product__name', 'changed_by__username']
    readonly_fields = ['product', 'changed_by', 'changes', 'changed_at']
