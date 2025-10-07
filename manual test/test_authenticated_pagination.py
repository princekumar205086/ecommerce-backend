#!/usr/bin/env python
"""
Test authenticated endpoint pagination
"""
import os
import sys

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import Brand, ProductCategory

User = get_user_model()

def test_authenticated_pagination():
    """Test pagination in authenticated endpoints"""
    print("🔍 TESTING AUTHENTICATED ENDPOINT PAGINATION")
    print("=" * 60)
    
    # Get admin user for testing
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        print("❌ No admin user found")
        return
    
    # Setup authenticated client
    client = APIClient()
    token = str(RefreshToken.for_user(admin_user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Test authenticated brand endpoint without pagination
    print("Testing /api/products/brands/ (no page param):")
    response = client.get('/api/products/brands/')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Count: {response.data['count']}")
        print(f"  Results length: {len(response.data['results'])}")
        total_brands = Brand.objects.count()
        print(f"  Expected: All {total_brands} brands (admin sees all)")
        print(f"  Issue: {'✅ Returns all data' if len(response.data['results']) == total_brands else '❌ Limited to 12 items'}")
        
        if 'next' in response.data:
            print(f"  Has next page: {response.data['next'] is not None}")
    print()
    
    # Test with page parameter
    print("Testing /api/products/brands/?page=1:")
    response = client.get('/api/products/brands/?page=1')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Count: {response.data['count']}")
        print(f"  Results length: {len(response.data['results'])}")
        print(f"  Has next: {response.data.get('next') is not None}")
    print()
    
    # Test categories endpoint
    print("Testing /api/products/categories/ (no page param):")
    response = client.get('/api/products/categories/')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Count: {response.data['count']}")
        print(f"  Results length: {len(response.data['results'])}")
        total_categories = ProductCategory.objects.count()
        print(f"  Expected: All {total_categories} categories")
        print(f"  Issue: {'✅ Returns all data' if len(response.data['results']) == total_categories else '❌ Limited to 12 items'}")

if __name__ == '__main__':
    test_authenticated_pagination()