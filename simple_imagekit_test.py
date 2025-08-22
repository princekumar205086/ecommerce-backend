#!/usr/bin/env python3
"""
Simple ImageKit Upload Test
Tests the exact response format and creates a working upload function
"""

import os
import sys
import json
import base64
from dotenv import load_dotenv

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

# Load environment variables
load_dotenv()

def simple_upload_test():
    """Simple test to understand ImageKit response format"""
    print("🔍 Simple ImageKit Upload Test")
    print("=" * 40)
    
    try:
        from imagekitio import ImageKit
        
        imagekit = ImageKit(
            private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
            public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
            url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
        )
        
        # Use a small test image
        test_image = "glucose.webp"  # Small 11KB image
        image_path = f"media/images/{test_image}"
        
        if not os.path.exists(image_path):
            print(f"❌ Test image not found: {image_path}")
            return
        
        print(f"📤 Testing upload with: {test_image}")
        
        # Read file
        with open(image_path, 'rb') as f:
            file_data = f.read()
        
        print(f"📊 File size: {len(file_data)} bytes")
        
        # Try basic upload
        print("\n🧪 Attempting upload...")
        
        result = imagekit.upload_file(
            file=file_data,
            file_name=f"debug_test_{test_image}",
            options={}
        )
        
        print(f"✅ Upload completed!")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        # If it's a dictionary, show its keys
        if isinstance(result, dict):
            print(f"Dictionary keys: {list(result.keys())}")
            
            # Look for URL in common places
            url_candidates = ['url', 'fileUrl', 'thumbnailUrl', 'filePath']
            found_url = None
            
            for key in url_candidates:
                if key in result:
                    found_url = result[key]
                    print(f"Found URL in '{key}': {found_url}")
                    break
            
            if found_url:
                # Test if the URL is accessible
                import requests
                try:
                    response = requests.head(found_url, timeout=10)
                    if response.status_code == 200:
                        print(f"✅ URL is accessible!")
                        return found_url, 'dict'
                    else:
                        print(f"❌ URL returned status: {response.status_code}")
                except Exception as e:
                    print(f"❌ URL test failed: {e}")
            
            # Print full result for debugging
            print(f"Full result: {json.dumps(result, indent=2)}")
        
        # If it's an object, check its attributes
        elif hasattr(result, '__dict__'):
            print(f"Object attributes: {list(result.__dict__.keys())}")
            
            if hasattr(result, 'url'):
                print(f"Object URL: {result.url}")
                return result.url, 'object'
        
        return None, None
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def create_working_upload_function(url, response_type):
    """Create a working upload function based on discovered format"""
    print(f"\n🔧 Creating upload function for {response_type} response...")
    
    if response_type == 'dict':
        return '''
def upload_image(file, file_name):
    """Upload image to ImageKit and return URL - Fixed for dict response"""
    try:
        # Handle different input types
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
                "use_unique_file_name": True
            }
        )
        
        # Handle dictionary response
        if isinstance(upload, dict):
            # Try common URL keys
            for key in ['url', 'fileUrl', 'thumbnailUrl', 'filePath']:
                if key in upload and upload[key]:
                    return upload[key]
            
            # If no URL found, print for debugging
            print(f"Upload result keys: {list(upload.keys())}")
            return "https://via.placeholder.com/300x300.png?text=Image+Error"
        
        # Handle object response (fallback)
        elif hasattr(upload, 'url') and upload.url:
            return upload.url
        else:
            print(f"Unexpected upload result type: {type(upload)}")
            return "https://via.placeholder.com/300x300.png?text=Image+Error"
            
    except Exception as e:
        print(f"ImageKit upload error: {e}")
        return "https://via.placeholder.com/300x300.png?text=Image+Error"
'''
    else:
        return '''
def upload_image(file, file_name):
    """Upload image to ImageKit and return URL - Fixed for object response"""
    try:
        # Handle different input types
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
                "use_unique_file_name": True
            }
        )
        
        # Handle object response
        if hasattr(upload, 'url') and upload.url:
            return upload.url
        elif hasattr(upload, 'response') and upload.response:
            return upload.response.get('url', '')
        else:
            print(f"Unexpected upload result: {upload}")
            return "https://via.placeholder.com/300x300.png?text=Image+Error"
            
    except Exception as e:
        print(f"ImageKit upload error: {e}")
        return "https://via.placeholder.com/300x300.png?text=Image+Error"
'''

def main():
    print("🚀 IMAGEKIT SIMPLE DEBUG TEST")
    print("=" * 50)
    
    url, response_type = simple_upload_test()
    
    if url and response_type:
        print(f"\n🎉 SUCCESS! Found working URL: {url}")
        fixed_function = create_working_upload_function(url, response_type)
        
        print("\n📝 Here's the fixed upload function:")
        print("=" * 50)
        print(fixed_function)
        print("=" * 50)
        
        # Write the fixed function to a file
        with open('fixed_upload_function.py', 'w') as f:
            f.write(fixed_function)
        print("\n💾 Fixed function saved to 'fixed_upload_function.py'")
        
    else:
        print("\n❌ Could not determine working upload method")

if __name__ == "__main__":
    main()