#!/usr/bin/env python3
"""
Debug script to test product detail view variant issue
"""
import os
import django
import requests
import json

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductVariant, ProductAttributeValue
from products.serializers import PublicProductSerializer

def debug_product_detail():
    """Debug product detail view variant issue"""
    
    print("=== Debugging Product Detail View ===\n")
    
    # First, let's check which products have variants in the database
    print("1. Products with variants in database:")
    products_with_variants = Product.objects.filter(variants__isnull=False).distinct()
    for product in products_with_variants:
        variant_count = product.variants.count()
        approved_variant_count = product.variants.filter(status__in=['approved', 'published']).count()
        print(f"   Product {product.id}: {product.name[:50]}... - {variant_count} variants ({approved_variant_count} approved)")
    
    if not products_with_variants.exists():
        print("   No products have variants!")
        return
    
    # Test with first product that has variants
    test_product = products_with_variants.first()
    print(f"\n2. Testing with Product {test_product.id}: {test_product.name}")
    
    # Test direct serializer
    print("\n3. Direct serializer test (simulating what API should return):")
    serializer = PublicProductSerializer(test_product)
    data = serializer.data
    print(f"   Variants count in serializer: {len(data.get('variants', []))}")
    print(f"   Images count in serializer: {len(data.get('images', []))}")
    print(f"   Reviews count in serializer: {len(data.get('reviews', []))}")
    
    if data.get('variants'):
        print("   First variant:")
        variant = data['variants'][0]
        print(f"      ID: {variant.get('id')}")
        print(f"      SKU: {variant.get('sku')}")
        print(f"      Price: {variant.get('price')}")
        print(f"      Attributes: {len(variant.get('attributes', []))}")
    
    # Test API endpoints
    base_url = "http://127.0.0.1:8000"
    
    print(f"\n4. Testing API endpoints for product {test_product.id}:")
    
    # Test list endpoint
    try:
        list_response = requests.get(f"{base_url}/api/products/", timeout=10)
        if list_response.status_code == 200:
            list_data = list_response.json()
            print(f"   List endpoint status: {list_response.status_code}")
            print(f"   Products returned: {len(list_data.get('results', []))}")
            
            # Find our test product in list
            our_product = None
            for product in list_data.get('results', []):
                if product['id'] == test_product.id:
                    our_product = product
                    break
            
            if our_product:
                print(f"   Our product in list - Variants: {len(our_product.get('variants', []))}")
                print(f"   Our product in list - Images: {len(our_product.get('images', []))}")
                print(f"   Our product in list - Reviews: {len(our_product.get('reviews', []))}")
            else:
                print(f"   Our product (ID {test_product.id}) not found in list!")
        else:
            print(f"   List endpoint failed: {list_response.status_code}")
    except Exception as e:
        print(f"   List endpoint error: {e}")
    
    # Test detail endpoint
    try:
        detail_response = requests.get(f"{base_url}/api/products/{test_product.id}/", timeout=10)
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            print(f"   Detail endpoint status: {detail_response.status_code}")
            print(f"   Detail variants: {len(detail_data.get('variants', []))}")
            print(f"   Detail images: {len(detail_data.get('images', []))}")
            print(f"   Detail reviews: {len(detail_data.get('reviews', []))}")
            
            if detail_data.get('variants'):
                print("   First variant in detail:")
                variant = detail_data['variants'][0]
                print(f"      ID: {variant.get('id')}")
                print(f"      SKU: {variant.get('sku')}")
                print(f"      Price: {variant.get('price')}")
                print(f"      Attributes: {len(variant.get('attributes', []))}")
        else:
            print(f"   Detail endpoint failed: {detail_response.status_code}")
            print(f"   Response: {detail_response.text}")
    except Exception as e:
        print(f"   Detail endpoint error: {e}")
    
    # Check database state for this product
    print(f"\n5. Database state for product {test_product.id}:")
    variants = ProductVariant.objects.filter(product=test_product)
    print(f"   Total variants: {variants.count()}")
    
    for variant in variants:
        print(f"   Variant {variant.id}: status={variant.status}, sku={variant.sku}")
        attr_count = variant.attributes.count()
        print(f"      Attributes: {attr_count}")
        if attr_count > 0:
            for attr_val in variant.attributes.all()[:3]:  # Show first 3
                print(f"         {attr_val.attribute.name}: {attr_val.value}")

if __name__ == "__main__":
    debug_product_detail()