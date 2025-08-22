#!/usr/bin/env python
"""
Re-upload all existing images with the fixed base64 method
"""
import os
import sys
import django
import requests
from PIL import Image
from io import BytesIO

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductCategory, Brand
from accounts.models import upload_to_imagekit

def fix_product_images():
    """Fix all broken product images"""
    print("🔄 Fixing Product Images")
    
    products = Product.objects.exclude(image__isnull=True).exclude(image__exact='')
    fixed_count = 0
    failed_count = 0
    
    for product in products:
        if product.image and product.image.startswith('http'):
            try:
                # Download the current broken image
                response = requests.get(product.image, timeout=10)
                if response.status_code == 200 and len(response.content) > 100:
                    # Try to process as image
                    try:
                        img = Image.open(BytesIO(response.content))
                        # Image is already good, skip
                        print(f"✅ Product {product.id} image already working: {product.name}")
                        continue
                    except:
                        pass
                
                # Image is broken, need to find source
                print(f"🔧 Fixing broken image for Product {product.id}: {product.name}")
                
                # Look for source image in media folder
                media_path = "media"
                source_found = False
                
                if os.path.exists(media_path):
                    for root, dirs, files in os.walk(media_path):
                        for file in files:
                            if (file.lower().endswith(('.jpg', '.jpeg', '.png')) and 
                                any(word in file.lower() for word in product.name.lower().split()[:3])):
                                
                                image_path = os.path.join(root, file)
                                try:
                                    with open(image_path, 'rb') as f:
                                        image_data = f.read()
                                    
                                    # Upload with fixed function
                                    new_url = upload_to_imagekit(
                                        image_data, 
                                        f"product_{product.id}_{file}", 
                                        "products/fixed"
                                    )
                                    
                                    if new_url:
                                        product.image = new_url
                                        product.save()
                                        print(f"  ✅ Fixed: {new_url}")
                                        fixed_count += 1
                                        source_found = True
                                        break
                                        
                                except Exception as e:
                                    print(f"  ❌ Error processing {image_path}: {e}")
                        
                        if source_found:
                            break
                
                if not source_found:
                    print(f"  ⚠️ No source image found for {product.name}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ Error fixing product {product.id}: {e}")
                failed_count += 1
    
    print(f"\n📊 Products: {fixed_count} fixed, {failed_count} failed")
    return fixed_count

def fix_category_images():
    """Fix all broken category images"""
    print("\n🔄 Fixing Category Images")
    
    categories = ProductCategory.objects.exclude(icon__isnull=True).exclude(icon__exact='')
    fixed_count = 0
    failed_count = 0
    
    for category in categories:
        if category.icon and category.icon.startswith('http'):
            try:
                # Check if current image works
                response = requests.get(category.icon, timeout=10)
                if response.status_code == 200 and len(response.content) > 100:
                    try:
                        img = Image.open(BytesIO(response.content))
                        print(f"✅ Category {category.id} image already working: {category.name}")
                        continue
                    except:
                        pass
                
                print(f"🔧 Fixing broken image for Category {category.id}: {category.name}")
                
                # Look for source image
                media_path = "media"
                source_found = False
                
                if os.path.exists(media_path):
                    for root, dirs, files in os.walk(media_path):
                        for file in files:
                            if (file.lower().endswith(('.jpg', '.jpeg', '.png')) and 
                                any(word in file.lower() for word in category.name.lower().split()[:2])):
                                
                                image_path = os.path.join(root, file)
                                try:
                                    with open(image_path, 'rb') as f:
                                        image_data = f.read()
                                    
                                    new_url = upload_to_imagekit(
                                        image_data, 
                                        f"category_{category.id}_{file}", 
                                        "categories/fixed"
                                    )
                                    
                                    if new_url:
                                        category.icon = new_url
                                        category.save()
                                        print(f"  ✅ Fixed: {new_url}")
                                        fixed_count += 1
                                        source_found = True
                                        break
                                        
                                except Exception as e:
                                    print(f"  ❌ Error processing {image_path}: {e}")
                        
                        if source_found:
                            break
                
                if not source_found:
                    print(f"  ⚠️ No source image found for {category.name}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ Error fixing category {category.id}: {e}")
                failed_count += 1
    
    print(f"\n📊 Categories: {fixed_count} fixed, {failed_count} failed")
    return fixed_count

def fix_brand_images():
    """Fix all broken brand images"""
    print("\n🔄 Fixing Brand Images")
    
    brands = Brand.objects.exclude(image__isnull=True).exclude(image__exact='')
    fixed_count = 0
    failed_count = 0
    
    for brand in brands:
        if brand.image and brand.image.startswith('http'):
            try:
                # Check if current image works
                response = requests.get(brand.image, timeout=10)
                if response.status_code == 200 and len(response.content) > 100:
                    try:
                        img = Image.open(BytesIO(response.content))
                        print(f"✅ Brand {brand.id} image already working: {brand.name}")
                        continue
                    except:
                        pass
                
                print(f"🔧 Fixing broken image for Brand {brand.id}: {brand.name}")
                
                # Look for source image
                media_path = "media"
                source_found = False
                
                if os.path.exists(media_path):
                    for root, dirs, files in os.walk(media_path):
                        for file in files:
                            if (file.lower().endswith(('.jpg', '.jpeg', '.png')) and 
                                any(word in file.lower() for word in brand.name.lower().split()[:2])):
                                
                                image_path = os.path.join(root, file)
                                try:
                                    with open(image_path, 'rb') as f:
                                        image_data = f.read()
                                    
                                    new_url = upload_to_imagekit(
                                        image_data, 
                                        f"brand_{brand.id}_{file}", 
                                        "brands/fixed"
                                    )
                                    
                                    if new_url:
                                        brand.image = new_url
                                        brand.save()
                                        print(f"  ✅ Fixed: {new_url}")
                                        fixed_count += 1
                                        source_found = True
                                        break
                                        
                                except Exception as e:
                                    print(f"  ❌ Error processing {image_path}: {e}")
                        
                        if source_found:
                            break
                
                if not source_found:
                    print(f"  ⚠️ No source image found for {brand.name}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ Error fixing brand {brand.id}: {e}")
                failed_count += 1
    
    print(f"\n📊 Brands: {fixed_count} fixed, {failed_count} failed")
    return fixed_count

def main():
    print("🚀 FIXING ALL BROKEN IMAGEKIT IMAGES")
    print("=" * 60)
    
    # Fix all types of images
    products_fixed = fix_product_images()
    categories_fixed = fix_category_images()
    brands_fixed = fix_brand_images()
    
    total_fixed = products_fixed + categories_fixed + brands_fixed
    
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    print(f"✅ Total images fixed: {total_fixed}")
    print(f"  - Products: {products_fixed}")
    print(f"  - Categories: {categories_fixed}")
    print(f"  - Brands: {brands_fixed}")
    
    if total_fixed > 0:
        print(f"\n🎉 Successfully fixed {total_fixed} broken images!")
        print("🔧 All images now use the correct base64 upload method.")
    else:
        print("\n✅ No broken images found or all images are already working!")

if __name__ == "__main__":
    main()