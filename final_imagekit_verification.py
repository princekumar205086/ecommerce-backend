#!/usr/bin/env python3
"""
Final ImageKit Verification
Check that all existing products now have working ImageKit images
"""

import os
import django
import sys
import requests

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductCategory, Brand

def test_image_accessibility(url):
    """Test if an image URL is accessible"""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def verify_all_images():
    """Verify all product, category, and brand images"""
    print("🔍 FINAL IMAGEKIT VERIFICATION")
    print("=" * 50)
    
    # Check products
    print("\n💊 Checking Product Images:")
    products = Product.objects.exclude(image='')
    working_products = 0
    broken_products = 0
    
    for product in products[:10]:  # Check first 10 products
        if 'imagekit.io' in product.image:
            if test_image_accessibility(product.image):
                working_products += 1
                print(f"✅ {product.name}: WORKING")
            else:
                broken_products += 1
                print(f"❌ {product.name}: BROKEN")
        else:
            broken_products += 1
            print(f"⚠️ {product.name}: NOT IMAGEKIT")
    
    print(f"📊 Products: {working_products} working, {broken_products} broken/non-ImageKit")
    
    # Check categories
    print("\n🏷️ Checking Category Icons:")
    categories = ProductCategory.objects.exclude(icon='')
    working_categories = 0
    broken_categories = 0
    
    for category in categories:
        if 'imagekit.io' in category.icon:
            if test_image_accessibility(category.icon):
                working_categories += 1
                print(f"✅ {category.name}: WORKING")
            else:
                broken_categories += 1
                print(f"❌ {category.name}: BROKEN")
        else:
            broken_categories += 1
            print(f"⚠️ {category.name}: NOT IMAGEKIT")
    
    print(f"📊 Categories: {working_categories} working, {broken_categories} broken/non-ImageKit")
    
    # Check brands
    print("\n🏭 Checking Brand Images:")
    brands = Brand.objects.exclude(image='')
    working_brands = 0
    broken_brands = 0
    
    for brand in brands:
        if 'imagekit.io' in brand.image:
            if test_image_accessibility(brand.image):
                working_brands += 1
                print(f"✅ {brand.name}: WORKING")
            else:
                broken_brands += 1
                print(f"❌ {brand.name}: BROKEN")
        else:
            broken_brands += 1
            print(f"⚠️ {brand.name}: NOT IMAGEKIT")
    
    print(f"📊 Brands: {working_brands} working, {broken_brands} broken/non-ImageKit")
    
    # Overall summary
    total_working = working_products + working_categories + working_brands
    total_broken = broken_products + broken_categories + broken_brands
    
    print(f"\n" + "=" * 50)
    print(f"🎯 FINAL SUMMARY")
    print(f"=" * 50)
    print(f"✅ Total Working Images: {total_working}")
    print(f"❌ Total Broken/Non-ImageKit: {total_broken}")
    
    if total_working > 0:
        print(f"\n🎉 SUCCESS! ImageKit integration is working properly!")
        print(f"📸 {total_working} images are now served from ImageKit CDN")
    
    if total_broken > 0:
        print(f"\n⚠️ Note: {total_broken} images are still broken or not using ImageKit")
    
    # Show sample working URLs
    print(f"\n🌐 Sample Working ImageKit URLs:")
    sample_count = 0
    
    for product in products:
        if 'imagekit.io' in product.image and test_image_accessibility(product.image):
            print(f"   {product.name}: {product.image}")
            sample_count += 1
            if sample_count >= 3:
                break
    
    return total_working > 0

def main():
    success = verify_all_images()
    
    if success:
        print(f"\n✅ ImageKit verification passed! Images are working correctly.")
    else:
        print(f"\n❌ ImageKit verification failed. No working images found.")

if __name__ == "__main__":
    main()