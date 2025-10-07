#!/usr/bin/env python
"""
Test Brand API access control fix
"""
import os
import sys
import json
from datetime import datetime

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import Brand

User = get_user_model()

def test_brand_api_access_control():
    """Test brand API access control for different user roles"""
    print("🚀 TESTING BRAND API ACCESS CONTROL")
    print("=" * 60)
    
    # Get users of different roles
    admin_user = User.objects.filter(role='admin').first()
    supplier_user = User.objects.filter(role='supplier').first()
    regular_user = User.objects.filter(role='user').first()
    
    if not admin_user:
        print("❌ No admin user found")
        return
    if not supplier_user:
        print("❌ No supplier user found")
        return
    if not regular_user:
        print("❌ No regular user found")
        return
    
    print(f"Testing with:")
    print(f"  Admin: {admin_user.email} (role: {admin_user.role})")
    print(f"  Supplier: {supplier_user.email} (role: {supplier_user.role})")
    print(f"  Regular User: {regular_user.email} (role: {regular_user.role})")
    print()
    
    # Test each user type
    test_results = {}
    
    # Test Admin Access
    print("👑 TESTING ADMIN ACCESS:")
    print("-" * 30)
    admin_client = APIClient()
    admin_token = str(RefreshToken.for_user(admin_user).access_token)
    admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
    
    response = admin_client.get('/api/products/brands/')
    test_results['admin'] = {
        'status_code': response.status_code,
        'count': response.data['count'] if response.status_code == 200 else 0,
        'success': response.status_code == 200
    }
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Brands visible: {response.data['count']}")
    else:
        print(f"  Error: {response.data if hasattr(response, 'data') else response.content}")
    print()
    
    # Test Supplier Access
    print("🏪 TESTING SUPPLIER ACCESS:")
    print("-" * 30)
    supplier_client = APIClient()
    supplier_token = str(RefreshToken.for_user(supplier_user).access_token)
    supplier_client.credentials(HTTP_AUTHORIZATION=f'Bearer {supplier_token}')
    
    response = supplier_client.get('/api/products/brands/')
    test_results['supplier'] = {
        'status_code': response.status_code,
        'count': response.data['count'] if response.status_code == 200 else 0,
        'success': response.status_code == 200
    }
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Brands visible: {response.data['count']}")
    else:
        print(f"  Error: {response.data if hasattr(response, 'data') else response.content}")
    print()
    
    # Test Regular User Access (should be denied)
    print("👤 TESTING REGULAR USER ACCESS (should be denied):")
    print("-" * 30)
    user_client = APIClient()
    user_token = str(RefreshToken.for_user(regular_user).access_token)
    user_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
    
    response = user_client.get('/api/products/brands/')
    test_results['user'] = {
        'status_code': response.status_code,
        'count': 0,
        'success': response.status_code == 403  # Should be forbidden
    }
    print(f"  Status: {response.status_code}")
    if response.status_code == 403:
        print(f"  ✅ Correctly denied access (403 Forbidden)")
    else:
        print(f"  ❌ Unexpected result - should be 403")
        if hasattr(response, 'data'):
            print(f"  Response: {response.data}")
    print()
    
    # Test Public Endpoint (should work for everyone)
    print("🌐 TESTING PUBLIC ENDPOINT:")
    print("-" * 30)
    public_client = APIClient()
    
    # Test without authentication
    response = public_client.get('/api/public/products/brands/')
    test_results['public_anonymous'] = {
        'status_code': response.status_code,
        'count': response.data['count'] if response.status_code == 200 else 0,
        'success': response.status_code == 200
    }
    print(f"  Anonymous access status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Brands visible: {response.data['count']}")
    print()
    
    # Test with regular user authentication (should work)
    public_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
    response = public_client.get('/api/public/products/brands/')
    test_results['public_authenticated'] = {
        'status_code': response.status_code,
        'count': response.data['count'] if response.status_code == 200 else 0,
        'success': response.status_code == 200
    }
    print(f"  Regular user access to public endpoint: {response.status_code}")
    if response.status_code == 200:
        print(f"  Brands visible: {response.data['count']}")
    print()
    
    # Summary
    print("📊 TEST SUMMARY:")
    print("-" * 30)
    for role, result in test_results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {role.upper()}: {status} (Status: {result['status_code']}, Count: {result['count']})")
    
    # Overall success
    all_passed = all(result['success'] for result in test_results.values())
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

def test_with_jwt_token():
    """Test with the specific JWT token from the user's curl request"""
    print("\n🔍 TESTING WITH SPECIFIC JWT TOKEN:")
    print("-" * 50)
    
    # The JWT token from the user's curl request
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU5MzU0NzczLCJpYXQiOjE3NTkzNTM4NzMsImp0aSI6IjBiOTllNzZlM2M3YjQwYzc4ZDBmNjU5OTgyODhmZTA3IiwidXNlcl9pZCI6OH0.Li7nW4S3uOBITMWOO8BikgshZVM_-LOcMYJMm0a8OJg"
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {jwt_token}')
    
    # Test private endpoint
    print("Testing /api/products/brands/ with JWT token:")
    response = client.get('/api/products/brands/')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Count: {response.data['count']}")
    elif response.status_code == 403:
        print(f"  ✅ Access denied (403) - User role not authorized for private endpoint")
    else:
        print(f"  Error: {response.data if hasattr(response, 'data') else response.content}")
    
    # Test public endpoint
    print("\nTesting /api/public/products/brands/ with JWT token:")
    response = client.get('/api/public/products/brands/')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Count: {response.data['count']}")
        print(f"  ✅ Public endpoint working correctly")
    else:
        print(f"  Error: {response.data if hasattr(response, 'data') else response.content}")

if __name__ == '__main__':
    success = test_brand_api_access_control()
    test_with_jwt_token()
    
    print(f"\n🎉 Access control fix {'SUCCESS' if success else 'NEEDS MORE WORK'}!")