#!/usr/bin/env python
"""
Test API endpoints with image uploads
"""
import os
import requests
from PIL import Image
from io import BytesIO

def test_brand_creation():
    """Test brand creation with image"""
    print("🔄 Testing Brand Creation with Image")
    
    # Get admin token
    auth_url = "http://127.0.0.1:8000/api/accounts/token/"
    auth_data = {
        "email": "prince@example.com",
        "password": "Test@123456"
    }
    
    try:
        auth_response = requests.post(auth_url, json=auth_data)
        if auth_response.status_code == 200:
            token = auth_response.json().get('access')
            print(f"✅ Got auth token")
            
            # Create test image
            img = Image.new('RGB', (200, 200), color='purple')
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            # Test brand creation
            brand_url = "http://127.0.0.1:8000/api/products/brands/"
            
            files = {
                'image_file': ('test_brand.jpg', img_bytes, 'image/jpeg')
            }
            
            data = {
                'name': 'Test Brand API Upload',
                'description': 'Test brand with image upload'
            }
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            brand_response = requests.post(
                brand_url, 
                data=data, 
                files=files, 
                headers=headers
            )
            
            if brand_response.status_code == 201:
                brand_data = brand_response.json()
                image_url = brand_data.get('image')
                print(f"✅ Brand created successfully")
                print(f"📸 Image URL: {image_url}")
                
                if image_url and image_url.startswith('http'):
                    # Test the image URL
                    response = requests.head(image_url, timeout=10)
                    if response.status_code == 200:
                        print(f"✅ Brand image URL is accessible")
                        return image_url
                    else:
                        print(f"❌ Brand image URL not accessible: {response.status_code}")
                else:
                    print(f"❌ Invalid image URL: {image_url}")
            else:
                print(f"❌ Brand creation failed: {brand_response.status_code}")
                print(f"Response: {brand_response.text}")
                
        else:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            print(f"Response: {auth_response.text}")
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return None

def test_category_creation():
    """Test category creation with image"""
    print("\n🔄 Testing Category Creation with Image")
    
    # Get admin token
    auth_url = "http://127.0.0.1:8000/api/accounts/token/"
    auth_data = {
        "email": "prince@example.com",
        "password": "Test@123456"
    }
    
    try:
        auth_response = requests.post(auth_url, json=auth_data)
        if auth_response.status_code == 200:
            token = auth_response.json().get('access')
            print(f"✅ Got auth token")
            
            # Create test image
            img = Image.new('RGB', (150, 150), color='orange')
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            # Test category creation
            category_url = "http://127.0.0.1:8000/api/products/categories/"
            
            files = {
                'icon_file': ('test_category.jpg', img_bytes, 'image/jpeg')
            }
            
            data = {
                'name': 'Test Category API Upload'
            }
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            category_response = requests.post(
                category_url, 
                data=data, 
                files=files, 
                headers=headers
            )
            
            if category_response.status_code == 201:
                category_data = category_response.json()
                icon_url = category_data.get('icon')
                print(f"✅ Category created successfully")
                print(f"📸 Icon URL: {icon_url}")
                
                if icon_url and icon_url.startswith('http'):
                    # Test the image URL
                    response = requests.head(icon_url, timeout=10)
                    if response.status_code == 200:
                        print(f"✅ Category icon URL is accessible")
                        return icon_url
                    else:
                        print(f"❌ Category icon URL not accessible: {response.status_code}")
                else:
                    print(f"❌ Invalid icon URL: {icon_url}")
            else:
                print(f"❌ Category creation failed: {category_response.status_code}")
                print(f"Response: {category_response.text}")
                
        else:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return None

def main():
    print("🚀 Testing Live API Endpoints with Image Upload")
    print("=" * 60)
    
    # Test brand creation
    brand_url = test_brand_creation()
    
    # Test category creation
    category_url = test_category_creation()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 API UPLOAD SUMMARY")
    print("=" * 60)
    
    success_count = 0
    
    if brand_url:
        print(f"✅ Brand creation: SUCCESS")
        success_count += 1
    else:
        print(f"❌ Brand creation: FAILED")
    
    if category_url:
        print(f"✅ Category creation: SUCCESS")
        success_count += 1
    else:
        print(f"❌ Category creation: FAILED")
    
    print(f"\n🎯 Overall: {success_count}/2 API tests passed")
    
    if success_count == 2:
        print("🎉 All API tests passed! Image upload via API is working perfectly.")
    elif success_count > 0:
        print("⚠️ Some API tests passed. Check the failed ones for issues.")
    else:
        print("🚨 All API tests failed. Check authentication and API endpoints.")

if __name__ == "__main__":
    main()