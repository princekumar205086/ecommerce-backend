#!/usr/bin/env python3
"""
Test script to check the actual API response format for brand data
"""

import os
import django
import requests
import json
from datetime import datetime

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

def test_product_api_response():
    """Test the actual product API response format"""
    print("🔍 TESTING PRODUCT API BRAND DATA FORMAT")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000/api/public/products/products"
    
    try:
        # Get first few products with pagination
        response = requests.get(f"{base_url}/?page=1", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if results:
                print(f"📊 Total products: {data.get('count', 'N/A')}")
                print(f"📈 Products in response: {len(results)}")
                
                # Check first few products
                for i, product in enumerate(results[:3], 1):
                    print(f"\n📦 Product {i}: {product.get('name', 'N/A')}")
                    print(f"   🆔 ID: {product.get('id', 'N/A')}")
                    
                    # Check brand data structure
                    brand = product.get('brand')
                    brand_name = product.get('brand_name')
                    
                    print(f"   🏷️  Brand field: {brand} (type: {type(brand)})")
                    print(f"   🏷️  Brand name field: {brand_name}")
                    
                    # Check category data structure for comparison
                    category = product.get('category')
                    category_name = product.get('category_name')
                    category_id = product.get('category_id')
                    
                    print(f"   📂 Category field: {category} (type: {type(category)})")
                    print(f"   📂 Category name field: {category_name}")
                    print(f"   📂 Category ID field: {category_id}")
                    
                    # Check if we should restructure the response
                    print(f"   🔧 Current structure issue: brand={brand}, brand_name={brand_name}")
                    if brand and brand_name:
                        suggested_structure = {"id": brand, "name": brand_name}
                        print(f"   💡 Suggested structure: {suggested_structure}")
                
                # Show sample JSON structure
                print(f"\n📄 SAMPLE RESPONSE STRUCTURE:")
                sample_product = results[0]
                relevant_fields = {
                    'id': sample_product.get('id'),
                    'name': sample_product.get('name'),
                    'brand': sample_product.get('brand'),
                    'brand_name': sample_product.get('brand_name'),
                    'category': sample_product.get('category'),
                    'category_name': sample_product.get('category_name'),
                    'category_id': sample_product.get('category_id')
                }
                print(json.dumps(relevant_fields, indent=2))
                
            else:
                print("❌ No products found in response")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_brand_api_response():
    """Test the brands API to see the expected structure"""
    print(f"\n\n🔍 TESTING BRANDS API STRUCTURE")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000/api/public/products/brands"
    
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if results:
                print(f"📊 Total brands: {data.get('count', len(results))}")
                print(f"📈 Brands in response: {len(results)}")
                
                # Show first few brands
                for i, brand in enumerate(results[:3], 1):
                    print(f"\n🏷️  Brand {i}:")
                    print(f"   🆔 ID: {brand.get('id', 'N/A')}")
                    print(f"   📛 Name: {brand.get('name', 'N/A')}")
                    print(f"   🖼️  Image: {brand.get('image', 'N/A')}")
                
                # Show sample brand structure
                print(f"\n📄 SAMPLE BRAND STRUCTURE:")
                sample_brand = results[0]
                print(json.dumps(sample_brand, indent=2))
                
            else:
                print("❌ No brands found in response")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 BRAND DATA STRUCTURE ANALYSIS")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_product_api_response()
    test_brand_api_response()
    
    print(f"\n\n💡 RECOMMENDATIONS:")
    print("1. Products API should return brand as nested object: {id: X, name: 'Brand Name'}")
    print("2. This matches how category data should be structured")
    print("3. Frontend can then use product.brand.name consistently")
    print("4. Alternative: Frontend can map brand ID to brand name using brands API")
    
    print(f"\n✅ ANALYSIS COMPLETED")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)