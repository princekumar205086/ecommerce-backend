#!/usr/bin/env python3

"""
Test script to verify the brand and category data structure fix
Checks if the API now returns nested objects instead of flat ID/name fields
"""

import requests
import json

# Test configuration
BASE_URL = "http://127.0.0.1:8000/api/public/products"

def test_brand_data_structure():
    """Test if brand is returned as nested object instead of flat fields"""
    
    print("🧪 Testing Brand Data Structure Fix")
    print("=" * 50)
    
    # Test main products endpoint with a single product
    url = f"{BASE_URL}/products/?page=1"
    
    try:
        print(f"📞 Calling: {url}")
        response = requests.get(url)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('results') and len(data['results']) > 0:
                product = data['results'][0]
                
                print(f"📦 Product: {product.get('name', 'Unknown')}")
                print(f"🏷️  Product ID: {product.get('id', 'Unknown')}")
                
                # Check brand structure
                print("\n🔍 Brand Structure:")
                if 'brand' in product:
                    brand = product['brand']
                    print(f"   brand type: {type(brand)}")
                    if isinstance(brand, dict):
                        print(f"   ✅ brand is object: {brand}")
                        print(f"   🏷️  brand.id: {brand.get('id', 'missing')}")
                        print(f"   📝 brand.name: {brand.get('name', 'missing')}")
                        print(f"   🖼️  brand.image: {brand.get('image', 'missing')}")
                    else:
                        print(f"   ❌ brand is still flat: {brand}")
                        print(f"   🔴 ISSUE: Expected nested object, got {type(brand)}")
                
                # Check if old flat fields still exist (they shouldn't)
                if 'brand_name' in product:
                    print(f"   ⚠️  Old brand_name field still exists: {product['brand_name']}")
                else:
                    print(f"   ✅ Old brand_name field removed")
                
                # Check category structure  
                print("\n🔍 Category Structure:")
                if 'category' in product:
                    category = product['category']
                    print(f"   category type: {type(category)}")
                    if isinstance(category, dict):
                        print(f"   ✅ category is object: {category}")
                        print(f"   🏷️  category.id: {category.get('id', 'missing')}")
                        print(f"   📝 category.name: {category.get('name', 'missing')}")
                        print(f"   🔗 category.slug: {category.get('slug', 'missing')}")
                        print(f"   🎯 category.icon: {category.get('icon', 'missing')}")
                    else:
                        print(f"   ❌ category is still flat: {category}")
                        print(f"   🔴 ISSUE: Expected nested object, got {type(category)}")
                
                # Check if old flat fields still exist (they shouldn't)
                if 'category_name' in product:
                    print(f"   ⚠️  Old category_name field still exists: {product['category_name']}")
                else:
                    print(f"   ✅ Old category_name field removed")
                
                # Summary
                print("\n📊 SUMMARY:")
                brand_ok = isinstance(product.get('brand'), dict)
                category_ok = isinstance(product.get('category'), dict)
                
                if brand_ok and category_ok:
                    print("   ✅ SUCCESS: Both brand and category are nested objects")
                    print("   🎉 Frontend compatibility issue FIXED!")
                elif brand_ok:
                    print("   ⚠️  PARTIAL: Brand is nested but category is not")
                elif category_ok:
                    print("   ⚠️  PARTIAL: Category is nested but brand is not")
                else:
                    print("   ❌ FAILURE: Neither brand nor category are nested objects")
                    print("   🔧 Need to check serializer implementation")
                
                return brand_ok and category_ok
            else:
                print("❌ No products found in response")
                return False
                
        else:
            print(f"❌ API call failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure Django server is running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_specific_product_detail():
    """Test product detail endpoint for brand/category structure"""
    
    print("\n🧪 Testing Product Detail Endpoint")
    print("=" * 50)
    
    # Get first product ID from list
    try:
        list_response = requests.get(f"{BASE_URL}/products/?page=1")
        if list_response.status_code == 200:
            list_data = list_response.json()
            if list_data.get('results'):
                product_id = list_data['results'][0]['id']
                
                # Test detail endpoint
                detail_url = f"{BASE_URL}/products/{product_id}/"
                print(f"📞 Calling: {detail_url}")
                
                detail_response = requests.get(detail_url)
                print(f"📊 Status Code: {detail_response.status_code}")
                
                if detail_response.status_code == 200:
                    product = detail_response.json()
                    
                    # Check structures
                    brand_nested = isinstance(product.get('brand'), dict)
                    category_nested = isinstance(product.get('category'), dict)
                    
                    print(f"   ✅ Brand nested: {brand_nested}")
                    print(f"   ✅ Category nested: {category_nested}")
                    
                    # Check related products too
                    if 'related_products' in product:
                        related = product['related_products']
                        if related:
                            first_related = related[0]
                            related_brand_nested = isinstance(first_related.get('brand'), dict)
                            related_category_nested = isinstance(first_related.get('category'), dict)
                            
                            print(f"   ✅ Related products brand nested: {related_brand_nested}")
                            print(f"   ✅ Related products category nested: {related_category_nested}")
                            
                            return brand_nested and category_nested and related_brand_nested and related_category_nested
                    
                    return brand_nested and category_nested
                
    except Exception as e:
        print(f"❌ Error testing detail endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Brand/Category Data Structure Test")
    print("Testing if API now returns nested objects for frontend compatibility")
    print()
    
    # Run tests
    list_success = test_brand_data_structure()
    detail_success = test_specific_product_detail()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"   📋 Product List Endpoint: {'✅ PASS' if list_success else '❌ FAIL'}")
    print(f"   📄 Product Detail Endpoint: {'✅ PASS' if detail_success else '❌ FAIL'}")
    
    if list_success and detail_success:
        print("\n🎉 SUCCESS: Brand/category structure fix is working!")
        print("   Frontend can now access brand.name and category.name")
    else:
        print("\n⚠️  Some endpoints still need fixes")