#!/usr/bin/env python3
"""
Test locally using Django serializers
"""
import os
import sys
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductVariant, ProductImage, ProductReview
from products.serializers import PublicProductSerializer

def test_local_serializer():
    """Test the serializer locally"""
    print("=== TESTING LOCAL SERIALIZER ===\n")
    
    # Find any product with variants
    product = Product.objects.filter(
        status='published',
        is_publish=True,
        variants__isnull=False
    ).first()
    
    if not product:
        print("❌ No products with variants found")
        return
    
    print(f"🧪 Testing Product: {product.name} (ID: {product.id})")
    
    # Check database state
    total_variants = product.variants.count()
    approved_variants = product.variants.filter(
        status__in=['approved', 'published'], 
        is_active=True
    ).count()
    
    print(f"📊 Database State:")
    print(f"   Total variants: {total_variants}")
    print(f"   Approved variants: {approved_variants}")
    print(f"   Total images: {product.images.count()}")
    print(f"   Total reviews: {product.reviews.count()}")
    
    # Test serializer
    serializer = PublicProductSerializer(product)
    data = serializer.data
    
    print(f"\n📋 Serializer Output:")
    print(f"   Variants returned: {len(data.get('variants', []))}")
    print(f"   Images returned: {len(data.get('images', []))}")
    
    # Show detailed variant info
    if data.get('variants'):
        print(f"\n🔧 First variant details:")
        first_variant = data['variants'][0]
        print(f"   SKU: {first_variant.get('sku')}")
        print(f"   Price: {first_variant.get('price')}")
        print(f"   Total Price: {first_variant.get('total_price')}")
        print(f"   Stock: {first_variant.get('stock')}")
        print(f"   Attributes: {len(first_variant.get('attributes', []))}")
        
        for attr in first_variant.get('attributes', []):
            print(f"     - {attr.get('attribute_name')}: {attr.get('value')}")
    
    # Test as JSON
    json_output = json.dumps(data, indent=2, default=str)
    
    print(f"\n💾 Saving output to test_response.json")
    with open('test_response.json', 'w') as f:
        f.write(json_output)
    
    return product.id

def test_queryset_filtering():
    """Test if the queryset filtering is working"""
    print("\n=== TESTING QUERYSET FILTERING ===\n")
    
    # Check what the public views see
    from products.public_views import PublicProductDetailView
    
    view = PublicProductDetailView()
    view.request = type('MockRequest', (), {
        'user': type('MockUser', (), {'is_authenticated': False})(),
        'session': {}
    })()
    
    queryset = view.get_queryset()
    
    print(f"📊 Public queryset stats:")
    print(f"   Total products in queryset: {queryset.count()}")
    
    products_with_variants = queryset.filter(variants__isnull=False).distinct()
    print(f"   Products with variants: {products_with_variants.count()}")
    
    # Show some examples
    print(f"\n📋 Sample products with variants:")
    for product in products_with_variants[:5]:
        approved_variants = product.variants.filter(
            status__in=['approved', 'published'], 
            is_active=True
        ).count()
        print(f"   ID: {product.id}, Name: {product.name}, Approved variants: {approved_variants}")

if __name__ == "__main__":
    product_id = test_local_serializer()
    test_queryset_filtering()
    
    if product_id:
        print(f"\n✅ Local test completed! Product ID {product_id} has working variants.")
        print(f"🧪 Try testing with this product ID in your API calls.")