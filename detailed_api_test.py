#!/usr/bin/env python3
"""
Detailed Public API Test with Data Verification
"""

import requests
import json

def test_detailed_functionality():
    base_url = 'http://127.0.0.1:8000'
    
    print("🔍 Testing Detailed Public API Functionality...")
    print("=" * 60)
    
    # Test public product search with filters
    print("\n1. Testing Product Search with Filters")
    search_response = requests.get(f"{base_url}/api/public/products/search/", params={
        'q': 'test',
        'page': 1,
        'page_size': 10,
        'sort_by': '-created_at'
    })
    
    if search_response.status_code == 200:
        search_data = search_response.json()
        print(f"✅ Search endpoint working")
        print(f"   📄 Results structure: {list(search_data.keys())}")
        if 'pagination' in search_data:
            print(f"   📊 Pagination: {search_data['pagination']}")
        if 'filters' in search_data:
            filters = search_data['filters']
            print(f"   🏷️  Available categories: {len(filters.get('categories', []))}")
            print(f"   🏢 Available brands: {len(filters.get('brands', []))}")
            print(f"   📦 Product types: {filters.get('product_types', [])}")
    else:
        print(f"❌ Search endpoint failed: {search_response.status_code}")
    
    # Test categories
    print("\n2. Testing Product Categories")
    categories_response = requests.get(f"{base_url}/api/public/products/categories/")
    if categories_response.status_code == 200:
        categories = categories_response.json()
        print(f"✅ Categories endpoint working")
        print(f"   📊 Total categories: {len(categories)}")
        if categories and len(categories) > 0:
            print(f"   📝 Sample category: {categories[0] if isinstance(categories, list) else 'Dict response'}")
    else:
        print(f"❌ Categories endpoint failed: {categories_response.status_code}")
    
    # Test brands
    print("\n3. Testing Brands")
    brands_response = requests.get(f"{base_url}/api/public/products/brands/")
    if brands_response.status_code == 200:
        brands = brands_response.json()
        print(f"✅ Brands endpoint working")
        print(f"   📊 Total brands: {len(brands)}")
        if brands and len(brands) > 0:
            print(f"   📝 Sample brand: {brands[0] if isinstance(brands, list) else 'Dict response'}")
    else:
        print(f"❌ Brands endpoint failed: {brands_response.status_code}")
    
    # Test products
    print("\n4. Testing Products")
    products_response = requests.get(f"{base_url}/api/public/products/products/")
    if products_response.status_code == 200:
        products = products_response.json()
        print(f"✅ Products endpoint working")
        print(f"   📊 Total products: {len(products)}")
        if products and len(products) > 0 and isinstance(products, list):
            product = products[0]
            print(f"   📝 Sample product: {product.get('name', 'No name')}")
            
            # Test individual product detail
            product_id = product.get('id')
            if product_id:
                detail_response = requests.get(f"{base_url}/api/public/products/products/{product_id}/")
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    print(f"   ✅ Product detail working")
                    print(f"      📊 Detail keys: {list(detail_data.keys())}")
                    if 'review_stats' in detail_data:
                        print(f"      ⭐ Review stats: {detail_data['review_stats']}")
                else:
                    print(f"   ❌ Product detail failed: {detail_response.status_code}")
        else:
            print("   📝 No products found or response is not a list")
    else:
        print(f"❌ Products endpoint failed: {products_response.status_code}")
    
    # Test CMS endpoints
    print("\n5. Testing CMS Endpoints")
    cms_endpoints = {
        'Pages': '/api/cms/pages/',
        'Banners': '/api/cms/banners/',
        'Blog Posts': '/api/cms/blog/',
        'Blog Categories': '/api/cms/blog/categories/',
        'Blog Tags': '/api/cms/blog/tags/',
        'FAQs': '/api/cms/faqs/',
        'Testimonials': '/api/cms/testimonials/',
    }
    
    for name, endpoint in cms_endpoints.items():
        response = requests.get(f"{base_url}{endpoint}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {name}: {len(data)} items")
        else:
            print(f"   ❌ {name}: Status {response.status_code}")
    
    # Test analytics tracking
    print("\n6. Testing Analytics Tracking")
    track_response = requests.post(f"{base_url}/api/analytics/track/", json={
        'event_type': 'page_view',
        'path': '/test-path',
        'data': {'test': True}
    })
    
    if track_response.status_code in [200, 201]:
        print("✅ Analytics tracking working")
    else:
        print(f"❌ Analytics tracking failed: {track_response.status_code}")
    
    # Test API documentation
    print("\n7. Testing API Documentation")
    swagger_response = requests.get(f"{base_url}/swagger.json")
    if swagger_response.status_code == 200:
        swagger_data = swagger_response.json()
        print("✅ Swagger JSON available")
        print(f"   📝 API Title: {swagger_data.get('info', {}).get('title', 'Unknown')}")
        print(f"   📊 Number of paths: {len(swagger_data.get('paths', {}))}")
    else:
        print(f"❌ Swagger JSON failed: {swagger_response.status_code}")
    
    print("\n" + "=" * 60)
    print("✨ Detailed testing completed!")

if __name__ == "__main__":
    test_detailed_functionality()