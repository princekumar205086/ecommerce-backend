#!/usr/bin/env python3
"""
Test the new product with medicine details via API.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_optimized_product_api():
    """
    Test API for our newly created optimized products.
    """
    print("Testing API for optimized products...")
    
    try:
        # Get all products and find our test medicine
        response = requests.get(f"{BASE_URL}/api/public/products/products/")
        if response.status_code == 200:
            products_data = response.json()
            products_list = products_data['results'] if 'results' in products_data else products_data
            
            # Find our test medicine product
            test_medicine = None
            for product in products_list:
                if product['name'] == 'Test Optimized Medicine':
                    test_medicine = product
                    break
            
            if test_medicine:
                print(f"✅ Found Test Optimized Medicine: ID {test_medicine['id']}")
                print(f"   Category: {test_medicine['category_name']} (ID: {test_medicine['category_id']})")
                print(f"   Brand: {test_medicine['brand_name']}")
                print(f"   Product Type: {test_medicine['product_type']}")
                print(f"   Price: ${test_medicine['price']}")
                print(f"   Stock: {test_medicine['stock']}")
                print(f"   Variants: {len(test_medicine['variants'])}")
                
                # Check medicine details
                med_details = test_medicine.get('medicine_details')
                if med_details:
                    print(f"✅ Medicine Details Found:")
                    print(f"     Composition: {med_details['composition']}")
                    print(f"     Manufacturer: {med_details['manufacturer']}")
                    print(f"     Batch Number: {med_details['batch_number']}")
                    print(f"     Prescription Required: {med_details['prescription_required']}")
                    print(f"     Form: {med_details['form']}")
                    print(f"     Pack Size: {med_details['pack_size']}")
                else:
                    print("❌ Medicine Details not found")
                
                # Test the detail endpoint
                detail_response = requests.get(f"{BASE_URL}/api/public/products/products/{test_medicine['id']}/")
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    print(f"\n✅ Product Detail API working")
                    print(f"   Related Products: {len(detail_data.get('related_products', []))}")
                    
                    # Check variants in detail
                    variants = detail_data.get('variants', [])
                    print(f"   Variants Details:")
                    for i, variant in enumerate(variants, 1):
                        print(f"     Variant {i}: SKU={variant['sku']}, Price=${variant['total_price']}")
                        attrs = variant.get('attributes', [])
                        if attrs:
                            attr_strs = [f"{attr['attribute_name']}: {attr['value']}" for attr in attrs]
                            print(f"       Attributes: {', '.join(attr_strs)}")
                else:
                    print(f"❌ Product detail API error: {detail_response.status_code}")
            else:
                print("❌ Test Optimized Medicine not found in products list")
                print("Available products:")
                for prod in products_list[:5]:
                    print(f"   - {prod['name']} (Type: {prod['product_type']})")
        else:
            print(f"❌ Error getting products: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_optimized_product_api()
