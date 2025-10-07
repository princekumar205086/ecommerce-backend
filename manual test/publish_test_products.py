#!/usr/bin/env python3
"""
Script to publish the test products so they appear in public API.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product

def publish_test_products():
    """
    Publish test products so they appear in public APIs.
    """
    print("Publishing test products...")
    
    # Find and publish test products
    test_products = Product.objects.filter(name__icontains='Test Optimized')
    
    for product in test_products:
        product.status = 'published'
        product.is_publish = True
        product.save()
        print(f"✅ Published: {product.name}")
    
    print(f"\nPublished {test_products.count()} test products")
    
    # Show all published products
    published_products = Product.objects.filter(status='published', is_publish=True)
    print(f"\nTotal published products: {published_products.count()}")

if __name__ == "__main__":
    publish_test_products()
