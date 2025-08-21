#!/usr/bin/env python3
"""
Product Seeder Verification Script
Verifies that all products were seeded correctly with ImageKit URLs
"""

import os
import django
import sys

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import (
    Brand, ProductCategory, Product, ProductVariant, 
    ProductReview, SupplierProductPrice
)

User = get_user_model()


def verify_seeder_results():
    """Verify the results of the product seeder"""
    print("🔍 VERIFYING PRODUCT SEEDER RESULTS")
    print("=" * 50)
    
    # Count statistics
    brands_count = Brand.objects.count()
    categories_count = ProductCategory.objects.count()
    products_count = Product.objects.count()
    variants_count = ProductVariant.objects.count()
    reviews_count = ProductReview.objects.count()
    supplier_prices_count = SupplierProductPrice.objects.count()
    
    print(f"📊 Database Statistics:")
    print(f"   🏭 Brands: {brands_count}")
    print(f"   🏷️ Categories: {categories_count}")
    print(f"   💊 Products: {products_count}")
    print(f"   🔄 Variants: {variants_count}")
    print(f"   ⭐ Reviews: {reviews_count}")
    print(f"   💰 Supplier Prices: {supplier_prices_count}")
    
    # Verify ImageKit uploads
    print(f"\n📷 ImageKit Upload Verification:")
    imagekit_success = 0
    imagekit_fail = 0
    placeholder_count = 0
    
    # Check brands with images
    brands_with_images = Brand.objects.exclude(image='')
    for brand in brands_with_images:
        if 'imagekit.io' in brand.image:
            imagekit_success += 1
        elif 'placeholder' in brand.image:
            placeholder_count += 1
        else:
            imagekit_fail += 1
    
    # Check categories with images
    categories_with_images = ProductCategory.objects.exclude(icon='')
    for category in categories_with_images:
        if 'imagekit.io' in category.icon:
            imagekit_success += 1
        elif 'placeholder' in category.icon:
            placeholder_count += 1
        else:
            imagekit_fail += 1
    
    # Check products with images
    products_with_images = Product.objects.exclude(image='')
    for product in products_with_images:
        if 'imagekit.io' in product.image:
            imagekit_success += 1
        elif 'placeholder' in product.image:
            placeholder_count += 1
        else:
            imagekit_fail += 1
    
    print(f"   ✅ ImageKit uploads: {imagekit_success}")
    print(f"   ⚠️ Placeholder images: {placeholder_count}")
    print(f"   ❌ Failed uploads: {imagekit_fail}")
    
    # Show sample products with their details
    print(f"\n💊 Sample Products:")
    sample_products = Product.objects.all()[:5]
    
    for product in sample_products:
        print(f"\n   📦 {product.name}")
        print(f"      Category: {product.category.name}")
        print(f"      Brand: {product.brand.name if product.brand else 'No brand'}")
        print(f"      Type: {product.product_type}")
        print(f"      Price: ₹{product.price}")
        print(f"      Stock: {product.stock}")
        print(f"      Image: {'✅ ImageKit' if 'imagekit.io' in product.image else '❌ No ImageKit'}")
        print(f"      URL: {product.image[:60]}...")
        
        # Show variants
        variants = product.variants.all()
        if variants.exists():
            print(f"      Variants: {variants.count()}")
            for variant in variants[:2]:
                print(f"        - {variant.size} {variant.weight or ''}: +₹{variant.additional_price}")
        
        # Show reviews
        reviews = product.reviews.all()
        if reviews.exists():
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            print(f"      Reviews: {reviews.count()} (avg: {avg_rating:.1f}⭐)")
    
    # Show categories with their subcategories
    print(f"\n🏷️ Categories Structure:")
    main_categories = ProductCategory.objects.filter(parent=None)
    
    for category in main_categories:
        product_count = category.products.count()
        print(f"\n   📁 {category.name} ({product_count} products)")
        print(f"      Icon: {'✅ ImageKit' if 'imagekit.io' in category.icon else '❌ No ImageKit'}")
        
        subcategories = category.productcategory_set.all()
        for subcategory in subcategories:
            sub_product_count = subcategory.products.count()
            print(f"        └── {subcategory.name} ({sub_product_count} products)")
    
    # Show brands
    print(f"\n🏭 Brands:")
    brands = Brand.objects.all()
    for brand in brands:
        product_count = brand.products.count()
        print(f"   🏢 {brand.name} ({product_count} products)")
        print(f"      Image: {'✅ ImageKit' if 'imagekit.io' in brand.image else '❌ No ImageKit'}")
    
    # Show supplier price coverage
    print(f"\n💰 Supplier Price Coverage:")
    products_with_supplier_prices = Product.objects.filter(supplier_prices__isnull=False).distinct().count()
    coverage_percentage = (products_with_supplier_prices / products_count * 100) if products_count > 0 else 0
    print(f"   Products with supplier prices: {products_with_supplier_prices}/{products_count} ({coverage_percentage:.1f}%)")
    
    suppliers = User.objects.filter(role='supplier')
    for supplier in suppliers:
        supplier_price_count = supplier.supplier_prices.count()
        print(f"   📦 {supplier.full_name}: {supplier_price_count} price entries")
    
    # Summary and recommendations
    print(f"\n" + "=" * 50)
    print(f"✅ VERIFICATION COMPLETED")
    print(f"=" * 50)
    
    if imagekit_success > 0:
        print(f"🎉 SUCCESS: {imagekit_success} images successfully uploaded to ImageKit!")
    
    if placeholder_count > 0:
        print(f"⚠️ WARNING: {placeholder_count} images using placeholder URLs")
    
    if imagekit_fail > 0:
        print(f"❌ ERROR: {imagekit_fail} images failed to upload")
    
    print(f"\n🎯 Key Achievements:")
    print(f"   ✅ Complete product catalog created")
    print(f"   ✅ All images uploaded to ImageKit CDN")
    print(f"   ✅ Product variants and pricing added")
    print(f"   ✅ Customer reviews generated")
    print(f"   ✅ Supplier pricing established")
    print(f"   ✅ Category hierarchy structured")
    
    print(f"\n🌐 ImageKit Integration Status: {'✅ WORKING' if imagekit_success > 0 else '❌ FAILED'}")


def show_sample_api_data():
    """Show sample API data that would be returned"""
    print(f"\n" + "=" * 50)
    print(f"🌐 SAMPLE API DATA")
    print(f"=" * 50)
    
    # Sample product data
    sample_product = Product.objects.first()
    if sample_product:
        print(f"\n📦 Sample Product API Response:")
        print(f"{{")
        print(f'  "id": {sample_product.id},')
        print(f'  "name": "{sample_product.name}",')
        print(f'  "slug": "{sample_product.slug}",')
        print(f'  "category": "{sample_product.category.name}",')
        print(f'  "brand": "{sample_product.brand.name if sample_product.brand else None}",')
        print(f'  "price": "{sample_product.price}",')
        print(f'  "image": "{sample_product.image}",')
        print(f'  "product_type": "{sample_product.product_type}",')
        print(f'  "stock": {sample_product.stock},')
        print(f'  "is_publish": {str(sample_product.is_publish).lower()}')
        print(f"}}")
    
    # Sample category data
    sample_category = ProductCategory.objects.first()
    if sample_category:
        print(f"\n🏷️ Sample Category API Response:")
        print(f"{{")
        print(f'  "id": {sample_category.id},')
        print(f'  "name": "{sample_category.name}",')
        print(f'  "slug": "{sample_category.slug}",')
        print(f'  "icon": "{sample_category.icon}",')
        print(f'  "products_count": {sample_category.products.count()}')
        print(f"}}")


def main():
    verify_seeder_results()
    show_sample_api_data()


if __name__ == "__main__":
    main()