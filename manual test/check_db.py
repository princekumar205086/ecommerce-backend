#!/usr/bin/env python
"""
Quick database check script
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductVariant

def check_database():
    total_products = Product.objects.count()
    print(f"Total products: {total_products}")
    
    if total_products > 0:
        statuses = set(Product.objects.values_list('status', flat=True))
        print(f"Product statuses: {statuses}")
        
        for status in statuses:
            count = Product.objects.filter(status=status).count()
            print(f"  {status}: {count} products")
            
        # Show first few products
        print("\nFirst 5 products:")
        for product in Product.objects.all()[:5]:
            print(f"  - {product.name} ({product.status})")
            
        # Check variants
        total_variants = ProductVariant.objects.count()
        print(f"\nTotal variants: {total_variants}")
        
        if total_variants > 0:
            variant_statuses = set(ProductVariant.objects.values_list('status', flat=True))
            print(f"Variant statuses: {variant_statuses}")
            
    else:
        print("No products found in database")

if __name__ == '__main__':
    check_database()