#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.urls import reverse
from products.models import Product

# Get the first product
product = Product.objects.first()
if product:
    print(f"Product ID: {product.id}")
    print(f"Product Name: {product.name}")
    
    # Get the correct URL pattern
    try:
        detail_url = reverse('products:product-detail', kwargs={'pk': product.id})
        print(f"Correct detail URL: {detail_url}")
    except Exception as e:
        print(f"URL reverse error: {e}")
        
    # Test various URL patterns
    test_urls = [
        f'/api/products/products/{product.id}/',
        f'/api/products/{product.id}/',
        f'/products/{product.id}/',
        f'/api/products/products/{product.id}',
        f'/api/products/{product.id}',
    ]
    
    print("\nTesting URL patterns:")
    for url in test_urls:
        print(f"  {url}")
else:
    print("No products found in database")