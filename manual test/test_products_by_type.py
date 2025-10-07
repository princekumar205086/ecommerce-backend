#!/usr/bin/env python3
"""
Test script for the new Products by Type endpoint
Tests all product types: medicine, equipment, pathology
"""

import os
import django
import requests
import json
from datetime import datetime

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product

def test_local_endpoint():
    """Test the endpoint locally using Django models"""
    print("🧪 TESTING PRODUCTS BY TYPE ENDPOINT (Local)")
    print("=" * 60)
    
    # Test each product type
    product_types = ['medicine', 'equipment', 'pathology']
    
    for product_type in product_types:
        print(f"\n📋 Testing product_type: {product_type}")
        print("-" * 40)
        
        # Query products locally
        products = Product.objects.filter(
            product_type=product_type,
            status='published',
            is_publish=True
        ).select_related('category', 'brand')
        
        print(f"   📊 Total {product_type} products: {products.count()}")
        
        if products.exists():
            print(f"   📝 Sample products:")
            for i, product in enumerate(products[:3], 1):
                print(f"      {i}. {product.name} - ₹{product.price}")
                print(f"         Category: {product.category.name}")
                print(f"         Brand: {product.brand.name if product.brand else 'No Brand'}")
        else:
            print(f"   ⚠️  No {product_type} products found")

def test_api_endpoint():
    """Test the API endpoint via HTTP requests"""
    print("\n\n🌐 TESTING PRODUCTS BY TYPE API ENDPOINT (HTTP)")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000/api/public/products/types"
    product_types = ['medicine', 'equipment', 'pathology']
    
    for product_type in product_types:
        print(f"\n📡 Testing API: {product_type}")
        print("-" * 40)
        
        url = f"{base_url}/{product_type}/products/"
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   🔗 URL: {url}")
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"   📈 Total products returned: {len(results)}")
                print(f"   🔢 Total count: {data.get('count', 'N/A')}")
                
                if results:
                    print(f"   📝 Sample products:")
                    for i, product in enumerate(results[:3], 1):
                        print(f"      {i}. {product.get('name', 'N/A')} - ₹{product.get('price', 'N/A')}")
                        print(f"         Type: {product.get('product_type', 'N/A')}")
                        print(f"         Category: {product.get('category', {}).get('name', 'N/A')}")
                else:
                    print(f"   ⚠️  No products returned")
                    
            elif response.status_code == 404:
                print(f"   ❌ Not Found - Check if URL pattern is correct")
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Connection failed - Make sure Django server is running")
            print(f"   💡 Run: python manage.py runserver")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_invalid_product_type():
    """Test with invalid product type"""
    print(f"\n\n🚫 TESTING INVALID PRODUCT TYPE")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000/api/public/products/types"
    invalid_types = ['invalid', 'food', 'electronics']
    
    for invalid_type in invalid_types:
        print(f"\n📡 Testing invalid type: {invalid_type}")
        print("-" * 40)
        
        url = f"{base_url}/{invalid_type}/products/"
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   🔗 URL: {url}")
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 404:
                print(f"   ✅ Correctly returned 404 for invalid type")
            else:
                print(f"   ⚠️  Expected 404 but got {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Connection failed - Make sure Django server is running")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_with_ordering():
    """Test endpoint with different ordering options"""
    print(f"\n\n📊 TESTING WITH ORDERING PARAMETERS")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000/api/public/products/types"
    ordering_options = ['price', '-price', 'name', '-name', 'created_at', '-created_at']
    
    for ordering in ordering_options:
        print(f"\n📈 Testing ordering: {ordering}")
        print("-" * 40)
        
        url = f"{base_url}/medicine/products/?ordering={ordering}"
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   🔗 URL: {url}")
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"   📈 Products returned: {len(results)}")
                
                if results:
                    print(f"   📝 First 3 products (ordered by {ordering}):")
                    for i, product in enumerate(results[:3], 1):
                        print(f"      {i}. {product.get('name', 'N/A')} - ₹{product.get('price', 'N/A')}")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Connection failed - Make sure Django server is running")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def generate_curl_examples():
    """Generate curl command examples for testing"""
    print(f"\n\n📋 CURL COMMAND EXAMPLES")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000/api/public/products/types"
    
    examples = [
        {
            "description": "Get all medicine products",
            "url": f"{base_url}/medicine/products/"
        },
        {
            "description": "Get all equipment products",
            "url": f"{base_url}/equipment/products/"
        },
        {
            "description": "Get all pathology products",
            "url": f"{base_url}/pathology/products/"
        },
        {
            "description": "Get medicine products ordered by price (low to high)",
            "url": f"{base_url}/medicine/products/?ordering=price"
        },
        {
            "description": "Get equipment products ordered by price (high to low)",
            "url": f"{base_url}/equipment/products/?ordering=-price"
        },
        {
            "description": "Get pathology products ordered by name",
            "url": f"{base_url}/pathology/products/?ordering=name"
        }
    ]
    
    for example in examples:
        print(f"\n📝 {example['description']}:")
        print(f"   curl -X GET '{example['url']}'")

if __name__ == "__main__":
    print(f"🚀 PRODUCTS BY TYPE ENDPOINT TEST SUITE")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run all tests
    test_local_endpoint()
    test_api_endpoint() 
    test_invalid_product_type()
    test_with_ordering()
    generate_curl_examples()
    
    print(f"\n\n✅ TEST SUITE COMPLETED")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
