#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

# Check ImageKit configuration
from dotenv import load_dotenv
load_dotenv()

print("🔍 Checking ImageKit Configuration")
print("=" * 60)

imagekit_private = os.environ.get('IMAGEKIT_PRIVATE_KEY')
imagekit_public = os.environ.get('IMAGEKIT_PUBLIC_KEY')
imagekit_endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT')

print(f"IMAGEKIT_PRIVATE_KEY: {'✅ Set' if imagekit_private else '❌ Not set'}")
print(f"IMAGEKIT_PUBLIC_KEY: {'✅ Set' if imagekit_public else '❌ Not set'}")
print(f"IMAGEKIT_URL_ENDPOINT: {'✅ Set' if imagekit_endpoint else '❌ Not set'}")

if imagekit_endpoint:
    print(f"  → Endpoint: {imagekit_endpoint}")

# Test ImageKit connection
print("\n🧪 Testing ImageKit Connection")
print("=" * 60)

try:
    from imagekitio import ImageKit
    
    imagekit = ImageKit(
        private_key=imagekit_private,
        public_key=imagekit_public,
        url_endpoint=imagekit_endpoint
    )
    
    # Try to get account details (non-destructive test)
    account_info = imagekit.get_account_details()
    
    if account_info and hasattr(account_info, 'response'):
        print("✅ ImageKit connection successful")
        if isinstance(account_info.response, dict):
            print(f"  Account: {account_info.response.get('name', 'Unknown')}")
    else:
        print("⚠️  ImageKit connected but no account info")
        
except Exception as e:
    print(f"❌ ImageKit connection failed: {str(e)[:100]}")

# Test upload_to_imagekit function
print("\n🧪 Testing upload_to_imagekit Function")
print("=" * 60)

try:
    from accounts.models import upload_to_imagekit
    from PIL import Image
    from io import BytesIO
    
    # Create a simple test image
    img = Image.new('RGB', (10, 10), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes = img_bytes.getvalue()
    
    print(f"Created test image: {len(img_bytes)} bytes")
    
    # Try to upload
    result = upload_to_imagekit(img_bytes, "test_image.jpg", folder="carousel_banners")
    
    if result:
        print(f"✅ Upload successful")
        print(f"  URL: {result}")
    else:
        print(f"❌ Upload returned None (no error, but no URL)")
        
except Exception as e:
    print(f"❌ Upload error: {str(e)[:100]}")

print("\n" + "=" * 60)
print("Note: If ImageKit credentials are not set in .env,")
print("the upload will return None. Configure IMAGEKIT_* vars.")
