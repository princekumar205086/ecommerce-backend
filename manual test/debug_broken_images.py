#!/usr/bin/env python
"""
Debug ImageKit upload with detailed analysis
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

def test_image_creation_and_upload():
    """Test creating different types of images and uploading them"""
    print("🔄 Testing Image Creation and Upload with Different Methods")
    
    # Method 1: Create JPEG with high quality
    print("\n📸 Method 1: High Quality JPEG")
    img1 = Image.new('RGB', (300, 300), color='red')
    img1_bytes = BytesIO()
    img1.save(img1_bytes, format='JPEG', quality=95, optimize=True)
    img1_data = img1_bytes.getvalue()
    
    print(f"Image size: {len(img1_data)} bytes")
    
    # Try to verify the image data
    try:
        verify_img = Image.open(BytesIO(img1_data))
        verify_img.verify()
        print(f"✅ Image verification successful: {verify_img.format} {verify_img.size}")
    except Exception as e:
        print(f"❌ Image verification failed: {e}")
        return
    
    # Upload with universal function
    url1 = upload_to_imagekit(img1_data, "debug_test_hq.jpg", "debug")
    print(f"Upload result: {url1}")
    
    if url1:
        # Test with curl-like request to see actual content
        response = requests.get(url1)
        print(f"Response status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Length: {response.headers.get('Content-Length')}")
        
        # Try to open the downloaded image
        try:
            downloaded_img = Image.open(BytesIO(response.content))
            print(f"✅ Downloaded image can be opened: {downloaded_img.format} {downloaded_img.size}")
        except Exception as e:
            print(f"❌ Downloaded image cannot be opened: {e}")
            print(f"First 100 bytes of response: {response.content[:100]}")
    
    # Method 2: Create PNG
    print("\n📸 Method 2: PNG Format")
    img2 = Image.new('RGBA', (200, 200), color='blue')
    img2_bytes = BytesIO()
    img2.save(img2_bytes, format='PNG')
    img2_data = img2_bytes.getvalue()
    
    print(f"Image size: {len(img2_data)} bytes")
    
    url2 = upload_to_imagekit(img2_data, "debug_test.png", "debug")
    print(f"Upload result: {url2}")
    
    if url2:
        response = requests.get(url2)
        print(f"Response status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        try:
            downloaded_img = Image.open(BytesIO(response.content))
            print(f"✅ Downloaded PNG can be opened: {downloaded_img.format} {downloaded_img.size}")
        except Exception as e:
            print(f"❌ Downloaded PNG cannot be opened: {e}")

def test_real_image_file():
    """Test with a real image file from media folder"""
    print("\n🔄 Testing with Real Image File")
    
    # Look for image files in media folder
    media_path = "media"
    if os.path.exists(media_path):
        for root, dirs, files in os.walk(media_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(root, file)
                    print(f"Found image: {image_path}")
                    
                    try:
                        # Read the real image file
                        with open(image_path, 'rb') as f:
                            real_image_data = f.read()
                        
                        print(f"Real image size: {len(real_image_data)} bytes")
                        
                        # Verify it's a valid image
                        verify_img = Image.open(BytesIO(real_image_data))
                        verify_img.verify()
                        print(f"✅ Real image verification: {verify_img.format} {verify_img.size}")
                        
                        # Upload it
                        url = upload_to_imagekit(real_image_data, f"real_{file}", "debug")
                        print(f"Real image upload result: {url}")
                        
                        if url:
                            response = requests.get(url)
                            print(f"Real image response status: {response.status_code}")
                            print(f"Real image Content-Type: {response.headers.get('Content-Type')}")
                            
                            try:
                                downloaded_img = Image.open(BytesIO(response.content))
                                print(f"✅ Downloaded real image works: {downloaded_img.format} {downloaded_img.size}")
                                return url
                            except Exception as e:
                                print(f"❌ Downloaded real image broken: {e}")
                        
                        # Only test first image found
                        break
                    except Exception as e:
                        print(f"❌ Error with real image {image_path}: {e}")
            if files:  # Break outer loop too
                break
    else:
        print("❌ Media folder not found")
    
    return None

def test_imagekit_direct():
    """Test ImageKit SDK directly without our wrapper"""
    print("\n🔄 Testing ImageKit SDK Directly")
    
    from imagekitio import ImageKit
    from dotenv import load_dotenv
    
    load_dotenv()
    
    imagekit = ImageKit(
        private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
        public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
        url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
    )
    
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG', quality=100)
    img_data = img_bytes.getvalue()
    
    try:
        # Upload directly with minimal parameters
        result = imagekit.upload_file(
            file=img_data,
            file_name="direct_test.jpg"
        )
        
        print(f"Direct upload result: {result}")
        print(f"Direct upload URL: {getattr(result, 'url', 'No URL')}")
        
        if hasattr(result, 'url') and result.url:
            response = requests.get(result.url)
            print(f"Direct upload response status: {response.status_code}")
            
            try:
                downloaded_img = Image.open(BytesIO(response.content))
                print(f"✅ Direct upload image works: {downloaded_img.format} {downloaded_img.size}")
                return result.url
            except Exception as e:
                print(f"❌ Direct upload image broken: {e}")
        
    except Exception as e:
        print(f"❌ Direct upload error: {e}")
    
    return None

def main():
    print("🚀 Deep Debugging ImageKit Upload Issues")
    print("=" * 60)
    
    # Test different methods
    test_image_creation_and_upload()
    test_real_image_file()
    working_url = test_imagekit_direct()
    
    print("\n" + "=" * 60)
    print("🔍 ANALYSIS")
    print("=" * 60)
    
    if working_url:
        print(f"✅ Found working URL: {working_url}")
        print("🔧 The issue might be in our wrapper functions or image processing")
    else:
        print("❌ All uploads are producing broken images")
        print("🔧 This suggests an issue with ImageKit configuration or image data")

if __name__ == "__main__":
    main()