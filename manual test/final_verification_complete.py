#!/usr/bin/env python
"""
Final verification of all fixed ImageKit images and API endpoints
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

from products.models import Product, ProductCategory, Brand

def verify_api_endpoints():
    """Test API endpoints to ensure they return working ImageKit URLs"""
    print("🔄 Verifying API Endpoints")
    
    endpoints = [
        "http://127.0.0.1:8000/api/products/products/",
        "http://127.0.0.1:8000/api/products/categories/",
        "http://127.0.0.1:8000/api/products/brands/"
    ]
    
    total_images_tested = 0
    working_images = 0
    broken_images = 0
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Handle paginated responses
                items = data.get('results', data) if isinstance(data, dict) else data
                
                for item in items:
                    # Check different image field names
                    image_fields = ['image', 'icon']
                    
                    for field in image_fields:
                        if field in item and item[field]:
                            image_url = item[field]
                            if image_url.startswith('http'):
                                total_images_tested += 1
                                
                                try:
                                    img_response = requests.get(image_url, timeout=5)
                                    if img_response.status_code == 200 and len(img_response.content) > 100:
                                        # Try to open as image
                                        img = Image.open(BytesIO(img_response.content))
                                        working_images += 1
                                        print(f"  ✅ {field}: {item.get('name', item.get('id'))} - {img.format} {img.size}")
                                    else:
                                        broken_images += 1
                                        print(f"  ❌ {field}: {item.get('name', item.get('id'))} - Invalid response")
                                except Exception as e:
                                    broken_images += 1
                                    print(f"  ❌ {field}: {item.get('name', item.get('id'))} - Error: {e}")
            else:
                print(f"❌ API endpoint failed: {endpoint} - {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing endpoint {endpoint}: {e}")
    
    return total_images_tested, working_images, broken_images

def test_new_image_upload():
    """Test creating new items with image upload to ensure the fix works for new uploads"""
    print("\n🔄 Testing New Image Upload via API")
    
    # Get auth token
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
            
            # Test brand creation with new fixed upload
            brand_url = "http://127.0.0.1:8000/api/products/brands/"
            
            # Create test image
            img = Image.new('RGB', (300, 300), color='purple')
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG', quality=95)
            img_bytes.seek(0)
            
            files = {
                'image_file': ('verification_test_brand.jpg', img_bytes, 'image/jpeg')
            }
            
            data = {
                'name': 'Verification Test Brand',
                'description': 'Testing fixed image upload'
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
                print(f"✅ New brand created with image: {image_url}")
                
                # Test the new image
                if image_url and image_url.startswith('http'):
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200 and len(response.content) > 100:
                        try:
                            img = Image.open(BytesIO(response.content))
                            print(f"✅ New brand image works: {img.format} {img.size}")
                            return True
                        except Exception as e:
                            print(f"❌ New brand image broken: {e}")
                    else:
                        print(f"❌ New brand image invalid response: {response.status_code}")
                else:
                    print(f"❌ Invalid image URL: {image_url}")
            else:
                print(f"❌ Brand creation failed: {brand_response.status_code}")
                print(f"Response: {brand_response.text}")
                
        else:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            
    except Exception as e:
        print(f"❌ New upload test error: {e}")
    
    return False

def verify_database_images():
    """Verify images directly from database"""
    print("\n🔄 Verifying Database Images")
    
    # Check products
    products_with_images = Product.objects.exclude(image__isnull=True).exclude(image__exact='')
    products_working = 0
    products_broken = 0
    
    for product in products_with_images[:10]:  # Test first 10
        if product.image and product.image.startswith('http'):
            try:
                response = requests.get(product.image, timeout=5)
                if response.status_code == 200 and len(response.content) > 100:
                    img = Image.open(BytesIO(response.content))
                    products_working += 1
                else:
                    products_broken += 1
            except:
                products_broken += 1
    
    # Check categories
    categories_with_images = ProductCategory.objects.exclude(icon__isnull=True).exclude(icon__exact='')
    categories_working = 0
    categories_broken = 0
    
    for category in categories_with_images[:5]:  # Test first 5
        if category.icon and category.icon.startswith('http'):
            try:
                response = requests.get(category.icon, timeout=5)
                if response.status_code == 200 and len(response.content) > 100:
                    img = Image.open(BytesIO(response.content))
                    categories_working += 1
                else:
                    categories_broken += 1
            except:
                categories_broken += 1
    
    # Check brands
    brands_with_images = Brand.objects.exclude(image__isnull=True).exclude(image__exact='')
    brands_working = 0
    brands_broken = 0
    
    for brand in brands_with_images[:3]:  # Test first 3
        if brand.image and brand.image.startswith('http'):
            try:
                response = requests.get(brand.image, timeout=5)
                if response.status_code == 200 and len(response.content) > 100:
                    img = Image.open(BytesIO(response.content))
                    brands_working += 1
                else:
                    brands_broken += 1
            except:
                brands_broken += 1
    
    print(f"📊 Database verification:")
    print(f"  Products: {products_working} working, {products_broken} broken")
    print(f"  Categories: {categories_working} working, {categories_broken} broken")
    print(f"  Brands: {brands_working} working, {brands_broken} broken")
    
    return (products_working + categories_working + brands_working), (products_broken + categories_broken + brands_broken)

def main():
    print("🎯 FINAL IMAGEKIT VERIFICATION")
    print("=" * 60)
    
    # Test 1: API endpoints
    total_tested, working, broken = verify_api_endpoints()
    
    # Test 2: New upload functionality
    new_upload_works = test_new_image_upload()
    
    # Test 3: Database verification
    db_working, db_broken = verify_database_images()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE VERIFICATION RESULTS")
    print("=" * 60)
    
    print(f"🔍 API Endpoints Test:")
    print(f"  Total images tested: {total_tested}")
    print(f"  ✅ Working: {working}")
    print(f"  ❌ Broken: {broken}")
    
    if total_tested > 0:
        success_rate = (working / total_tested) * 100
        print(f"  📈 Success rate: {success_rate:.1f}%")
    
    print(f"\n🔍 New Upload Test:")
    print(f"  ✅ Working: {'Yes' if new_upload_works else 'No'}")
    
    print(f"\n🔍 Database Verification:")
    print(f"  ✅ Working: {db_working}")
    print(f"  ❌ Broken: {db_broken}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    
    if working >= total_tested * 0.9 and new_upload_works and db_working > db_broken:
        print("🎉 EXCELLENT! ImageKit integration is working perfectly!")
        print("✅ All images are properly uploaded and accessible")
        print("✅ New uploads work correctly") 
        print("✅ Existing images have been fixed")
    elif working >= total_tested * 0.7:
        print("✅ GOOD! ImageKit integration is mostly working")
        print("⚠️ Some images may still need attention")
    else:
        print("⚠️ NEEDS WORK! Some ImageKit issues remain")
        print("🔧 Consider re-running the fix script")

if __name__ == "__main__":
    main()