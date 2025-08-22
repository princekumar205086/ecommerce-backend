#!/usr/bin/env python
"""
Test script to verify improved ImageKit upload functionality
Based on Puja app pattern with comprehensive validation
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

def test_universal_upload_function():
    """Test the universal upload function from accounts app"""
    print("\n🔄 Testing Universal Upload Function (accounts.models.upload_to_imagekit)")
    
    # Create a test image
    img = Image.new('RGB', (300, 300), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    try:
        # Test upload with bytes
        image_url = upload_to_imagekit(
            file_bytes=img_bytes.getvalue(),
            filename="test_universal_upload.jpg",
            folder="tests"
        )
        
        if image_url and image_url.startswith('http'):
            print(f"✅ Universal upload successful: {image_url}")
            
            # Test the URL
            response = requests.head(image_url, timeout=10)
            if response.status_code == 200:
                print(f"✅ URL is accessible: {response.status_code}")
            else:
                print(f"❌ URL not accessible: {response.status_code}")
                
            return image_url
        else:
            print(f"❌ Universal upload failed: {image_url}")
            return None
            
    except Exception as e:
        print(f"❌ Universal upload error: {e}")
        return None

def test_products_upload_function():
    """Test the products-specific upload function"""
    print("\n🔄 Testing Products Upload Function (products.utils.imagekit.upload_image)")
    
    # Create a test image
    img = Image.new('RGB', (400, 400), color='blue')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    try:
        # Test upload with file-like object
        image_url = upload_image(
            file=img_bytes,
            file_name="test_products_upload.jpg",
            folder="tests/products"
        )
        
        if image_url and image_url.startswith('http'):
            print(f"✅ Products upload successful: {image_url}")
            
            # Test the URL
            response = requests.head(image_url, timeout=10)
            if response.status_code == 200:
                print(f"✅ URL is accessible: {response.status_code}")
            else:
                print(f"❌ URL not accessible: {response.status_code}")
                
            return image_url
        else:
            print(f"❌ Products upload failed: {image_url}")
            return None
            
    except Exception as e:
        print(f"❌ Products upload error: {e}")
        return None

def test_api_endpoint_with_image():
    """Test API endpoint with image upload"""
    print("\n🔄 Testing API Endpoint with Image Upload")
    
    # Get auth token
    auth_url = "http://127.0.0.1:8000/api/accounts/login/"
    auth_data = {
        "email": "prince@example.com",
        "password": "Test@123456"
    }
    
    try:
        auth_response = requests.post(auth_url, json=auth_data)
        if auth_response.status_code == 200:
            token = auth_response.json().get('access')
            print(f"✅ Got auth token: {token[:20]}...")
            
            # Test product creation with image
            product_url = "http://127.0.0.1:8000/api/products/products/"
            
            # Create test image file
            img = Image.new('RGB', (500, 500), color='green')
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            # Prepare multipart form data
            files = {
                'image_file': ('test_product.jpg', img_bytes, 'image/jpeg')
            }
            
            data = {
                'name': 'Test Product API Upload',
                'description': 'Test product with improved image upload',
                'category': 1,  # Assuming category ID 1 exists
                'price': '99.99',
                'stock': '100',
                'product_type': 'medicine'
            }
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            # Reset BytesIO position
            img_bytes.seek(0)
            files = {
                'image_file': ('test_product.jpg', img_bytes, 'image/jpeg')
            }
            
            product_response = requests.post(
                product_url, 
                data=data, 
                files=files, 
                headers=headers
            )
            
            if product_response.status_code == 201:
                product_data = product_response.json()
                image_url = product_data.get('image')
                print(f"✅ Product created successfully with image: {image_url}")
                
                if image_url and image_url.startswith('http'):
                    # Test the image URL
                    response = requests.head(image_url, timeout=10)
                    if response.status_code == 200:
                        print(f"✅ Product image URL is accessible: {response.status_code}")
                        return image_url
                    else:
                        print(f"❌ Product image URL not accessible: {response.status_code}")
                else:
                    print(f"❌ Invalid image URL in response: {image_url}")
            else:
                print(f"❌ Product creation failed: {product_response.status_code}")
                print(f"Response: {product_response.text}")
                
        else:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return None

def main():
    print("🚀 Testing Improved ImageKit Upload Functionality")
    print("=" * 60)
    
    # Test 1: Universal upload function
    universal_url = test_universal_upload_function()
    
    # Test 2: Products upload function
    products_url = test_products_upload_function()
    
    # Test 3: API endpoint
    api_url = test_api_endpoint_with_image()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    success_count = 0
    
    if universal_url:
        print(f"✅ Universal upload: SUCCESS")
        success_count += 1
    else:
        print(f"❌ Universal upload: FAILED")
    
    if products_url:
        print(f"✅ Products upload: SUCCESS")
        success_count += 1
    else:
        print(f"❌ Products upload: FAILED")
    
    if api_url:
        print(f"✅ API endpoint upload: SUCCESS")
        success_count += 1
    else:
        print(f"❌ API endpoint upload: FAILED")
    
    print(f"\n🎯 Overall: {success_count}/3 tests passed")
    
    if success_count == 3:
        print("🎉 All tests passed! ImageKit integration is working perfectly.")
    elif success_count > 0:
        print("⚠️ Some tests passed. Check the failed ones for issues.")
    else:
        print("🚨 All tests failed. Check ImageKit configuration and implementation.")

if __name__ == "__main__":
    main()