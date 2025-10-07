#!/usr/bin/env python3
"""
Server ImageKit Configuration Checker
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

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_server_config():
    print("🔧 Server ImageKit Configuration Check")
    print("=" * 60)
    
    # Check environment variables
    url_endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT')
    public_key = os.environ.get('IMAGEKIT_PUBLIC_KEY')
    private_key = os.environ.get('IMAGEKIT_PRIVATE_KEY')
    
    print("📋 Environment Variables:")
    print(f"   IMAGEKIT_URL_ENDPOINT: {url_endpoint or 'NOT SET'}")
    print(f"   IMAGEKIT_PUBLIC_KEY: {public_key[:20] + '...' if public_key else 'NOT SET'}")
    print(f"   IMAGEKIT_PRIVATE_KEY: {'SET' if private_key else 'NOT SET'}")
    
    # Check media directory structure
    print(f"\n📁 Media Directory Check:")
    media_root = Path('/srv/backend/media')
    categories_dir = media_root / 'categories'
    
    print(f"   Media root exists: {media_root.exists()}")
    print(f"   Categories dir exists: {categories_dir.exists()}")
    
    if categories_dir.exists():
        images = list(categories_dir.glob('*.png'))
        print(f"   Images found: {len(images)}")
        for img in images[:5]:  # Show first 5
            print(f"     - {img.name}")
        if len(images) > 5:
            print(f"     ... and {len(images) - 5} more")
    else:
        print("   ❌ Categories directory doesn't exist!")
    
    # Test ImageKit connection
    print(f"\n🔗 ImageKit Connection Test:")
    if all([url_endpoint, public_key, private_key]):
        try:
            from imagekitio import ImageKit
            
            imagekit = ImageKit(
                private_key=private_key,
                public_key=public_key,
                url_endpoint=url_endpoint
            )
            
            # Try to list files to test connection
            try:
                result = imagekit.list_files(limit=1)
                print("   ✅ ImageKit connection successful!")
                print(f"   📊 Account has files: {len(result.list) if hasattr(result, 'list') else 'Unknown'}")
            except Exception as e:
                print(f"   ❌ ImageKit connection failed: {str(e)}")
                
        except Exception as e:
            print(f"   ❌ ImageKit import/setup failed: {str(e)}")
    else:
        print("   ❌ ImageKit credentials incomplete")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not all([url_endpoint, public_key, private_key]):
        print("   1. ❌ Update .env file with new ImageKit credentials")
        print("   2. 🔄 Restart Django/Gunicorn after updating .env")
    
    if not categories_dir.exists():
        print("   3. 📁 Create categories directory and upload default images")
        print("   4. 🖼️  Or use the non-upload seeder for static paths")
    
    print("   5. 🧪 Test with a simple upload before running full seeder")

if __name__ == '__main__':
    check_server_config()
