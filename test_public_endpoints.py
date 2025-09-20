#!/usr/bin/env python3
"""
Test the correct public API endpoints
"""
import requests
import json

def test_public_endpoints():
    """Test public product endpoints"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("=== Testing Public API Endpoints ===\n")
    
    # Test public list endpoint
    try:
        list_response = requests.get(f"{base_url}/api/public/products/products/", timeout=10)
        if list_response.status_code == 200:
            list_data = list_response.json()
            print(f"✅ Public List endpoint: {list_response.status_code}")
            print(f"   Products returned: {len(list_data.get('results', []))}")
            
            # Check first product for variants
            if list_data.get('results'):
                first_product = list_data['results'][0]
                print(f"   First product ID: {first_product.get('id')}")
                print(f"   First product variants: {len(first_product.get('variants', []))}")
                print(f"   First product images: {len(first_product.get('images', []))}")
                print(f"   First product reviews: {len(first_product.get('reviews', []))}")
                
                # Test detail endpoint with this product
                product_id = first_product.get('id')
                if product_id:
                    print(f"\n   Testing detail endpoint for product {product_id}:")
                    detail_response = requests.get(f"{base_url}/api/public/products/products/{product_id}/", timeout=10)
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        print(f"   ✅ Detail endpoint: {detail_response.status_code}")
                        print(f"      Detail variants: {len(detail_data.get('variants', []))}")
                        print(f"      Detail images: {len(detail_data.get('images', []))}")
                        print(f"      Detail reviews: {len(detail_data.get('reviews', []))}")
                        
                        # Compare list vs detail
                        list_variants = len(first_product.get('variants', []))
                        detail_variants = len(detail_data.get('variants', []))
                        
                        if list_variants == detail_variants:
                            print(f"   ✅ CONSISTENCY CHECK: List and detail both show {list_variants} variants")
                        else:
                            print(f"   ❌ INCONSISTENCY: List shows {list_variants} variants, detail shows {detail_variants}")
                            
                        # Show variant details if present
                        if detail_data.get('variants'):
                            print(f"   Detail variant example:")
                            variant = detail_data['variants'][0]
                            print(f"      ID: {variant.get('id')}")
                            print(f"      SKU: {variant.get('sku')}")
                            print(f"      Price: ${variant.get('price')}")
                            print(f"      Stock: {variant.get('stock')}")
                            print(f"      Attributes: {len(variant.get('attributes', []))}")
                    else:
                        print(f"   ❌ Detail endpoint failed: {detail_response.status_code}")
                        print(f"      Error: {detail_response.text[:200]}...")
        else:
            print(f"❌ Public List endpoint failed: {list_response.status_code}")
            print(f"   Error: {list_response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")

if __name__ == "__main__":
    test_public_endpoints()