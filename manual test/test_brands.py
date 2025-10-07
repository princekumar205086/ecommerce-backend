#!/usr/bin/env python3
"""
Brand Database Test Script
Verifies brand seeding results and image accessibility
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Brand
import requests
from urllib.parse import urlparse
import concurrent.futures
import time

def test_image_url(brand):
    """Test if a brand's image URL is accessible"""
    try:
        if not brand.image:
            return brand.name, False, "No image URL"
        
        # Skip default paths for now
        if brand.image.startswith('/brand/default.png'):
            return brand.name, True, "Static default image"
        
        response = requests.head(brand.image, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                return brand.name, True, f"HTTP {response.status_code} - {content_type}"
            else:
                return brand.name, False, f"HTTP {response.status_code} - Not an image"
        else:
            return brand.name, False, f"HTTP {response.status_code}"
    
    except requests.exceptions.RequestException as e:
        return brand.name, False, f"Request error: {str(e)}"
    except Exception as e:
        return brand.name, False, f"Error: {str(e)}"

def main():
    print("🧪 Testing Brand Database and Images...")
    print("=" * 50)
    
    # Test database connection
    try:
        total_brands = Brand.objects.count()
        print(f"📊 Total brands in database: {total_brands}")
        
        if total_brands == 0:
            print("⚠️ No brands found in database!")
            print("💡 Run: python manage.py seed_brands_production --use-imagekit")
            return
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return
    
    # Get all brands
    brands = Brand.objects.all().order_by('name')
    
    print(f"\n📋 Brand Details:")
    print("-" * 50)
    
    imagekit_count = 0
    static_count = 0
    no_image_count = 0
    
    for brand in brands:
        image_type = "❓ No Image"
        if brand.image:
            if 'imagekit.io' in brand.image:
                image_type = "☁️ ImageKit"
                imagekit_count += 1
            elif brand.image.startswith('/'):
                image_type = "📁 Static"
                static_count += 1
            else:
                image_type = "🔗 Other URL"
        else:
            no_image_count += 1
        
        print(f"{image_type} | {brand.name}")
        if brand.image:
            print(f"     🔗 {brand.image}")
        print()
    
    # Summary
    print("\n📈 Summary:")
    print("-" * 30)
    print(f"☁️ ImageKit URLs: {imagekit_count}")
    print(f"📁 Static URLs: {static_count}")
    print(f"❓ No Image: {no_image_count}")
    print(f"📊 Total: {total_brands}")
    
    # Test image accessibility
    if imagekit_count > 0 or static_count > 0:
        print(f"\n🌐 Testing Image Accessibility...")
        print("-" * 40)
        
        start_time = time.time()
        
        # Test images concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_brand = {
                executor.submit(test_image_url, brand): brand 
                for brand in brands if brand.image and not brand.image.startswith('/brand/default.png')
            }
            
            working_images = 0
            broken_images = 0
            
            for future in concurrent.futures.as_completed(future_to_brand):
                brand_name, is_working, status = future.result()
                
                if is_working:
                    print(f"✅ {brand_name}: {status}")
                    working_images += 1
                else:
                    print(f"❌ {brand_name}: {status}")
                    broken_images += 1
        
        end_time = time.time()
        
        print(f"\n🎯 Image Test Results:")
        print("-" * 30)
        print(f"✅ Working Images: {working_images}")
        print(f"❌ Broken Images: {broken_images}")
        print(f"⏱️ Test Duration: {end_time - start_time:.2f} seconds")
        
        if working_images > 0:
            success_rate = (working_images / (working_images + broken_images)) * 100
            print(f"📊 Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 90:
                print("🎉 Excellent! Almost all images are working!")
            elif success_rate >= 75:
                print("👍 Good! Most images are working!")
            else:
                print("⚠️ Many images have issues. Check ImageKit configuration.")
    
    # Brand distribution check
    print(f"\n📊 Brand Analysis:")
    print("-" * 25)
    
    # Check for medical brands
    medical_brands = ['Cipla', 'Sun Pharma', 'Dr. Reddy\'s', 'Lupin', 'Abbott']
    medical_found = [brand.name for brand in brands if brand.name in medical_brands]
    print(f"💊 Medical Brands Found: {len(medical_found)}/{len(medical_brands)}")
    
    # Check for equipment brands
    equipment_brands = ['Siemens Healthineers', 'GE Healthcare', 'Philips Healthcare', 'Medtronic']
    equipment_found = [brand.name for brand in brands if brand.name in equipment_brands]
    print(f"🏥 Equipment Brands Found: {len(equipment_found)}/{len(equipment_brands)}")
    
    # Check for personal care brands
    personal_care_brands = ['Johnson & Johnson', 'Unilever', 'Colgate-Palmolive', 'Mamaearth']
    personal_care_found = [brand.name for brand in brands if brand.name in personal_care_brands]
    print(f"🧴 Personal Care Brands Found: {len(personal_care_found)}/{len(personal_care_brands)}")
    
    print(f"\n✅ Brand database test completed!")
    
    if total_brands >= 20 and (imagekit_count > 0 or static_count > 0):
        print("🎉 Brand seeding appears successful!")
    else:
        print("⚠️ Brand seeding may need attention.")
        print("💡 Suggestions:")
        print("   - Run seeder with --use-imagekit for cloud images")
        print("   - Check ImageKit credentials if using cloud storage")
        print("   - Verify brand.json file exists and is valid")

if __name__ == "__main__":
    main()
