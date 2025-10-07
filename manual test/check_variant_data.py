#!/usr/bin/env python3
"""
Script to check variant data for products
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductVariant, ProductAttribute, ProductAttributeValue, ProductImage, ProductReview

def check_variant_data():
    print("=== VARIANT DATA ANALYSIS ===\n")
    
    # Check all products
    products = Product.objects.filter(is_publish=True, status='published')
    print(f"Total published products: {products.count()}")
    
    # Check specific product (ID 4)
    try:
        product_4 = Product.objects.get(id=4)
        print(f"\nProduct ID 4: {product_4.name}")
        print(f"SKU: {product_4.sku}")
        print(f"Price: {product_4.price}")
        print(f"Stock: {product_4.stock}")
        
        # Check variants for product 4
        variants_4 = ProductVariant.objects.filter(product=product_4)
        print(f"Variants for product 4: {variants_4.count()}")
        
        for variant in variants_4:
            print(f"  - Variant ID: {variant.id}, SKU: {variant.sku}")
            print(f"    Price: {variant.price}, Additional Price: {variant.additional_price}")
            print(f"    Stock: {variant.stock}, Active: {variant.is_active}")
            print(f"    Status: {variant.status}")
            attributes = variant.attributes.all()
            print(f"    Attributes: {[str(attr) for attr in attributes]}")
        
        # Check images for product 4
        images_4 = ProductImage.objects.filter(product=product_4)
        print(f"Images for product 4: {images_4.count()}")
        for img in images_4:
            print(f"  - Image: {img.image[:50]}...")
            print(f"    Alt text: {img.alt_text}")
            print(f"    Order: {img.order}")
            if img.variant:
                print(f"    Associated with variant: {img.variant.id}")
        
        # Check reviews for product 4
        reviews_4 = ProductReview.objects.filter(product=product_4)
        print(f"Reviews for product 4: {reviews_4.count()}")
        for review in reviews_4:
            print(f"  - Rating: {review.rating}, User: {review.user}")
            print(f"    Comment: {review.comment[:100]}...")
            print(f"    Published: {review.is_published}")
            
    except Product.DoesNotExist:
        print("Product with ID 4 not found")
    
    print("\n=== OVERALL VARIANT STATISTICS ===")
    
    # Check all variants
    all_variants = ProductVariant.objects.all()
    print(f"Total variants in system: {all_variants.count()}")
    
    active_variants = ProductVariant.objects.filter(is_active=True)
    print(f"Active variants: {active_variants.count()}")
    
    approved_variants = ProductVariant.objects.filter(status='approved')
    print(f"Approved variants: {approved_variants.count()}")
    
    # Check attributes
    attributes = ProductAttribute.objects.all()
    print(f"Total attributes: {attributes.count()}")
    for attr in attributes:
        values = ProductAttributeValue.objects.filter(attribute=attr)
        print(f"  - {attr.name}: {values.count()} values")
    
    # Check products with variants
    products_with_variants = Product.objects.filter(variants__isnull=False).distinct()
    print(f"Products with variants: {products_with_variants.count()}")
    
    # Check products without variants
    products_without_variants = Product.objects.filter(variants__isnull=True)
    print(f"Products without variants: {products_without_variants.count()}")
    
    # Sample some products without variants
    print("\nSample products without variants:")
    for product in products_without_variants[:5]:
        print(f"  - ID: {product.id}, Name: {product.name}")
    
    print("\n=== PRODUCT IMAGES STATISTICS ===")
    total_images = ProductImage.objects.all().count()
    print(f"Total product images: {total_images}")
    
    variant_images = ProductImage.objects.filter(variant__isnull=False).count()
    print(f"Images associated with variants: {variant_images}")
    
    product_only_images = ProductImage.objects.filter(variant__isnull=True).count()
    print(f"Images associated with products only: {product_only_images}")
    
    print("\n=== PRODUCT REVIEWS STATISTICS ===")
    total_reviews = ProductReview.objects.all().count()
    print(f"Total product reviews: {total_reviews}")
    
    published_reviews = ProductReview.objects.filter(is_published=True).count()
    print(f"Published reviews: {published_reviews}")

if __name__ == "__main__":
    check_variant_data()