#!/usr/bin/env python
"""
Fix ImageKit upload by testing different upload parameters and configurations
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

def test_imagekit_with_different_params():
    """Test ImageKit with different parameter combinations"""
    print("🔄 Testing ImageKit with Different Parameters")
    
    from imagekitio import ImageKit
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print(f"ImageKit URL Endpoint: {os.environ.get('IMAGEKIT_URL_ENDPOINT')}")
    print(f"ImageKit Public Key: {os.environ.get('IMAGEKIT_PUBLIC_KEY')[:10]}...")
    print(f"ImageKit Private Key: {'*' * 20}")
    
    imagekit = ImageKit(
        private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
        public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
        url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
    )
    
    # Create a simple test image
    img = Image.new('RGB', (200, 200), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    img_data = img_bytes.getvalue()
    
    print(f"Original image size: {len(img_data)} bytes")
    
    # Test 1: Minimal parameters
    print("\n🧪 Test 1: Minimal parameters")
    try:
        result1 = imagekit.upload_file(
            file=img_data,
            file_name="test_minimal.jpg"
        )
        print(f"✅ Minimal upload successful: {result1.url}")
        test_image_url(result1.url, "minimal")
    except Exception as e:
        print(f"❌ Minimal upload failed: {e}")
    
    # Test 2: With folder parameter as string
    print("\n🧪 Test 2: With folder in file_name")
    try:
        result2 = imagekit.upload_file(
            file=img_data,
            file_name="test_folder/test_folder.jpg"
        )
        print(f"✅ Folder upload successful: {result2.url}")
        test_image_url(result2.url, "folder")
    except Exception as e:
        print(f"❌ Folder upload failed: {e}")
    
    # Test 3: With use_unique_file_name
    print("\n🧪 Test 3: With use_unique_file_name")
    try:
        result3 = imagekit.upload_file(
            file=img_data,
            file_name="test_unique.jpg",
            options={
                "use_unique_file_name": True
            }
        )
        print(f"✅ Unique name upload successful: {result3.url}")
        test_image_url(result3.url, "unique")
    except Exception as e:
        print(f"❌ Unique name upload failed: {e}")
    
    # Test 4: Using base64 encoding
    print("\n🧪 Test 4: Using base64 encoding")
    try:
        import base64
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        result4 = imagekit.upload_file(
            file=f"data:image/jpeg;base64,{img_b64}",
            file_name="test_b64.jpg"
        )
        print(f"✅ Base64 upload successful: {result4.url}")
        test_image_url(result4.url, "base64")
    except Exception as e:
        print(f"❌ Base64 upload failed: {e}")

def test_image_url(url, test_name):
    """Test if an image URL actually works"""
    try:
        response = requests.get(url, timeout=10)
        print(f"  📊 {test_name} - Status: {response.status_code}, Size: {len(response.content)} bytes")
        
        if len(response.content) < 100:
            print(f"  ❌ {test_name} - Response too small: {response.content}")
            return False
        
        # Try to open as image
        img = Image.open(BytesIO(response.content))
        print(f"  ✅ {test_name} - Valid image: {img.format} {img.size}")
        return True
        
    except Exception as e:
        print(f"  ❌ {test_name} - Error: {e}")
        return False

def test_working_imagekit_example():
    """Test with a known working example from ImageKit documentation"""
    print("\n🔄 Testing with Known Working Example")
    
    from imagekitio import ImageKit
    from dotenv import load_dotenv
    
    load_dotenv()
    
    imagekit = ImageKit(
        private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
        public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
        url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
    )
    
    # Create a very simple image
    from PIL import Image, ImageDraw
    
    # Create image with text to verify it's working
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Test Image", fill='black')
    
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG', quality=100)
    img_data = img_bytes.getvalue()
    
    print(f"Test image size: {len(img_data)} bytes")
    
    try:
        # Upload with the exact format from ImageKit docs
        upload_result = imagekit.upload_file(
            file=img_data,
            file_name="working_test.jpg"
        )
        
        print(f"Upload response: {upload_result}")
        
        if hasattr(upload_result, 'url'):
            print(f"Upload URL: {upload_result.url}")
            return test_image_url(upload_result.url, "working_example")
        else:
            print(f"No URL in response: {dir(upload_result)}")
            
    except Exception as e:
        print(f"Working example failed: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def check_imagekit_account():
    """Check if ImageKit account is properly configured"""
    print("\n🔄 Checking ImageKit Account Configuration")
    
    from imagekitio import ImageKit
    from dotenv import load_dotenv
    
    load_dotenv()
    
    imagekit = ImageKit(
        private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
        public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
        url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
    )
    
    try:
        # Try to list files (this tests authentication)
        file_list = imagekit.list_files()
        print(f"✅ Authentication successful. Found {len(file_list.list)} files")
        
        # Show some recent files
        if file_list.list:
            print("Recent files:")
            for file_info in file_list.list[:3]:
                print(f"  - {file_info.name}: {file_info.url}")
                
                # Test if these files work
                if test_image_url(file_info.url, f"existing_{file_info.name}"):
                    print(f"    ✅ Existing file works!")
                    return True
                else:
                    print(f"    ❌ Existing file broken!")
        
    except Exception as e:
        print(f"❌ Authentication or listing failed: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def main():
    print("🚀 Comprehensive ImageKit Debugging")
    print("=" * 60)
    
    # Check account first
    account_ok = check_imagekit_account()
    
    # Test different upload methods
    test_imagekit_with_different_params()
    
    # Test working example
    working_example = test_working_imagekit_example()
    
    print("\n" + "=" * 60)
    print("🔍 FINAL ANALYSIS")
    print("=" * 60)
    
    if account_ok:
        print("✅ ImageKit account is properly configured")
    else:
        print("❌ ImageKit account configuration issues")
    
    if working_example:
        print("✅ Found a working upload method")
    else:
        print("❌ All upload methods are failing")
        print("🔧 This suggests a deeper issue with ImageKit configuration or account")

if __name__ == "__main__":
    main()