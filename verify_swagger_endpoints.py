#!/usr/bin/env python3
"""
Verification script to test all public endpoints and confirm they're visible in Swagger.
"""

import os
import sys
import django
import requests
import json
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

BASE_URL = "http://127.0.0.1:8000"

def test_swagger_availability():
    """Test if Swagger UI is accessible"""
    print("🔍 Testing Swagger UI availability...")
    try:
        response = requests.get(f"{BASE_URL}/swagger/")
        if response.status_code == 200:
            print("✅ Swagger UI is accessible")
            return True
        else:
            print(f"❌ Swagger UI not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing Swagger UI: {e}")
        return False

def test_swagger_schema():
    """Test if Swagger schema includes all public endpoints"""
    print("\n🔍 Testing Swagger schema for public endpoints...")
    try:
        # Use requests session with proper headers
        session = requests.Session()
        session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        response = session.get(f"{BASE_URL}/swagger.json")
        if response.status_code == 200:
            # Handle binary content
            content = response.content.decode('utf-8') if isinstance(response.content, bytes) else response.text
            
            try:
                schema = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"First 200 chars of response: {content[:200]}")
                return False
                
            paths = schema.get('paths', {})
            
            # Expected public endpoints (without /api/ prefix as shown in Swagger)
            expected_endpoints = [
                # Products public endpoints (corrected paths)
                '/public/products/products/',
                '/public/products/categories/',
                '/public/products/brands/',
                '/public/products/search/',
                '/public/products/featured/',
                '/public/products/categories/{category_id}/products/',
                '/public/products/brands/{brand_id}/products/',
                '/public/products/products/{product_id}/reviews/',
                '/public/products/products/{id}/',
                
                # CMS public endpoints
                '/cms/pages/',
                '/cms/banners/',
                '/cms/blog/',
                '/cms/blog/categories/',
                '/cms/blog/tags/',
                '/cms/faqs/',
                '/cms/testimonials/',
                '/cms/pages/{slug}/',
                '/cms/blog/{slug}/',
            ]
            
            print(f"📊 Total paths in schema: {len(paths)}")
            print("\n🔍 Checking for public endpoints in schema:")
            
            found_endpoints = []
            missing_endpoints = []
            
            for endpoint in expected_endpoints:
                # Check for exact match or similar patterns
                found = False
                for path in paths.keys():
                    # Normalize path patterns for comparison
                    normalized_endpoint = endpoint.replace('{pk}', '{id}').replace('{category_id}', '{id}').replace('{brand_id}', '{id}').replace('{product_id}', '{id}').replace('{slug}', '{id}')
                    normalized_path = path.replace('{id}', '{id}')
                    
                    if endpoint == path or normalized_endpoint == normalized_path or endpoint in path:
                        found = True
                        found_endpoints.append(endpoint)
                        break
                
                if not found:
                    missing_endpoints.append(endpoint)
            
            print(f"\n✅ Found endpoints ({len(found_endpoints)}):")
            for endpoint in sorted(found_endpoints):
                print(f"  ✓ {endpoint}")
            
            if missing_endpoints:
                print(f"\n❌ Missing endpoints ({len(missing_endpoints)}):")
                for endpoint in sorted(missing_endpoints):
                    print(f"  ✗ {endpoint}")
            
            print(f"\n📊 Summary: {len(found_endpoints)}/{len(expected_endpoints)} expected endpoints found in Swagger")
            
            # Print public endpoints for reference
            print(f"\n📋 Public endpoints in Swagger schema:")
            public_paths = [path for path in sorted(paths.keys()) if '/public/' in path or '/cms/' in path]
            for path in public_paths:
                print(f"  • {path}")
            
            return len(missing_endpoints) == 0
            
        else:
            print(f"❌ Swagger schema not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing Swagger schema: {e}")
        return False

def test_public_endpoints():
    """Test actual public endpoints"""
    print("\n🔍 Testing actual public endpoints...")
    
    public_endpoints = [
        # Products (corrected paths)
        ("/api/public/products/products/", "Products List"),
        ("/api/public/products/categories/", "Categories List"),
        ("/api/public/products/brands/", "Brands List"),
        ("/api/public/products/search/?q=test", "Product Search"),
        ("/api/public/products/featured/", "Featured Products"),
        
        # CMS
        ("/api/cms/pages/", "Pages List"),
        ("/api/cms/banners/", "Banners List"),
        ("/api/cms/blog/", "Blog Posts List"),
        ("/api/cms/blog/categories/", "Blog Categories List"),
        ("/api/cms/blog/tags/", "Blog Tags List"),
        ("/api/cms/faqs/", "FAQs List"),
        ("/api/cms/testimonials/", "Testimonials List"),
    ]
    
    successful = 0
    total = len(public_endpoints)
    
    for endpoint, name in public_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: {response.status_code} - {len(data.get('results', data) if isinstance(data, dict) else data)} items")
                successful += 1
            else:
                print(f"❌ {name}: {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
    
    print(f"\n📊 Endpoint Test Summary: {successful}/{total} endpoints working")
    return successful == total

def main():
    """Main verification function"""
    print("🚀 Starting Swagger and Public Endpoints Verification")
    print("=" * 60)
    
    # Test Swagger availability
    swagger_ok = test_swagger_availability()
    
    # Test Swagger schema
    schema_ok = test_swagger_schema()
    
    # Test actual endpoints
    endpoints_ok = test_public_endpoints()
    
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Swagger UI Accessible: {'✅' if swagger_ok else '❌'}")
    print(f"All Endpoints in Schema: {'✅' if schema_ok else '❌'}")
    print(f"All Endpoints Working: {'✅' if endpoints_ok else '❌'}")
    
    if swagger_ok and schema_ok and endpoints_ok:
        print("\n🎉 SUCCESS: All public endpoints are working and visible in Swagger!")
        return True
    else:
        print("\n⚠️  ISSUES FOUND: Some endpoints may need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)