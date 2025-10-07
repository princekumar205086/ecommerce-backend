#!/usr/bin/env python3
"""
Script to check which products exist and their variant status
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductVariant

def check_products():
    print("=== CHECKING EXISTING PRODUCTS ===\n")
    
    # Check if product 4 exists at all
    try:
        product_4 = Product.objects.get(id=4)
        print(f"Product 4 found: {product_4.name}")
        print(f"Published: {product_4.is_publish}")
        print(f"Status: {product_4.status}")
    except Product.DoesNotExist:
        print("Product with ID 4 does not exist")
    
    # Check published products
    published = Product.objects.filter(is_publish=True, status='published')[:10]
    print(f"\nFirst 10 published products:")
    for product in published:
        variants_count = product.variants.count()
        print(f"ID: {product.id}, Name: {product.name}, Variants: {variants_count}")
    
    # Check products with variants
    products_with_variants = Product.objects.filter(variants__isnull=False).distinct()[:10]
    print(f"\nFirst 10 products with variants:")
    for product in products_with_variants:
        variants = product.variants.all()
        print(f"ID: {product.id}, Name: {product.name}")
        for variant in variants[:3]:  # Show first 3 variants
            print(f"  - Variant {variant.id}: Status={variant.status}, Active={variant.is_active}")
    
    # Check variant status distribution
    print(f"\n=== VARIANT STATUS DISTRIBUTION ===")
    statuses = ProductVariant.objects.values('status').distinct()
    for status in statuses:
        count = ProductVariant.objects.filter(status=status['status']).count()
        print(f"{status['status']}: {count}")

if __name__ == "__main__":
    check_products()