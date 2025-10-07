#!/usr/bin/env python3
"""
Test the performance optimization - lightweight vs full serializers
"""
import requests
import time
import json

def test_performance_optimization():
    """Test the performance differences between list and detail endpoints"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("=== Testing Performance Optimization ===\n")
    
    # Test list endpoint (should use lightweight serializer)
    print("1. Testing List Endpoint (Lightweight - No Variants/Images/Reviews):")
    start_time = time.time()
    list_response = requests.get(f"{base_url}/api/public/products/products/?page_size=10", timeout=20)
    list_time = time.time() - start_time
    
    if list_response.status_code == 200:
        list_data = list_response.json()
        products = list_data.get('results', [])
        print(f"   ✅ Status: {list_response.status_code}")
        print(f"   ⏱️  Response time: {list_time:.3f} seconds")
        print(f"   📦 Products returned: {len(products)}")
        
        if products:
            first_product = products[0]
            print(f"   📊 First product data:")
            print(f"      ID: {first_product.get('id')}")
            print(f"      Name: {first_product.get('name', 'Unknown')[:30]}...")
            print(f"      Has variants field: {'variants' in first_product}")
            print(f"      Has images field: {'images' in first_product}")
            print(f"      Has reviews field: {'reviews' in first_product}")
            
            if 'variants' in first_product:
                print(f"      ❌ ISSUE: List endpoint includes variants (should be lightweight!)")
            else:
                print(f"      ✅ GOOD: List endpoint excludes variants (lightweight working!)")
            
            # Test detail endpoint with the same product
            product_id = first_product.get('id')
            print(f"\n2. Testing Detail Endpoint (Full - With Variants/Images/Reviews):")
            start_time = time.time()
            detail_response = requests.get(f"{base_url}/api/public/products/products/{product_id}/", timeout=20)
            detail_time = time.time() - start_time
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                print(f"   ✅ Status: {detail_response.status_code}")
                print(f"   ⏱️  Response time: {detail_time:.3f} seconds")
                print(f"   📊 Detail product data:")
                print(f"      ID: {detail_data.get('id')}")
                print(f"      Name: {detail_data.get('name', 'Unknown')[:30]}...")
                print(f"      Variants: {len(detail_data.get('variants', []))}")
                print(f"      Images: {len(detail_data.get('images', []))}")
                print(f"      Reviews: {len(detail_data.get('reviews', []))}")
                
                if detail_data.get('variants'):
                    print(f"      ✅ GOOD: Detail endpoint includes variants")
                    variant = detail_data['variants'][0]
                    print(f"         Sample variant: SKU={variant.get('sku')}, Price=${variant.get('price')}")
                else:
                    print(f"      ❌ ISSUE: Detail endpoint missing variants")
                
                # Performance comparison
                time_diff = detail_time - list_time
                if list_time < detail_time:
                    improvement = ((detail_time - list_time) / detail_time) * 100
                    print(f"\n3. Performance Analysis:")
                    print(f"   ⚡ List endpoint is {improvement:.1f}% faster than detail endpoint")
                    print(f"   📈 Time saved: {time_diff:.3f} seconds per request")
                    print(f"   ✅ Optimization working correctly!")
                else:
                    print(f"\n3. Performance Analysis:")
                    print(f"   ⚠️  Detail endpoint is faster - this might indicate an issue")
                
            else:
                print(f"   ❌ Detail endpoint failed: {detail_response.status_code}")
    else:
        print(f"   ❌ List endpoint failed: {list_response.status_code}")
        print(f"   Error: {list_response.text[:200]}...")
    
    # Test search endpoint (should also be lightweight)
    print(f"\n4. Testing Search Endpoint (Should be Lightweight):")
    start_time = time.time()
    search_response = requests.get(f"{base_url}/api/public/products/search/?q=vitamin&page_size=5", timeout=20)
    search_time = time.time() - start_time
    
    if search_response.status_code == 200:
        search_data = search_response.json()
        print(f"   ✅ Status: {search_response.status_code}")
        print(f"   ⏱️  Response time: {search_time:.3f} seconds")
        search_products = search_data.get('products', [])
        print(f"   📦 Products found: {len(search_products)}")
        
        if search_products:
            search_product = search_products[0]
            print(f"   📊 First search result:")
            print(f"      Name: {search_product.get('name', 'Unknown')[:30]}...")
            print(f"      Has variants field: {'variants' in search_product}")
            
            if 'variants' in search_product:
                print(f"      ❌ ISSUE: Search endpoint includes variants (should be lightweight!)")
            else:
                print(f"      ✅ GOOD: Search endpoint excludes variants (lightweight working!)")
    else:
        print(f"   ❌ Search endpoint failed: {search_response.status_code}")

if __name__ == "__main__":
    test_performance_optimization()