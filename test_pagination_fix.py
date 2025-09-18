#!/usr/bin/env python3
"""
Test script to verify pagination shows 12 products per page
Tests all product endpoints with pagination parameters
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
from django.conf import settings

def test_pagination_settings():
    """Test Django settings for pagination"""
    print("🔧 TESTING PAGINATION SETTINGS")
    print("=" * 50)
    
    page_size = settings.REST_FRAMEWORK.get('PAGE_SIZE', 'Not set')
    pagination_class = settings.REST_FRAMEWORK.get('DEFAULT_PAGINATION_CLASS', 'Not set')
    
    print(f"   📊 DRF PAGE_SIZE: {page_size}")
    print(f"   📋 Pagination Class: {pagination_class}")
    
    if page_size == 12:
        print("   ✅ Page size correctly set to 12")
    else:
        print(f"   ❌ Expected 12, got {page_size}")

def test_product_endpoints_pagination():
    """Test various product endpoints with pagination"""
    print("\n\n🧪 TESTING PRODUCT ENDPOINTS PAGINATION")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000/api/public/products"
    
    endpoints_to_test = [
        {
            "name": "All Products",
            "url": f"{base_url}/",
            "expect_pagination": True
        },
        {
            "name": "Medicine Products",
            "url": f"{base_url}/types/medicine/products/",
            "expect_pagination": True
        },
        {
            "name": "Equipment Products", 
            "url": f"{base_url}/types/equipment/products/",
            "expect_pagination": True
        },
        {
            "name": "Search Products",
            "url": f"{base_url}/search/",
            "params": {"q": "tablet"},
            "expect_pagination": True
        },
        {
            "name": "Featured Products",
            "url": f"{base_url}/featured/",
            "expect_pagination": True
        },
        {
            "name": "Categories (with page param)",
            "url": f"{base_url}/../categories/",
            "expect_pagination": True
        },
        {
            "name": "Brands (with page param)",
            "url": f"{base_url}/../brands/",
            "expect_pagination": True
        }
    ]
    
    for endpoint in endpoints_to_test:
        test_endpoint_pagination(endpoint)

def test_endpoint_pagination(endpoint_config):
    """Test a specific endpoint for pagination"""
    print(f"\n📡 Testing: {endpoint_config['name']}")
    print("-" * 40)
    
    url = endpoint_config['url']
    params = endpoint_config.get('params', {})
    
    try:
        # Test without page parameter
        print(f"   🔗 URL: {url}")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            count = data.get('count', 'N/A')
            next_page = data.get('next')
            
            print(f"   📊 Status: {response.status_code} ✅")
            print(f"   📈 Results returned: {len(results)}")
            print(f"   🔢 Total count: {count}")
            print(f"   ➡️  Next page: {'Yes' if next_page else 'No'}")
            
            # Check if we got 12 or fewer results (for small datasets)
            if len(results) <= 12:
                print(f"   ✅ Pagination working: Got {len(results)} results (≤12)")
            else:
                print(f"   ❌ Pagination issue: Got {len(results)} results (>12)")
            
            # Test with specific page parameter
            if next_page:
                test_specific_page(url, params, 2)
                
        else:
            print(f"   📊 Status: {response.status_code} ❌")
            print(f"   📄 Error: {response.text[:100]}...")
            
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Connection failed - Make sure Django server is running")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def test_specific_page(base_url, base_params, page_num):
    """Test a specific page number"""
    print(f"   🔄 Testing page {page_num}...")
    
    try:
        params = base_params.copy()
        params['page'] = page_num
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"      📄 Page {page_num}: {len(results)} results")
            
            if len(results) <= 12:
                print(f"      ✅ Page {page_num} pagination correct")
            else:
                print(f"      ❌ Page {page_num} has {len(results)} results (>12)")
        else:
            print(f"      ❌ Page {page_num} failed: {response.status_code}")
            
    except Exception as e:
        print(f"      ❌ Page {page_num} error: {str(e)}")

def test_search_pagination():
    """Specifically test search endpoint pagination"""
    print(f"\n\n🔍 TESTING SEARCH ENDPOINT PAGINATION")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000/api/public/products/search/"
    
    test_cases = [
        {"q": "medicine", "description": "Search for 'medicine'"},
        {"q": "tablet", "description": "Search for 'tablet'"},
        {"q": "equipment", "description": "Search for 'equipment'"},
        {"q": "paracetamol", "description": "Search for 'paracetamol'"}
    ]
    
    for test_case in test_cases:
        print(f"\n📋 {test_case['description']}")
        print("-" * 30)
        
        try:
            # Test default pagination (should be 12)
            response = requests.get(base_url, params=test_case, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pagination = data.get('pagination', {})
                results = data.get('results', [])
                
                print(f"   📊 Results: {len(results)}")
                print(f"   📄 Page: {pagination.get('page', 'N/A')}")
                print(f"   📏 Page size: {pagination.get('page_size', 'N/A')}")
                print(f"   📈 Total: {pagination.get('total_count', 'N/A')}")
                
                expected_page_size = pagination.get('page_size', 0)
                if expected_page_size == 12:
                    print(f"   ✅ Search pagination set to 12")
                else:
                    print(f"   ❌ Expected 12, got {expected_page_size}")
                    
                if len(results) <= 12:
                    print(f"   ✅ Results count correct: {len(results)} ≤ 12")
                else:
                    print(f"   ❌ Too many results: {len(results)} > 12")
                    
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_custom_page_size():
    """Test custom page_size parameter"""
    print(f"\n\n⚙️  TESTING CUSTOM PAGE SIZE")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000/api/public/products/search/"
    
    custom_sizes = [5, 8, 15, 25]
    
    for size in custom_sizes:
        print(f"\n📏 Testing page_size={size}")
        print("-" * 30)
        
        try:
            params = {"q": "medicine", "page_size": size}
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pagination = data.get('pagination', {})
                results = data.get('results', [])
                
                actual_size = pagination.get('page_size', 0)
                print(f"   📏 Requested: {size}, Got: {actual_size}")
                print(f"   📊 Results: {len(results)}")
                
                if actual_size == size and len(results) <= size:
                    print(f"   ✅ Custom page size working")
                else:
                    print(f"   ❌ Custom page size not working properly")
                    
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def generate_pagination_examples():
    """Generate example URLs for testing pagination"""
    print(f"\n\n📋 PAGINATION EXAMPLE URLS")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000/api/public/products"
    
    examples = [
        {"url": f"{base_url}/", "description": "All products (page 1, 12 items)"},
        {"url": f"{base_url}/?page=2", "description": "All products (page 2, 12 items)"},
        {"url": f"{base_url}/types/medicine/products/", "description": "Medicine products (page 1, 12 items)"},
        {"url": f"{base_url}/types/medicine/products/?page=2", "description": "Medicine products (page 2, 12 items)"},
        {"url": f"{base_url}/search/?q=tablet", "description": "Search tablets (page 1, 12 items)"},
        {"url": f"{base_url}/search/?q=tablet&page=2", "description": "Search tablets (page 2, 12 items)"},
        {"url": f"{base_url}/search/?q=medicine&page_size=6", "description": "Search medicine (custom 6 items)"},
        {"url": f"{base_url}/../categories/?page=1", "description": "Categories with pagination"},
        {"url": f"{base_url}/../brands/?page=1", "description": "Brands with pagination"}
    ]
    
    for example in examples:
        print(f"\n📝 {example['description']}:")
        print(f"   curl -X GET '{example['url']}'")

if __name__ == "__main__":
    print(f"🚀 PAGINATION TEST SUITE")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run all tests
    test_pagination_settings()
    test_product_endpoints_pagination()
    test_search_pagination() 
    test_custom_page_size()
    generate_pagination_examples()
    
    print(f"\n\n✅ PAGINATION TEST SUITE COMPLETED")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"\n💡 TIP: Use ?page=2, ?page=3 etc. to test pagination")
    print(f"💡 TIP: Use ?page_size=X for custom page sizes (search endpoint)")