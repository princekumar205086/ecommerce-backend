#!/usr/bin/env python3
"""
ImageKit Upload Debug and Test Script
Tests image uploads and verifies URLs work properly
"""

import os
import django
import sys
import requests
from io import BytesIO

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.utils.imagekit import upload_image


class ImageKitDebugger:
    def __init__(self):
        self.test_results = []
        
    def test_image_upload_comprehensive(self):
        """Test image upload with comprehensive debugging"""
        print("🔍 COMPREHENSIVE IMAGEKIT UPLOAD DEBUG")
        print("=" * 60)
        
        # Test different image formats
        test_images = [
            'medicine.png',
            'glucose.webp', 
            'medixmall.jpg',
            'doctor-equipment.png',
            'BpMonitor.webp'
        ]
        
        for image_name in test_images:
            print(f"\n📷 Testing: {image_name}")
            image_path = f"media/images/{image_name}"
            
            if not os.path.exists(image_path):
                print(f"❌ File not found: {image_path}")
                continue
                
            try:
                # Get file info
                file_size = os.path.getsize(image_path)
                print(f"📊 File size: {file_size} bytes")
                
                # Read and upload
                with open(image_path, 'rb') as image_file:
                    image_data = image_file.read()
                    print(f"📖 Read {len(image_data)} bytes")
                    
                    # Test upload
                    uploaded_url = upload_image(image_data, f"test_{image_name}")
                    print(f"🔗 Upload result: {uploaded_url}")
                    
                    # Test URL accessibility
                    if 'imagekit.io' in uploaded_url:
                        try:
                            response = requests.head(uploaded_url, timeout=10)
                            print(f"🌐 URL Status: {response.status_code}")
                            print(f"📋 Content-Type: {response.headers.get('content-type', 'Unknown')}")
                            print(f"📏 Content-Length: {response.headers.get('content-length', 'Unknown')}")
                            
                            if response.status_code == 200:
                                print(f"✅ URL is accessible")
                                self.test_results.append({
                                    'image': image_name,
                                    'url': uploaded_url,
                                    'status': 'SUCCESS',
                                    'accessible': True
                                })
                            else:
                                print(f"❌ URL not accessible")
                                self.test_results.append({
                                    'image': image_name,
                                    'url': uploaded_url,
                                    'status': 'UPLOAD_SUCCESS_BUT_NOT_ACCESSIBLE',
                                    'accessible': False
                                })
                                
                        except requests.RequestException as e:
                            print(f"❌ URL test failed: {e}")
                            self.test_results.append({
                                'image': image_name,
                                'url': uploaded_url,
                                'status': 'URL_TEST_FAILED',
                                'accessible': False
                            })
                    else:
                        print(f"❌ Not an ImageKit URL")
                        self.test_results.append({
                            'image': image_name,
                            'url': uploaded_url,
                            'status': 'NOT_IMAGEKIT_URL',
                            'accessible': False
                        })
                        
            except Exception as e:
                print(f"❌ Upload failed: {e}")
                self.test_results.append({
                    'image': image_name,
                    'url': '',
                    'status': f'FAILED: {str(e)}',
                    'accessible': False
                })
    
    def test_imagekit_direct(self):
        """Test ImageKit SDK directly"""
        print(f"\n🔧 TESTING IMAGEKIT SDK DIRECTLY")
        print("=" * 40)
        
        try:
            from imagekitio import ImageKit
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            
            imagekit = ImageKit(
                private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
                public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
                url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
            )
            
            # Test with a simple image
            test_image_path = "media/images/medicine.png"
            if os.path.exists(test_image_path):
                with open(test_image_path, 'rb') as img_file:
                    # Test direct upload
                    upload_result = imagekit.upload_file(
                        file=img_file.read(),
                        file_name="direct_test_medicine.png"
                    )
                    
                    print(f"📤 Direct upload result type: {type(upload_result)}")
                    print(f"📤 Has url attribute: {hasattr(upload_result, 'url')}")
                    
                    if hasattr(upload_result, 'url'):
                        print(f"🔗 Direct upload URL: {upload_result.url}")
                        
                        # Test this URL
                        try:
                            response = requests.head(upload_result.url, timeout=10)
                            print(f"🌐 Direct URL Status: {response.status_code}")
                            
                            if response.status_code == 200:
                                print(f"✅ Direct upload URL is accessible!")
                                return upload_result.url
                            else:
                                print(f"❌ Direct upload URL not accessible")
                                
                        except Exception as e:
                            print(f"❌ Direct URL test failed: {e}")
                    
                    # Check if it has response attribute
                    if hasattr(upload_result, 'response'):
                        print(f"📤 Response attribute: {upload_result.response}")
                    
                    # Try to get all attributes
                    if hasattr(upload_result, '__dict__'):
                        print(f"📤 All attributes: {list(upload_result.__dict__.keys())}")
                        for attr_name, attr_value in upload_result.__dict__.items():
                            print(f"   {attr_name}: {attr_value}")
            
        except Exception as e:
            print(f"❌ Direct ImageKit test failed: {e}")
            import traceback
            traceback.print_exc()
    
    def create_simple_test_image(self):
        """Create a simple test image to upload"""
        print(f"\n🎨 CREATING SIMPLE TEST IMAGE")
        print("=" * 30)
        
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple 200x200 red image
            img = Image.new('RGB', (200, 200), color='red')
            draw = ImageDraw.Draw(img)
            draw.text((50, 90), "TEST", fill='white')
            
            # Save to BytesIO
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Upload this simple image
            uploaded_url = upload_image(img_bytes.read(), "simple_test.png")
            print(f"🔗 Simple image upload: {uploaded_url}")
            
            # Test URL
            if 'imagekit.io' in uploaded_url:
                response = requests.head(uploaded_url, timeout=10)
                print(f"🌐 Simple image status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ Simple image accessible!")
                    return uploaded_url
                else:
                    print(f"❌ Simple image not accessible")
            
        except ImportError:
            print("⚠️ PIL not available, skipping simple image test")
        except Exception as e:
            print(f"❌ Simple image test failed: {e}")
    
    def show_results(self):
        """Show comprehensive results"""
        print(f"\n📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 50)
        
        successful_urls = []
        failed_uploads = []
        
        for result in self.test_results:
            print(f"\n📷 {result['image']}")
            print(f"   Status: {result['status']}")
            print(f"   URL: {result['url'][:60]}..." if result['url'] else "   URL: None")
            print(f"   Accessible: {'✅' if result['accessible'] else '❌'}")
            
            if result['accessible']:
                successful_urls.append(result['url'])
            else:
                failed_uploads.append(result['image'])
        
        print(f"\n📈 SUMMARY:")
        print(f"   ✅ Successful uploads: {len(successful_urls)}")
        print(f"   ❌ Failed uploads: {len(failed_uploads)}")
        
        if successful_urls:
            print(f"\n🌐 WORKING URLS (test these in browser):")
            for i, url in enumerate(successful_urls[:3], 1):
                print(f"   {i}. {url}")
                
        return successful_urls
    
    def run_full_debug(self):
        """Run complete debugging process"""
        print("🚀 STARTING COMPLETE IMAGEKIT DEBUG")
        print("=" * 60)
        
        # Test current upload function
        self.test_image_upload_comprehensive()
        
        # Test ImageKit SDK directly
        direct_url = self.test_imagekit_direct()
        
        # Test simple image creation
        simple_url = self.create_simple_test_image()
        
        # Show results
        working_urls = self.show_results()
        
        return working_urls, direct_url, simple_url


def main():
    debugger = ImageKitDebugger()
    working_urls, direct_url, simple_url = debugger.run_full_debug()
    
    print(f"\n🎯 FINAL RECOMMENDATIONS:")
    
    if working_urls:
        print(f"✅ Some uploads are working - test these URLs in browser:")
        for url in working_urls[:2]:
            print(f"   📸 {url}")
    
    if direct_url:
        print(f"✅ Direct SDK upload worked: {direct_url}")
        
    if simple_url:
        print(f"✅ Simple image upload worked: {simple_url}")
    
    if not working_urls and not direct_url and not simple_url:
        print(f"❌ All uploads failed - check ImageKit configuration")
    
    print(f"\n🌐 Open any working URL above in the browser to verify!")


if __name__ == "__main__":
    main()