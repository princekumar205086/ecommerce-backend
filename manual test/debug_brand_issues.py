#!/usr/bin/env python
"""
Debug specific Brand API issues
"""
import os
import sys
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

def debug_brand_access():
    """Debug brand access issues"""
    print("🔍 DEBUGGING BRAND ACCESS ISSUES")
    print("-" * 50)
    
    # Get users
    admin_user = User.objects.filter(role='admin').first()
    supplier_user = User.objects.filter(role='supplier').first()
    
    # Get Abbott brand
    abbott_brand = Brand.objects.filter(name='Abbott').first()
    
    if not abbott_brand:
        print("❌ Abbott brand not found")
        return
        
    print(f"Abbott Brand Details:")
    print(f"  ID: {abbott_brand.id}")
    print(f"  Name: {abbott_brand.name}")
    print(f"  Status: {abbott_brand.status}")
    print(f"  Is Publish: {abbott_brand.is_publish}")
    print(f"  Created By: {abbott_brand.created_by.email}")
    print(f"  Created By Role: {abbott_brand.created_by.role}")
    print()
    
    # Test what a supplier should see
    supplier_client = APIClient()
    token = str(RefreshToken.for_user(supplier_user).access_token)
    supplier_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    print("Supplier queryset test:")
    from django.db.models import Q
    supplier_brands = Brand.objects.filter(
        Q(created_by=supplier_user) | Q(status__in=['approved', 'published'], is_publish=True)
    )
    
    print(f"  Brands supplier should see: {supplier_brands.count()}")
    abbott_in_queryset = supplier_brands.filter(id=abbott_brand.id).exists()
    print(f"  Abbott in supplier queryset: {abbott_in_queryset}")
    
    # Test API access
    print(f"\nTesting API access:")
    response = supplier_client.get(f'/api/products/brands/{abbott_brand.id}/')
    print(f"  Supplier access to Abbott: {response.status_code}")
    
    # Create a published brand for testing
    print(f"\nCreating published brand for testing:")
    test_brand = Brand.objects.create(
        name=f'Test Published Brand {datetime.now().strftime("%H%M%S")}',
        status='published',
        is_publish=True,
        created_by=admin_user
    )
    
    print(f"  Created brand: {test_brand.name} (ID: {test_brand.id})")
    print(f"  Status: {test_brand.status}, Is Publish: {test_brand.is_publish}")
    
    # Test supplier access to published brand
    response = supplier_client.get(f'/api/products/brands/{test_brand.id}/')
    print(f"  Supplier access to published brand: {response.status_code}")
    
    # Clean up
    test_brand.delete()
    
    print()

def debug_validation_error():
    """Debug validation error issue"""
    print("🔍 DEBUGGING VALIDATION ERROR ISSUE")
    print("-" * 50)
    
    supplier_user = User.objects.filter(role='supplier').first()
    supplier_client = APIClient()
    token = str(RefreshToken.for_user(supplier_user).access_token)
    supplier_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Create a test brand
    test_brand = Brand.objects.create(
        name=f'Validation Test Brand {datetime.now().strftime("%H%M%S")}',
        status='pending',
        is_publish=False,
        created_by=supplier_user
    )
    
    print(f"Created test brand: {test_brand.name} (ID: {test_brand.id})")
    
    # Test validation error with PUT
    invalid_data = {'name': ''}  # Empty name should fail
    response = supplier_client.put(f'/api/products/brands/{test_brand.id}/', data=invalid_data, format='json')
    
    print(f"PUT with empty name: {response.status_code}")
    if hasattr(response, 'data'):
        print(f"Response data: {response.data}")
    
    # Clean up
    test_brand.delete()
    print()

if __name__ == '__main__':
    debug_brand_access()
    debug_validation_error()