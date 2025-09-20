#!/usr/bin/env python3
"""
Comprehensive test to verify the fix across multiple products
"""
import requests
import json

def test_multiple_products():
    """Test multiple products to ensure consistency"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("=== Comprehensive Consistency Test ===\n")
    
    # Get list of products
    list_response = requests.get(f"{base_url}/api/public/products/products/", timeout=10)
    if list_response.status_code != 200:
        print("❌ Cannot access product list")
        return
    
    list_data = list_response.json()
    products = list_data.get('results', [])[:5]  # Test first 5 products
    
    print(f"Testing {len(products)} products for consistency...\n")
    
    for i, product in enumerate(products, 1):
        product_id = product.get('id')
        product_name = product.get('name', 'Unknown')[:30]
        
        # Get list data
        list_variants = len(product.get('variants', []))
        list_images = len(product.get('images', []))
        list_reviews = len(product.get('reviews', []))
        
        # Get detail data
        detail_response = requests.get(f"{base_url}/api/public/products/products/{product_id}/", timeout=10)
        
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            detail_variants = len(detail_data.get('variants', []))
            detail_images = len(detail_data.get('images', []))
            detail_reviews = len(detail_data.get('reviews', []))
            
            # Check consistency
            variants_match = list_variants == detail_variants
            images_match = list_images == detail_images
            reviews_match = list_reviews == detail_reviews
            
            status = "✅" if (variants_match and images_match and reviews_match) else "❌"
            
            print(f"{i}. Product {product_id}: {product_name}... {status}")
            print(f"   Variants: List={list_variants}, Detail={detail_variants} {'✅' if variants_match else '❌'}")
            print(f"   Images: List={list_images}, Detail={detail_images} {'✅' if images_match else '❌'}")
            print(f"   Reviews: List={list_reviews}, Detail={detail_reviews} {'✅' if reviews_match else '❌'}")
            
            # Show variant details if available
            if detail_data.get('variants'):
                variant = detail_data['variants'][0]
                print(f"   Sample variant: SKU={variant.get('sku')}, Price=${variant.get('price')}, Attrs={len(variant.get('attributes', []))}")
            print()
        else:
            print(f"{i}. Product {product_id}: {product_name}... ❌ Detail endpoint failed ({detail_response.status_code})")
            print()

if __name__ == "__main__":
    test_multiple_products()