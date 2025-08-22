#!/usr/bin/env python
"""
Test the fixed ImageKit upload functions using base64 encoding
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

from accounts.models import upload_to_imagekit
from products.utils.imagekit import upload_image

def test_fixed_uploads():
    """Test the fixed upload functions"""
    print("🚀 Testing Fixed ImageKit Upload Functions")
    print("=" * 60)
    
    # Test 1: Universal upload function
    print("\n🔄 Test 1: Universal Upload Function (base64)")
    img1 = Image.new('RGB', (300, 300), color='blue')
    img1_bytes = BytesIO()
    img1.save(img1_bytes, format='JPEG', quality=95)
    img1_data = img1_bytes.getvalue()
    
    url1 = upload_to_imagekit(img1_data, "fixed_universal_test.jpg", "fixed_tests")
    if url1:
        print(f"✅ Universal upload URL: {url1}")
        test_image_in_browser(url1, "Universal Upload")
    else:
        print(f"❌ Universal upload failed")
    
    # Test 2: Products upload function
    print("\n🔄 Test 2: Products Upload Function (base64)")
    img2 = Image.new('RGB', (400, 400), color='green')
    img2_bytes = BytesIO()
    img2.save(img2_bytes, format='JPEG', quality=95)
    img2_bytes.seek(0)
    
    url2 = upload_image(img2_bytes, "fixed_products_test.jpg", "fixed_tests")
    if url2:
        print(f"✅ Products upload URL: {url2}")
        test_image_in_browser(url2, "Products Upload")
    else:
        print(f"❌ Products upload failed")
    
    # Test 3: PNG upload
    print("\n🔄 Test 3: PNG Upload")
    img3 = Image.new('RGBA', (200, 200), color='red')
    img3_bytes = BytesIO()
    img3.save(img3_bytes, format='PNG')
    img3_data = img3_bytes.getvalue()
    
    url3 = upload_to_imagekit(img3_data, "fixed_png_test.png", "fixed_tests")
    if url3:
        print(f"✅ PNG upload URL: {url3}")
        test_image_in_browser(url3, "PNG Upload")
    else:
        print(f"❌ PNG upload failed")
    
    return [url1, url2, url3]

def test_image_in_browser(url, test_name):
    """Test if the image actually displays properly"""
    try:
        response = requests.get(url, timeout=10)
        print(f"  📊 {test_name} - Status: {response.status_code}, Size: {len(response.content)} bytes")
        
        if response.status_code == 200 and len(response.content) > 100:
            # Try to open as image
            img = Image.open(BytesIO(response.content))
            print(f"  ✅ {test_name} - Valid image: {img.format} {img.size}")
            return True
        else:
            print(f"  ❌ {test_name} - Invalid response")
            return False
            
    except Exception as e:
        print(f"  ❌ {test_name} - Error: {e}")
        return False

def test_real_media_images():
    """Test with real images from media folder"""
    print("\n🔄 Testing with Real Media Images")
    
    media_path = "media"
    if os.path.exists(media_path):
        for root, dirs, files in os.walk(media_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(root, file)
                    print(f"\n📸 Testing real image: {file}")
                    
                    try:
                        # Read the real image file
                        with open(image_path, 'rb') as f:
                            real_image_data = f.read()
                        
                        # Upload it with fixed function
                        url = upload_to_imagekit(real_image_data, f"real_fixed_{file}", "fixed_tests")
                        
                        if url:
                            print(f"✅ Real image upload successful: {url}")
                            if test_image_in_browser(url, f"Real {file}"):
                                return url
                        else:
                            print(f"❌ Real image upload failed")
                        
                        # Only test first image found
                        break
                    except Exception as e:
                        print(f"❌ Error with real image {image_path}: {e}")
            if files:  # Break outer loop too
                break
    
    return None

def main():
    print("🎯 TESTING FIXED IMAGEKIT UPLOAD FUNCTIONS")
    print("=" * 80)
    
    # Test fixed functions
    test_urls = test_fixed_uploads()
    
    # Test with real images
    real_url = test_real_media_images()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    
    working_urls = [url for url in test_urls if url]
    
    print(f"✅ Working URLs: {len(working_urls)}/3")
    
    for i, url in enumerate(working_urls):
        print(f"  {i+1}. {url}")
    
    if real_url:
        print(f"✅ Real image URL: {real_url}")
    
    if len(working_urls) == 3 and real_url:
        print("\n🎉 ALL TESTS PASSED! ImageKit upload is now working perfectly!")
        print("🔧 The fix was using base64 encoding instead of binary uploads.")
    elif len(working_urls) > 0:
        print("\n⚠️ Some tests passed. ImageKit is partially working.")
    else:
        print("\n🚨 All tests failed. Check the implementation.")

if __name__ == "__main__":
    main()