#!/usr/bin/env python3
"""
Test script to verify the optimized products API endpoints.
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://127.0.0.1:8000"

def test_api_endpoints():
    """
    Test the products API endpoints with the new structure.
    """
    print("Testing optimized products API endpoints...")
    
    # Test 1: Get public product categories
    print("\n1. Testing Public Product Categories...")
    try:
        response = requests.get(f"{BASE_URL}/api/public/products/categories/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ Found {len(categories)} categories")
            if categories:
                print(f"   Sample category: {categories[0]['name']}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Get public products list  
    print("\n2. Testing Public Products List...")
    try:
        response = requests.get(f"{BASE_URL}/api/public/products/products/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            products = response.json()
            print(f"✅ Found products in response")
            if isinstance(products, dict) and 'results' in products:
                products_list = products['results']
                print(f"   Total products: {len(products_list)}")
                if products_list:
                    sample_product = products_list[0]
                    print(f"   Sample product: {sample_product['name']}")
                    print(f"   Category ID: {sample_product.get('category_id')}")
                    print(f"   Category Name: {sample_product.get('category_name')}")
                    print(f"   Brand Name: {sample_product.get('brand_name')}")
                    print(f"   Variants: {len(sample_product.get('variants', []))}")
                    print(f"   Medicine Details: {'medicine_details' in sample_product}")
                    print(f"   Equipment Details: {'equipment_details' in sample_product}")
            else:
                print(f"   Found {len(products)} products")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Get a specific product detail
    print("\n3. Testing Product Detail...")
    try:
        # First get a product ID from the list
        response = requests.get(f"{BASE_URL}/api/public/products/products/")
        if response.status_code == 200:
            products_data = response.json()
            if isinstance(products_data, dict) and 'results' in products_data:
                products_list = products_data['results']
            else:
                products_list = products_data
            
            if products_list:
                product_id = products_list[0]['id']
                detail_response = requests.get(f"{BASE_URL}/api/public/products/products/{product_id}/")
                print(f"Status: {detail_response.status_code}")
                
                if detail_response.status_code == 200:
                    product_detail = detail_response.json()
                    print(f"✅ Product detail retrieved: {product_detail['name']}")
                    print(f"   SKU: {product_detail.get('sku')}")
                    print(f"   Category ID: {product_detail.get('category_id')}")
                    print(f"   Category Name: {product_detail.get('category_name')}")
                    print(f"   Brand Name: {product_detail.get('brand_name')}")
                    print(f"   Product Type: {product_detail.get('product_type')}")
                    print(f"   Variants: {len(product_detail.get('variants', []))}")
                    print(f"   Images: {len(product_detail.get('images', []))}")
                    
                    # Check type-specific details
                    if product_detail.get('product_type') == 'medicine':
                        med_details = product_detail.get('medicine_details')
                        if med_details:
                            print(f"   Medicine Details: ✅")
                            print(f"     Composition: {med_details.get('composition', 'N/A')}")
                            print(f"     Manufacturer: {med_details.get('manufacturer', 'N/A')}")
                        else:
                            print(f"   Medicine Details: None")
                    elif product_detail.get('product_type') == 'equipment':
                        eq_details = product_detail.get('equipment_details')
                        if eq_details:
                            print(f"   Equipment Details: ✅")
                            print(f"     Model: {eq_details.get('model_number', 'N/A')}")
                            print(f"     Type: {eq_details.get('equipment_type', 'N/A')}")
                        else:
                            print(f"   Equipment Details: None")
                else:
                    print(f"❌ Error getting detail: {detail_response.text}")
            else:
                print("❌ No products found to test detail")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Test brands endpoint
    print("\n4. Testing Brands Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/public/products/brands/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            brands = response.json()
            print(f"✅ Found {len(brands)} brands")
            if brands:
                print(f"   Sample brand: {brands[0]['name']}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 5: Test Swagger documentation
    print("\n5. Testing Swagger Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/swagger/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Swagger documentation accessible")
        else:
            print(f"❌ Swagger not accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception accessing Swagger: {e}")
    
    print("\n🎉 API testing completed!")

if __name__ == "__main__":
    test_api_endpoints()
