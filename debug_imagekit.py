#!/usr/bin/env python3
"""
ImageKit Upload Debug and Fix
Tests and fixes image upload issues to ensure proper file upload
"""

import os
import sys
import base64
import mimetypes
import requests
from dotenv import load_dotenv

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

# Load environment variables
load_dotenv()

def test_imagekit_config():
    """Test ImageKit configuration"""
    print("🔧 Testing ImageKit Configuration...")
    
    private_key = os.environ.get('IMAGEKIT_PRIVATE_KEY')
    public_key = os.environ.get('IMAGEKIT_PUBLIC_KEY')
    url_endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT')
    
    print(f"Private Key: {'✅ Found' if private_key else '❌ Missing'}")
    print(f"Public Key: {'✅ Found' if public_key else '❌ Missing'}")
    print(f"URL Endpoint: {url_endpoint}")
    
    return private_key and public_key and url_endpoint

def test_image_file_integrity():
    """Test if image files are valid"""
    print("\n📁 Testing Image File Integrity...")
    
    images_dir = "media/images"
    valid_images = []
    invalid_images = []
    
    if not os.path.exists(images_dir):
        print(f"❌ Images directory not found: {images_dir}")
        return []
    
    for filename in os.listdir(images_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif')):
            image_path = os.path.join(images_dir, filename)
            
            try:
                # Check file size
                file_size = os.path.getsize(image_path)
                if file_size == 0:
                    print(f"❌ {filename}: Empty file")
                    invalid_images.append(filename)
                    continue
                
                # Check if we can read the file
                with open(image_path, 'rb') as f:
                    file_data = f.read(100)  # Read first 100 bytes
                    if len(file_data) < 10:
                        print(f"❌ {filename}: Too small ({file_size} bytes)")
                        invalid_images.append(filename)
                        continue
                
                # Check MIME type
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type or not mime_type.startswith('image/'):
                    print(f"⚠️ {filename}: Unknown MIME type ({mime_type})")
                
                print(f"✅ {filename}: Valid ({file_size} bytes, {mime_type})")
                valid_images.append(filename)
                
            except Exception as e:
                print(f"❌ {filename}: Error reading file - {e}")
                invalid_images.append(filename)
    
    print(f"\n📊 Summary: {len(valid_images)} valid, {len(invalid_images)} invalid")
    return valid_images

def upload_with_base64(file_path, file_name):
    """Upload image using base64 encoding method"""
    try:
        from imagekitio import ImageKit
        
        imagekit = ImageKit(
            private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
            public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
            url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
        )
        
        # Read file and encode as base64
        with open(file_path, 'rb') as image_file:
            file_data = image_file.read()
            
        # Encode as base64
        base64_data = base64.b64encode(file_data).decode('utf-8')
        
        # Upload using base64
        upload_result = imagekit.upload_file(
            file=base64_data,
            file_name=file_name,
            options={
                "folder": "/medixmall/products/",
                "use_unique_file_name": True,
                "response_fields": ["is_private_file", "tags", "custom_coordinates"]
            }
        )
        
        return upload_result
        
    except Exception as e:
        print(f"Base64 upload error: {e}")
        return None

def upload_with_file_object(file_path, file_name):
    """Upload image using file object method"""
    try:
        from imagekitio import ImageKit
        
        imagekit = ImageKit(
            private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
            public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
            url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
        )
        
        # Upload using file object
        with open(file_path, 'rb') as image_file:
            upload_result = imagekit.upload_file(
                file=image_file,
                file_name=file_name,
                options={
                    "folder": "/medixmall/products/",
                    "use_unique_file_name": True,
                    "response_fields": ["is_private_file", "tags", "custom_coordinates"]
                }
            )
        
        return upload_result
        
    except Exception as e:
        print(f"File object upload error: {e}")
        return None

def upload_with_bytes(file_path, file_name):
    """Upload image using bytes method"""
    try:
        from imagekitio import ImageKit
        
        imagekit = ImageKit(
            private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
            public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
            url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
        )
        
        # Read file as bytes
        with open(file_path, 'rb') as image_file:
            file_bytes = image_file.read()
        
        # Upload using bytes
        upload_result = imagekit.upload_file(
            file=file_bytes,
            file_name=file_name,
            options={
                "folder": "/medixmall/products/",
                "use_unique_file_name": True,
                "response_fields": ["is_private_file", "tags", "custom_coordinates"]
            }
        )
        
        return upload_result
        
    except Exception as e:
        print(f"Bytes upload error: {e}")
        return None

def test_image_accessibility(url):
    """Test if uploaded image is accessible"""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def comprehensive_upload_test():
    """Test different upload methods to find the working one"""
    print("\n🧪 Comprehensive Upload Test...")
    
    if not test_imagekit_config():
        print("❌ ImageKit configuration failed")
        return
    
    valid_images = test_image_file_integrity()
    if not valid_images:
        print("❌ No valid images found")
        return
    
    # Test with a small, reliable image first
    test_image = None
    for img in valid_images:
        if img.lower().endswith('.png') and os.path.getsize(f"media/images/{img}") < 100000:  # Less than 100KB
            test_image = img
            break
    
    if not test_image:
        test_image = valid_images[0]  # Use first available
    
    print(f"\n🎯 Testing with: {test_image}")
    image_path = f"media/images/{test_image}"
    
    methods = [
        ("Base64 Method", upload_with_base64),
        ("File Object Method", upload_with_file_object),
        ("Bytes Method", upload_with_bytes)
    ]
    
    successful_method = None
    successful_url = None
    
    for method_name, upload_func in methods:
        print(f"\n📤 Testing {method_name}...")
        
        try:
            result = upload_func(image_path, f"test_{method_name.lower().replace(' ', '_')}_{test_image}")
            
            if result:
                print(f"Upload result type: {type(result)}")
                print(f"Upload result: {result}")
                
                # Extract URL
                url = None
                if hasattr(result, 'url'):
                    url = result.url
                elif hasattr(result, 'response') and result.response:
                    url = result.response.get('url')
                
                if url:
                    print(f"URL: {url}")
                    
                    # Test accessibility
                    if test_image_accessibility(url):
                        print(f"✅ {method_name} SUCCESS - Image accessible!")
                        successful_method = method_name
                        successful_url = url
                        break
                    else:
                        print(f"❌ {method_name} FAILED - Image not accessible")
                else:
                    print(f"❌ {method_name} FAILED - No URL returned")
            else:
                print(f"❌ {method_name} FAILED - No result")
                
        except Exception as e:
            print(f"❌ {method_name} ERROR: {e}")
    
    if successful_method:
        print(f"\n🎉 SUCCESS! {successful_method} works correctly")
        print(f"📸 Working URL: {successful_url}")
        return successful_method
    else:
        print(f"\n💥 ALL METHODS FAILED!")
        return None

def create_fixed_upload_function(working_method):
    """Create a fixed upload function based on working method"""
    print(f"\n🔧 Creating fixed upload function using {working_method}...")
    
    if "base64" in working_method.lower():
        fixed_function = '''
def upload_image(file, file_name):
    """Upload image to ImageKit using base64 method"""
    import base64
    try:
        # If file is already bytes, use it directly
        if isinstance(file, bytes):
            file_data = file
        else:
            # If file is file object, read it
            file_data = file.read()
        
        # Encode as base64
        base64_data = base64.b64encode(file_data).decode('utf-8')
        
        upload = imagekit.upload_file(
            file=base64_data,
            file_name=file_name,
            options={
                "folder": "/medixmall/products/",
                "use_unique_file_name": True,
                "response_fields": ["is_private_file", "tags", "custom_coordinates"]
            }
        )
        
        if hasattr(upload, 'url') and upload.url:
            return upload.url
        elif hasattr(upload, 'response') and upload.response:
            return upload.response.get('url', '')
        else:
            return upload.get('url', '')
            
    except Exception as e:
        print(f"ImageKit upload error: {e}")
        return "https://via.placeholder.com/300x300.png?text=Image+Error"
'''
    elif "file object" in working_method.lower():
        fixed_function = '''
def upload_image(file, file_name):
    """Upload image to ImageKit using file object method"""
    try:
        # If file is bytes, we need to create a BytesIO object
        if isinstance(file, bytes):
            from io import BytesIO
            file_obj = BytesIO(file)
        else:
            file_obj = file
        
        upload = imagekit.upload_file(
            file=file_obj,
            file_name=file_name,
            options={
                "folder": "/medixmall/products/",
                "use_unique_file_name": True,
                "response_fields": ["is_private_file", "tags", "custom_coordinates"]
            }
        )
        
        if hasattr(upload, 'url') and upload.url:
            return upload.url
        elif hasattr(upload, 'response') and upload.response:
            return upload.response.get('url', '')
        else:
            return upload.get('url', '')
            
    except Exception as e:
        print(f"ImageKit upload error: {e}")
        return "https://via.placeholder.com/300x300.png?text=Image+Error"
'''
    else:  # bytes method
        fixed_function = '''
def upload_image(file, file_name):
    """Upload image to ImageKit using bytes method"""
    try:
        # If file is already bytes, use it directly
        if isinstance(file, bytes):
            file_data = file
        else:
            # If file is file object, read it
            file_data = file.read()
        
        upload = imagekit.upload_file(
            file=file_data,
            file_name=file_name,
            options={
                "folder": "/medixmall/products/",
                "use_unique_file_name": True,
                "response_fields": ["is_private_file", "tags", "custom_coordinates"]
            }
        )
        
        if hasattr(upload, 'url') and upload.url:
            return upload.url
        elif hasattr(upload, 'response') and upload.response:
            return upload.response.get('url', '')
        else:
            return upload.get('url', '')
            
    except Exception as e:
        print(f"ImageKit upload error: {e}")
        return "https://via.placeholder.com/300x300.png?text=Image+Error"
'''
    
    return fixed_function

def main():
    print("🚀 IMAGEKIT UPLOAD DEBUG AND FIX")
    print("=" * 50)
    
    working_method = comprehensive_upload_test()
    
    if working_method:
        fixed_function = create_fixed_upload_function(working_method)
        print("\n📝 Fixed upload function created!")
        print("Copy this function to products/utils/imagekit.py")
        print("\n" + "="*50)
        print(fixed_function)
        print("="*50)
    else:
        print("\n❌ Could not find a working upload method")
        print("Please check ImageKit credentials and try again")

if __name__ == "__main__":
    main()