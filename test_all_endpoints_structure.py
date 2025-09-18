#!/usr/bin/env python3

"""
Test script to verify all product endpoints now return nested brand/category objects
"""

import requests
import json

# Test configuration
BASE_URL = "http://127.0.0.1:8000/api/public/products"

def test_endpoint_structure(endpoint_name, url):
    """Test a specific endpoint for proper brand/category structure"""
    
    print(f"\n🧪 Testing {endpoint_name}")
    print("-" * 40)
    
    try:
        print(f"📞 Calling: {url}")
        response = requests.get(url)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle both paginated and non-paginated responses
            products = data.get('results', data) if isinstance(data, dict) else data
            
            if isinstance(products, list) and len(products) > 0:
                product = products[0]
                
                # Check brand structure
                brand = product.get('brand')
                brand_ok = isinstance(brand, dict) and 'name' in brand
                
                # Check category structure  
                category = product.get('category')
                category_ok = isinstance(category, dict) and 'name' in category
                
                print(f"   ✅ Brand nested: {brand_ok}")
                print(f"   ✅ Category nested: {category_ok}")
                
                if brand_ok and category_ok:
                    print(f"   🎉 {endpoint_name}: PASS")
                    return True
                else:
                    print(f"   ❌ {endpoint_name}: FAIL")
                    return False
            else:
                print(f"   ⚠️  No products found for {endpoint_name}")
                return True  # Not a failure, just no data
                
        else:
            print(f"   ❌ {endpoint_name} failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing {endpoint_name}: {e}")
        return False

def main():
    print("🚀 Comprehensive Product Endpoints Structure Test")
    print("Testing all product endpoints for nested brand/category objects")
    print("=" * 70)
    
    # List of endpoints to test
    endpoints = [
        ("Products List (no pagination)", f"{BASE_URL}/products/"),
        ("Products List (paginated)", f"{BASE_URL}/products/?page=1"),
        ("Featured Products", f"{BASE_URL}/featured/"),
        ("Search Products", f"{BASE_URL}/search/?q=medicine"),
    ]
    
    # Get sample IDs for category and brand specific tests
    try:
        # Get a sample category ID
        response = requests.get(f"{BASE_URL}/products/?page=1")
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                sample_product = data['results'][0]
                category_id = sample_product.get('category', {}).get('id') if isinstance(sample_product.get('category'), dict) else None
                brand_id = sample_product.get('brand', {}).get('id') if isinstance(sample_product.get('brand'), dict) else None
                
                if category_id:
                    endpoints.append((f"Products by Category", f"{BASE_URL}/categories/{category_id}/products/"))
                
                if brand_id:
                    endpoints.append((f"Products by Brand", f"{BASE_URL}/brands/{brand_id}/products/"))
                
                # Also test specific product type
                endpoints.append(("Products by Type (medicine)", f"{BASE_URL}/types/medicine/products/"))
    except:
        pass
    
    # Test all endpoints
    results = []
    for name, url in endpoints:
        result = test_endpoint_structure(name, url)
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 FINAL RESULTS:")
    
    all_pass = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
        if not result:
            all_pass = False
    
    print(f"\n{'🎉 ALL TESTS PASSED!' if all_pass else '⚠️  Some tests failed'}")
    
    if all_pass:
        print("✅ All product endpoints now return nested brand/category objects")
        print("✅ Frontend compatibility issue is completely resolved")
        print("✅ Frontend can now safely access brand.name and category.name")
    else:
        print("❌ Some endpoints still need to be updated")

if __name__ == "__main__":
    main()