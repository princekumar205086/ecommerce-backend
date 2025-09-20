#!/usr/bin/env python3
"""
Test the API endpoint to verify variants, images, and reviews are working
"""
import os
import sys
import django
import json
import requests

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductVariant, ProductImage, ProductReview

def test_product_api():
    """Test the product API to see if variants, images, and reviews appear"""
    print("=== TESTING PRODUCT API ENDPOINT ===\n")
    
    # Get a product with variants, images, and reviews
    product = Product.objects.filter(
        status='published',
        is_publish=True,
        variants__isnull=False,
        images__isnull=False,
        reviews__isnull=False
    ).first()
    
    if not product:
        print("❌ No product found with variants, images, and reviews")
        return None
    
    print(f"🧪 Testing Product: {product.name} (ID: {product.id})")
    
    # Check database state
    total_variants = product.variants.count()
    approved_variants = product.variants.filter(
        status__in=['approved', 'published'], 
        is_active=True
    ).count()
    
    total_images = product.images.count()
    variant_images = product.images.filter(variant__isnull=False).count()
    product_images = product.images.filter(variant__isnull=True).count()
    
    total_reviews = product.reviews.count()
    published_reviews = product.reviews.filter(is_published=True).count()
    
    print(f"📊 Database State:")
    print(f"   Variants: {approved_variants}/{total_variants} approved")
    print(f"   Images: {total_images} total ({product_images} product, {variant_images} variant)")
    print(f"   Reviews: {published_reviews}/{total_reviews} published")
    
    # Test API endpoint
    api_url = f"https://backend.okpuja.in/api/public/products/products/{product.id}/"
    
    print(f"\n🌐 Testing API: {api_url}")
    
    try:
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check variants in response
            api_variants = data.get('variants', [])
            api_images = data.get('images', [])
            api_review_stats = data.get('review_stats', {})
            
            print(f"✅ API Response successful!")
            print(f"📊 API Response Data:")
            print(f"   Variants returned: {len(api_variants)}")
            print(f"   Images returned: {len(api_images)}")
            print(f"   Review stats: {api_review_stats.get('total_reviews', 0)} reviews, {api_review_stats.get('average_rating', 0):.1f} avg rating")
            
            # Show variant details
            if api_variants:
                print(f"\n🔧 Variant Details:")
                for i, variant in enumerate(api_variants[:3]):  # Show first 3
                    print(f"   Variant {i+1}: SKU={variant.get('sku', 'N/A')}, Price={variant.get('total_price', 'N/A')}, Stock={variant.get('stock', 'N/A')}")
                    attributes = variant.get('attributes', [])
                    if attributes:
                        attr_str = ", ".join([f"{attr.get('attribute_name', '')}:{attr.get('value', '')}" for attr in attributes])
                        print(f"      Attributes: {attr_str}")
            
            # Show image details
            if api_images:
                print(f"\n🖼️  Image Details:")
                for i, image in enumerate(api_images[:3]):  # Show first 3
                    print(f"   Image {i+1}: {image.get('image', 'N/A')[:60]}...")
                    print(f"      Alt: {image.get('alt_text', 'N/A')}")
            
            # Show review stats breakdown
            if api_review_stats:
                print(f"\n⭐ Review Breakdown:")
                rating_dist = api_review_stats.get('rating_distribution', {})
                for rating in ['5', '4', '3', '2', '1']:
                    count = rating_dist.get(rating, 0)
                    print(f"   {rating}⭐: {count} reviews")
            
            return {
                'product_id': product.id,
                'product_name': product.name,
                'api_url': api_url,
                'variants_in_db': approved_variants,
                'variants_in_api': len(api_variants),
                'images_in_db': total_images,
                'images_in_api': len(api_images),
                'reviews_in_db': published_reviews,
                'reviews_in_api': api_review_stats.get('total_reviews', 0),
                'response_data': data
            }
            
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API request error: {str(e)}")
        return None
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

def test_multiple_products():
    """Test multiple products to ensure the fix works across different products"""
    print("\n=== TESTING MULTIPLE PRODUCTS ===\n")
    
    products = Product.objects.filter(
        status='published',
        is_publish=True,
        variants__isnull=False
    )[:5]
    
    results = []
    
    for product in products:
        print(f"\n🧪 Testing: {product.name} (ID: {product.id})")
        
        # Quick stats
        variants_count = product.variants.filter(
            status__in=['approved', 'published'], 
            is_active=True
        ).count()
        images_count = product.images.count()
        reviews_count = product.reviews.filter(is_published=True).count()
        
        print(f"   Variants: {variants_count}, Images: {images_count}, Reviews: {reviews_count}")
        
        if variants_count > 0:
            api_url = f"https://backend.okpuja.in/api/public/products/products/{product.id}/"
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    api_variants = len(data.get('variants', []))
                    api_images = len(data.get('images', []))
                    api_reviews = data.get('review_stats', {}).get('total_reviews', 0)
                    
                    status = "✅" if api_variants > 0 else "⚠️"
                    print(f"   {status} API: {api_variants} variants, {api_images} images, {api_reviews} reviews")
                    
                    results.append({
                        'id': product.id,
                        'name': product.name,
                        'variants_db': variants_count,
                        'variants_api': api_variants,
                        'images_db': images_count,
                        'images_api': api_images,
                        'reviews_db': reviews_count,
                        'reviews_api': api_reviews,
                        'success': api_variants > 0
                    })
                else:
                    print(f"   ❌ API error: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Request failed: {str(e)}")
    
    return results

if __name__ == "__main__":
    print("🧪 Starting comprehensive API testing...\n")
    
    # Test single product in detail
    detailed_result = test_product_api()
    
    # Test multiple products
    multi_results = test_multiple_products()
    
    print(f"\n📋 SUMMARY:")
    print(f"==========================================")
    
    if detailed_result:
        print(f"✅ Detailed test completed successfully!")
        print(f"   Product: {detailed_result['product_name']} (ID: {detailed_result['product_id']})")
        print(f"   Variants: {detailed_result['variants_in_api']}/{detailed_result['variants_in_db']} shown")
        print(f"   Images: {detailed_result['images_in_api']}/{detailed_result['images_in_db']} shown")
        print(f"   Reviews: {detailed_result['reviews_in_api']}/{detailed_result['reviews_in_db']} shown")
        print(f"   Test URL: {detailed_result['api_url']}")
    
    if multi_results:
        successful = [r for r in multi_results if r['success']]
        print(f"\n📊 Multi-product test: {len(successful)}/{len(multi_results)} products showing variants")
        
        for result in multi_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['name']} (ID: {result['id']}): {result['variants_api']} variants shown")
    
    print(f"\n🎉 Testing completed!")
    print(f"🌐 You can now use these products to test the frontend integration.")