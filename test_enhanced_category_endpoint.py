#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import Client
from products.models import ProductCategory, Product
import json

# Create test client
client = Client()

print("🔍 Testing Enhanced Category Products Endpoint...")
print("=" * 60)

# First, let's check what categories exist and which ones have children
categories = ProductCategory.objects.filter(is_publish=True).select_related('parent')

print("\n📂 Available Categories:")
for cat in categories[:10]:  # Show first 10
    parent_info = f" (Parent: {cat.parent.name})" if cat.parent else ""
    children_count = ProductCategory.objects.filter(parent=cat).count()
    children_info = f" [Has {children_count} subcategories]" if children_count > 0 else ""
    print(f"   ID: {cat.id} | Name: {cat.name}{parent_info}{children_info}")

# Find a category that has subcategories (parent category)
parent_categories = ProductCategory.objects.filter(
    is_publish=True,
    productcategory__isnull=False  # Has children
).distinct()

if parent_categories.exists():
    test_category = parent_categories.first()
    print(f"\n🎯 Testing with parent category: {test_category.name} (ID: {test_category.id})")
    
    # Get subcategories
    subcategories = ProductCategory.objects.filter(parent=test_category, is_publish=True)
    print(f"   Subcategories ({subcategories.count()}):")
    for subcat in subcategories:
        products_count = Product.objects.filter(category=subcat, is_publish=True).count()
        print(f"     - {subcat.name} (ID: {subcat.id}) - {products_count} products")
    
    # Test the enhanced endpoint
    url = f'/api/public/products/categories/{test_category.id}/products/'
    print(f"\n🚀 Testing URL: {url}")
    
    response = client.get(url)
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ SUCCESS!")
        print(f"   📊 Response Structure:")
        print(f"      - Category: {data.get('category', {}).get('name')} (Parent: {data.get('category', {}).get('is_parent')})")
        print(f"      - Subcategories: {len(data.get('subcategories', []))}")
        print(f"      - Total Products: {data.get('count', 0)}")
        print(f"      - Products in Results: {len(data.get('results', []))}")
        
        # Show subcategory details
        if data.get('subcategories'):
            print(f"   📂 Subcategory Details:")
            for subcat in data['subcategories']:
                print(f"      - {subcat['name']} (ID: {subcat['id']}) - {subcat['product_count']} products")
        
        # Show first few products
        print(f"   📦 First 3 Products:")
        for i, product in enumerate(data.get('results', [])[:3]):
            print(f"      {i+1}. {product['name']} (Category: {product['category']['name']})")
    
    else:
        print(f"   ❌ FAILED: {response.status_code}")
        print(f"   Error: {response.content.decode()[:200]}")

else:
    # Test with any category that has products
    categories_with_products = ProductCategory.objects.filter(
        is_publish=True,
        products__isnull=False
    ).distinct()
    
    if categories_with_products.exists():
        test_category = categories_with_products.first()
        print(f"\n🎯 Testing with category: {test_category.name} (ID: {test_category.id})")
        
        # Test the enhanced endpoint
        url = f'/api/public/products/categories/{test_category.id}/products/'
        print(f"\n🚀 Testing URL: {url}")
        
        response = client.get(url)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS!")
            print(f"   📊 Response Structure:")
            print(f"      - Category: {data.get('category', {}).get('name')}")
            print(f"      - Subcategories: {len(data.get('subcategories', []))}")
            print(f"      - Total Products: {data.get('count', 0)}")
        else:
            print(f"   ❌ FAILED: {response.status_code}")

print("\n" + "=" * 60)
print("Enhanced Category Products Test Complete!")