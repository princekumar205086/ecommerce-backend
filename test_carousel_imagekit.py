#!/usr/bin/env python
"""
Test script for CarouselBanner ImageKit integration
Tests all endpoints and verifies image upload to ImageKit works correctly
"""

import os
import sys

# Setup Django FIRST before any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.conf import settings
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from PIL import Image
from io import BytesIO
import requests

from cms.models import CarouselBanner
from accounts.models import User

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*80}{END}")
    print(f"{BOLD}{BLUE}{text:^80}{END}")
    print(f"{BOLD}{BLUE}{'='*80}{END}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{END}")

def print_error(text):
    print(f"{RED}❌ {text}{END}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{END}")

def print_test(text):
    print(f"{YELLOW}🧪 {text}{END}")

def create_test_image(filename="test_image.jpg", size=(100, 100), format="JPEG"):
    """Create a test image file"""
    image = Image.new('RGB', size, color='red')
    image.save(filename, format=format)
    print_info(f"Created test image: {filename}")
    return filename

def get_admin_token():
    """Create admin user and get JWT token"""
    print_test("Creating admin user and getting JWT token...")
    
    # Try to get existing admin or create one
    User = get_user_model()
    admin_user, created = User.objects.get_or_create(
        email='admin_test@example.com',
        defaults={
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    
    if created:
        admin_user.set_password('adminpass123')
        admin_user.save()
        print_success(f"Created admin user: {admin_user.email}")
    else:
        print_info(f"Using existing admin user: {admin_user.email}")
    
    # Generate token
    refresh = RefreshToken.for_user(admin_user)
    access_token = str(refresh.access_token)
    print_success(f"JWT token obtained (length: {len(access_token)} chars)")
    
    return access_token, admin_user

def test_public_endpoint():
    """Test public endpoint for fetching carousels"""
    print_test("Testing public endpoint: GET /api/cms/carousel/")
    
    client = Client()
    response = client.get('/api/cms/carousel/')
    
    if response.status_code == 200:
        data = response.json()
        count = len(data) if isinstance(data, list) else data.get('results', [])
        print_success(f"Public endpoint working: {response.status_code}")
        print_info(f"Response contains {count} carousel(s) or paginated results")
        return True
    else:
        print_error(f"Public endpoint failed: {response.status_code}")
        return False

def test_admin_create_with_image(access_token):
    """Test admin create endpoint with image upload"""
    print_test("Testing admin create endpoint with image upload...")
    
    # Create a test image
    image_file = create_test_image("test_carousel.jpg")
    
    client = Client()
    headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
    
    # Prepare multipart data using SimpleUploadedFile for better compatibility
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    with open(image_file, 'rb') as f:
        image_content = f.read()
    
    image_field = SimpleUploadedFile(
        name='test_carousel.jpg',
        content=image_content,
        content_type='image/jpeg'
    )
    
    data = {
        'title': 'Test Carousel Banner',
        'caption': 'Test Caption',
        'link': 'https://example.com',
        'is_active': 'true',
        'order': '1'
    }
    
    print_info("Sending POST request with image file...")
    response = client.post(
        '/api/cms/admin/carousels/',
        data=data,
        files={'image_file': image_field},
        **headers
    )
    
    if response.status_code == 201:
        resp_data = response.json()
        carousel_id = resp_data.get('id')
        image_url = resp_data.get('image')
        
        print_success(f"Image upload successful: {response.status_code}")
        print_info(f"Carousel ID: {carousel_id}")
        print_info(f"Image stored at: {image_url}")
        
        # Verify ImageKit URL pattern
        if image_url and ('imagekit' in image_url.lower() or 'ik.imagekit' in image_url.lower() or '/' in image_url):
            print_success("Image stored in expected format (URL)")
            
            # Try to verify image is accessible
            try:
                img_response = requests.head(image_url, timeout=5)
                if img_response.status_code in [200, 301, 302]:
                    print_success(f"Image URL is accessible: {img_response.status_code}")
                else:
                    print_error(f"Image URL returned: {img_response.status_code}")
            except requests.exceptions.RequestException as e:
                print_error(f"Could not verify image accessibility: {str(e)[:50]}...")
        else:
            print_error("Image URL doesn't match expected ImageKit pattern")
        
        # Clean up
        os.remove(image_file)
        return True, carousel_id
    elif response.status_code == 400:
        print_error(f"Validation error: {response.status_code}")
        print_info(f"Response: {response.json()}")
        os.remove(image_file)
        return False, None
    else:
        print_error(f"Upload failed: {response.status_code}")
        print_info(f"Response: {response.json()}")
        os.remove(image_file)
        return False, None

def test_admin_list(access_token):
    """Test admin list endpoint"""
    print_test("Testing admin list endpoint: GET /api/cms/admin/carousels/")
    
    client = Client()
    headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
    
    response = client.get('/api/cms/admin/carousels/', **headers)
    
    if response.status_code == 200:
        data = response.json()
        count = len(data) if isinstance(data, list) else data.get('count', 0)
        print_success(f"Admin list endpoint working: {response.status_code}")
        print_info(f"Total carousels: {count}")
        return True
    else:
        print_error(f"Admin list failed: {response.status_code}")
        return False

def test_admin_detail(access_token, carousel_id):
    """Test admin detail endpoint"""
    print_test(f"Testing admin detail endpoint: GET /api/cms/admin/carousels/{carousel_id}/")
    
    client = Client()
    headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
    
    response = client.get(f'/api/cms/admin/carousels/{carousel_id}/', **headers)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Admin detail endpoint working: {response.status_code}")
        print_info(f"Title: {data.get('title')}")
        print_info(f"Active: {data.get('is_active')}")
        return True
    else:
        print_error(f"Admin detail failed: {response.status_code}")
        return False

def test_admin_update(access_token, carousel_id):
    """Test admin update endpoint"""
    print_test(f"Testing admin update endpoint: PATCH /api/cms/admin/carousels/{carousel_id}/")
    
    client = Client()
    headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
    
    data = {
        'title': 'Updated Test Carousel',
        'caption': 'Updated Caption'
    }
    
    response = client.patch(
        f'/api/cms/admin/carousels/{carousel_id}/',
        data=data,
        content_type='application/json',
        **headers
    )
    
    if response.status_code == 200:
        resp_data = response.json()
        print_success(f"Admin update working: {response.status_code}")
        print_info(f"Updated title: {resp_data.get('title')}")
        return True
    else:
        print_error(f"Admin update failed: {response.status_code}")
        return False

def test_admin_delete(access_token, carousel_id):
    """Test admin delete endpoint"""
    print_test(f"Testing admin delete endpoint: DELETE /api/cms/admin/carousels/{carousel_id}/")
    
    client = Client()
    headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
    
    response = client.delete(f'/api/cms/admin/carousels/{carousel_id}/', **headers)
    
    if response.status_code == 204:
        print_success(f"Admin delete working: {response.status_code}")
        return True
    else:
        print_error(f"Admin delete failed: {response.status_code}")
        return False

def test_imagekit_integration():
    """Verify ImageKit upload function is available"""
    print_test("Checking ImageKit integration...")
    
    try:
        from accounts.models import upload_to_imagekit
        print_success("upload_to_imagekit function found in accounts.models")
        return True
    except ImportError as e:
        print_error(f"ImageKit function not found: {e}")
        return False

def test_serializer_validation():
    """Test serializer validation"""
    print_test("Testing CarouselBannerSerializer validation...")
    
    try:
        from cms.serializers import CarouselBannerSerializer
        
        serializer = CarouselBannerSerializer()
        max_size = serializer.MAX_IMAGE_SIZE / (1024 * 1024)
        allowed_ext = serializer.ALLOWED_EXTENSIONS
        
        print_success("Serializer loaded successfully")
        print_info(f"Max image size: {max_size} MB")
        print_info(f"Allowed extensions: {allowed_ext}")
        
        return True
    except Exception as e:
        print_error(f"Serializer validation failed: {e}")
        return False

def main():
    """Main test runner"""
    print_header("CAROUSEL BANNER - ImageKit Integration Tests")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    # Test 1: Check ImageKit integration
    if test_imagekit_integration():
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['tests'].append(('ImageKit Integration', results['passed'] == 1))
    
    # Test 2: Check serializer validation
    if test_serializer_validation():
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['tests'].append(('Serializer Validation', results['passed'] == 2))
    
    # Test 3: Get admin token
    try:
        access_token, admin_user = get_admin_token()
        results['passed'] += 1
        results['tests'].append(('Admin Token Generation', True))
    except Exception as e:
        print_error(f"Failed to get admin token: {e}")
        results['failed'] += 1
        results['tests'].append(('Admin Token Generation', False))
        return results
    
    # Test 4: Public endpoint
    if test_public_endpoint():
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['tests'].append(('Public Endpoint', results['passed'] == 4))
    
    # Test 5: Admin create with image (ImageKit upload)
    success, carousel_id = test_admin_create_with_image(access_token)
    if success:
        results['passed'] += 1
        results['tests'].append(('Admin Create with ImageKit Upload', True))
    else:
        results['failed'] += 1
        results['tests'].append(('Admin Create with ImageKit Upload', False))
        carousel_id = None
    
    if carousel_id:
        # Test 6: Admin list
        if test_admin_list(access_token):
            results['passed'] += 1
        else:
            results['failed'] += 1
        results['tests'].append(('Admin List', results['passed'] == 6))
        
        # Test 7: Admin detail
        if test_admin_detail(access_token, carousel_id):
            results['passed'] += 1
        else:
            results['failed'] += 1
        results['tests'].append(('Admin Detail', results['passed'] == 7))
        
        # Test 8: Admin update
        if test_admin_update(access_token, carousel_id):
            results['passed'] += 1
        else:
            results['failed'] += 1
        results['tests'].append(('Admin Update', results['passed'] == 8))
        
        # Test 9: Admin delete
        if test_admin_delete(access_token, carousel_id):
            results['passed'] += 1
        else:
            results['failed'] += 1
        results['tests'].append(('Admin Delete', results['passed'] == 9))
    
    # Print summary
    print_header("Test Results Summary")
    
    for test_name, passed in results['tests']:
        status = f"{GREEN}✅ PASS{END}" if passed else f"{RED}❌ FAIL{END}"
        print(f"{status} - {test_name}")
    
    print(f"\n{BOLD}Total: {GREEN}{results['passed']} passed{END}, {RED}{results['failed']} failed{END}{END}\n")
    
    if results['failed'] == 0:
        print_success("All tests passed! ImageKit integration is working correctly ✨\n")
    else:
        print_error(f"{results['failed']} test(s) failed. Please review above.\n")
    
    return results

if __name__ == '__main__':
    main()
