#!/usr/bin/env python3
"""
Test script to verify the main products endpoint pagination behavior:
- Without page param: Returns ALL products
- With page param: Returns 12 products per page
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

def test_main_products_endpoint():
    """Test the main products endpoint with and without page parameter"""
    print("🧪 TESTING MAIN PRODUCTS ENDPOINT PAGINATION")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000/api/public/products/products/"
    
    # Test 1: Without page parameter - should return ALL products
    print(f"\n📋 Test 1: WITHOUT page parameter")
    print("-" * 40)
    
    try:
        response = requests.get(base_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            count = data.get('count', 'N/A')
            next_page = data.get('next')
            
            print(f"   🔗 URL: {base_url}")
            print(f"   📊 Status: {response.status_code} ✅")
            print(f"   📈 Results returned: {len(results)}")
            print(f"   🔢 Total count: {count}")
            print(f"   ➡️  Next page: {'Yes' if next_page else 'No'}")
            
            # Should return ALL products (no pagination)
            total_products = Product.objects.filter(status='published', is_publish=True).count()
            print(f"   📊 Expected total: {total_products}")
            
            if len(results) == total_products and not next_page:
                print(f"   ✅ CORRECT: Returns all {total_products} products without pagination")
            else:
                print(f"   ❌ WRONG: Should return all {total_products} products, got {len(results)}")
                
        else:
            print(f"   📊 Status: {response.status_code} ❌")
            print(f"   📄 Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: With page parameter - should return 12 products
    print(f"\n📋 Test 2: WITH page parameter (page=1)")
    print("-" * 40)
    
    try:
        url_with_page = f"{base_url}?page=1"
        response = requests.get(url_with_page, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            count = data.get('count', 'N/A')
            next_page = data.get('next')
            
            print(f"   🔗 URL: {url_with_page}")
            print(f"   📊 Status: {response.status_code} ✅")
            print(f"   📈 Results returned: {len(results)}")
            print(f"   🔢 Total count: {count}")
            print(f"   ➡️  Next page: {'Yes' if next_page else 'No'}")
            
            # Should return exactly 12 products (with pagination)
            if len(results) <= 12 and next_page:
                print(f"   ✅ CORRECT: Returns {len(results)} products with pagination")
            else:
                print(f"   ❌ WRONG: Should return ≤12 products with next page, got {len(results)}")
                
        else:
            print(f"   📊 Status: {response.status_code} ❌")
            print(f"   📄 Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: With page=2 - should return next 12 products
    print(f"\n📋 Test 3: WITH page parameter (page=2)")
    print("-" * 40)
    
    try:
        url_page2 = f"{base_url}?page=2"
        response = requests.get(url_page2, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            previous_page = data.get('previous')
            
            print(f"   🔗 URL: {url_page2}")
            print(f"   📊 Status: {response.status_code} ✅")
            print(f"   📈 Results returned: {len(results)}")
            print(f"   ⬅️  Previous page: {'Yes' if previous_page else 'No'}")
            
            if len(results) <= 12 and previous_page:
                print(f"   ✅ CORRECT: Page 2 returns {len(results)} products with previous link")
            else:
                print(f"   ❌ WRONG: Page 2 should have ≤12 products with previous link")
                
        else:
            print(f"   📊 Status: {response.status_code} ❌")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def test_with_filters():
    """Test pagination behavior with filters"""
    print(f"\n\n🔍 TESTING WITH FILTERS")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000/api/public/products/products/"
    
    # Test with product_type filter
    test_cases = [
        {
            "name": "Filter by medicine (no page)",
            "params": {"product_type": "medicine"},
            "should_paginate": False
        },
        {
            "name": "Filter by medicine (with page)",
            "params": {"product_type": "medicine", "page": "1"},
            "should_paginate": True
        },
        {
            "name": "Search products (no page)",
            "params": {"search": "tablet"},
            "should_paginate": False
        },
        {
            "name": "Search products (with page)",
            "params": {"search": "tablet", "page": "1"},
            "should_paginate": True
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}")
        print("-" * 40)
        
        try:
            response = requests.get(base_url, params=test_case['params'], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                next_page = data.get('next')
                
                print(f"   📊 Results: {len(results)}")
                print(f"   ➡️  Next: {'Yes' if next_page else 'No'}")
                
                if test_case['should_paginate']:
                    if len(results) <= 12:
                        print(f"   ✅ CORRECT: Pagination working")
                    else:
                        print(f"   ❌ WRONG: Should be paginated (≤12 items)")
                else:
                    if not next_page:
                        print(f"   ✅ CORRECT: All results returned")
                    else:
                        print(f"   ❌ WRONG: Should return all results")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def generate_curl_examples():
    """Generate curl examples for testing"""
    print(f"\n\n📋 CURL EXAMPLES")
    print("=" * 60)
    
    examples = [
        {
            "description": "Get ALL products (no pagination)",
            "curl": "curl -X GET 'http://127.0.0.1:8000/api/public/products/products/'"
        },
        {
            "description": "Get first 12 products (with pagination)",
            "curl": "curl -X GET 'http://127.0.0.1:8000/api/public/products/products/?page=1'"
        },
        {
            "description": "Get second 12 products",
            "curl": "curl -X GET 'http://127.0.0.1:8000/api/public/products/products/?page=2'"
        },
        {
            "description": "Filter medicine products (all)",
            "curl": "curl -X GET 'http://127.0.0.1:8000/api/public/products/products/?product_type=medicine'"
        },
        {
            "description": "Filter medicine products (paginated)",
            "curl": "curl -X GET 'http://127.0.0.1:8000/api/public/products/products/?product_type=medicine&page=1'"
        }
    ]
    
    for example in examples:
        print(f"\n📝 {example['description']}:")
        print(f"   {example['curl']}")

if __name__ == "__main__":
    print(f"🚀 MAIN PRODUCTS ENDPOINT TEST SUITE")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run all tests
    test_main_products_endpoint()
    test_with_filters()
    generate_curl_examples()
    
    print(f"\n\n✅ TEST SUITE COMPLETED")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)