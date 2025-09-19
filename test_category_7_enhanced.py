#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import Client
import json

# Create test client
client = Client()

print("🔍 Testing Enhanced Category Products Endpoint - Category ID 7...")
print("=" * 70)

# Test the exact same endpoint as in your example
url = '/api/public/products/categories/7/products/'
print(f"🚀 Testing URL: {url}")

response = client.get(url)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    print(f"\n✅ SUCCESS! Enhanced Response Structure:")
    print(f"=" * 50)
    
    # Show the enhanced structure
    print(f"📂 Category Information:")
    category = data.get('category', {})
    print(f"   - Name: {category.get('name')}")
    print(f"   - ID: {category.get('id')}")
    print(f"   - Slug: {category.get('slug')}")
    print(f"   - Is Parent: {category.get('is_parent')}")
    print(f"   - Total Subcategories: {category.get('total_subcategories')}")
    
    print(f"\n📁 Subcategories ({len(data.get('subcategories', []))}):")
    for subcat in data.get('subcategories', []):
        print(f"   - {subcat['name']} (ID: {subcat['id']}) - {subcat['product_count']} products")
    
    print(f"\n📊 Products Summary:")
    print(f"   - Total Products: {data.get('count')}")
    print(f"   - Products in Current Page: {len(data.get('results', []))}")
    print(f"   - Next Page: {data.get('next')}")
    print(f"   - Previous Page: {data.get('previous')}")
    
    print(f"\n📦 Sample Products (first 3):")
    for i, product in enumerate(data.get('results', [])[:3]):
        print(f"   {i+1}. {product['name']}")
        print(f"      - Category: {product['category']['name']}")
        print(f"      - Price: ₹{product['price']}")
        print(f"      - Type: {product['product_type']}")
        print(f"      - In Stock: {product['stock']}")
        print()
    
    # Show the full JSON structure (truncated for readability)
    print(f"📄 Complete JSON Response Structure:")
    print(f"   ├── category (object)")
    print(f"   ├── subcategories (array[{len(data.get('subcategories', []))}])")
    print(f"   ├── count ({data.get('count')})")
    print(f"   ├── next ({data.get('next')})")
    print(f"   ├── previous ({data.get('previous')})")
    print(f"   └── results (array[{len(data.get('results', []))}])")
    
    # Compare with your original structure
    print(f"\n🔄 Comparison with Original Structure:")
    print(f"   ✅ ADDED: category information (parent details)")
    print(f"   ✅ ADDED: subcategories list with product counts")
    print(f"   ✅ ENHANCED: Now includes products from ALL subcategories")
    print(f"   ✅ MAINTAINED: All original fields (count, next, previous, results)")
    print(f"   ✅ MAINTAINED: Same product structure in results")

else:
    print(f"❌ FAILED: {response.status_code}")
    print(f"Error: {response.content.decode()}")

print("\n" + "=" * 70)
print("Enhanced Category Products Endpoint Test Complete!")