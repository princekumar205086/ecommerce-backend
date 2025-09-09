#!/usr/bin/env python3
"""
ImageKit Upload Test Script
Tests if images are actually uploading to ImageKit server and not broken
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import upload_to_imagekit
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_imagekit_config():
    """Test ImageKit configuration"""
    print("🔧 ImageKit Configuration Test")
    print("=" * 50)
    
    url_endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT')
    public_key = os.environ.get('IMAGEKIT_PUBLIC_KEY')
    private_key = os.environ.get('IMAGEKIT_PRIVATE_KEY')
    
    print(f"URL Endpoint: {url_endpoint}")
    print(f"Public Key: {public_key[:20] + '...' if public_key else 'NOT SET'}")
    print(f"Private Key: {'SET' if private_key else 'NOT SET'}")
    
    if not all([url_endpoint, public_key, private_key]):
        print("❌ ImageKit configuration incomplete!")
        return False
    
    print("✅ ImageKit configuration looks complete")
    return True


def test_local_image_upload():
    """Test uploading a local image to ImageKit"""
    print("\n📸 Local Image Upload Test")
    print("=" * 50)
    
    # Test with existing default.png
    image_path = project_root / 'media' / 'categories' / 'default.png'
    
    if not image_path.exists():
        print(f"❌ Test image not found: {image_path}")
        return False
    
    print(f"📁 Found test image: {image_path}")
    print(f"📏 File size: {image_path.stat().st_size} bytes")
    
    try:
        # Read the image
        with open(image_path, 'rb') as f:
            file_bytes = f.read()
        
        print(f"✅ Successfully read {len(file_bytes)} bytes")
        
        # Upload to ImageKit
        print("🚀 Uploading to ImageKit...")
        image_url = upload_to_imagekit(file_bytes, 'test_default.png', folder="categories")
        
        if image_url:
            print(f"✅ Upload successful!")
            print(f"🔗 Image URL: {image_url}")
            return image_url
        else:
            print("❌ Upload failed - no URL returned")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return None


def test_imagekit_direct():
    """Test ImageKit directly without our wrapper"""
    print("\n🔄 Direct ImageKit Test")
    print("=" * 50)
    
    try:
        from imagekitio import ImageKit
        
        imagekit = ImageKit(
            private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
            public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
            url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
        )
        
        # Create a simple test image data
        import base64
        from PIL import Image
        from io import BytesIO
        
        # Create a simple 100x100 red square
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        
        # Convert to base64
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        data_url = f"data:image/png;base64,{img_b64}"
        
        print("🎨 Created test image (100x100 red square)")
        print("🚀 Uploading directly to ImageKit...")
        
        # Upload directly
        upload_response = imagekit.upload_file(
            file=data_url,
            file_name="categories/direct_test.png"
        )
        
        print(f"📥 Response type: {type(upload_response)}")
        print(f"📥 Response attributes: {dir(upload_response)}")
        
        if hasattr(upload_response, 'url'):
            print(f"✅ Direct upload successful!")
            print(f"🔗 Image URL: {upload_response.url}")
            return upload_response.url
        else:
            print(f"❌ No URL in response: {upload_response}")
            return None
            
    except Exception as e:
        print(f"❌ Direct upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def verify_uploaded_image(image_url):
    """Verify if the uploaded image is accessible"""
    print(f"\n🔍 Image Verification Test")
    print("=" * 50)
    
    if not image_url:
        print("❌ No image URL to verify")
        return False
    
    try:
        import requests
        
        print(f"🌐 Testing URL: {image_url}")
        
        # Make a HEAD request to check if image exists
        response = requests.head(image_url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Content Type: {response.headers.get('content-type', 'Unknown')}")
        print(f"📊 Content Length: {response.headers.get('content-length', 'Unknown')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                print("✅ Image is accessible and valid!")
                return True
            else:
                print(f"⚠️  URL accessible but not an image: {content_type}")
                return False
        else:
            print(f"❌ Image not accessible: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
        return False


def main():
    print("🖼️  ImageKit Upload Test Suite")
    print("=" * 60)
    
    # Test 1: Configuration
    if not test_imagekit_config():
        print("\n❌ Cannot proceed - ImageKit not configured properly")
        return
    
    # Test 2: Local image upload
    local_url = test_local_image_upload()
    
    # Test 3: Direct ImageKit test
    direct_url = test_imagekit_direct()
    
    # Test 4: Verify uploaded images
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    if local_url:
        print(f"🔗 Local upload URL: {local_url}")
        verify_uploaded_image(local_url)
    
    if direct_url:
        print(f"🔗 Direct upload URL: {direct_url}")
        verify_uploaded_image(direct_url)
    
    # Final recommendation
    print("\n💡 RECOMMENDATIONS:")
    if local_url or direct_url:
        print("✅ ImageKit is working - images are uploading successfully")
        print("🔧 If you see broken images in browser:")
        print("   - Check if the ImageKit URL endpoint is correct")
        print("   - Verify ImageKit account permissions")
        print("   - Test URLs directly in browser")
    else:
        print("❌ ImageKit uploads are failing")
        print("🔧 Check:")
        print("   - ImageKit credentials in .env file")
        print("   - Internet connection")
        print("   - ImageKit account status")


if __name__ == '__main__':
    main()
