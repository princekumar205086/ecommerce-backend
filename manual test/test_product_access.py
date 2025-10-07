#!/usr/bin/env python
"""
Test product access by ID
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
from products.models import Product

User = get_user_model()

def test_product_access():
    """Test accessing product by ID"""
    client = APIClient()
    
    # Get users
    supplier_user = User.objects.filter(role='supplier').first()
    
    # Authenticate
    token = str(RefreshToken.for_user(supplier_user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Get latest product created by this supplier
    latest_product = Product.objects.filter(created_by=supplier_user).order_by('-id').first()
    
    if not latest_product:
        print("❌ No products found for supplier")
        return False
        
    print(f"Testing access to product {latest_product.id}: {latest_product.name}")
    print(f"Product status: {latest_product.status}, is_publish: {latest_product.is_publish}")
    
    # Test GET request
    response = client.get(f'/api/products/products/{latest_product.id}/')
    print(f"GET /api/products/products/{latest_product.id}/ -> {response.status_code}")
    
    if response.status_code == 404:
        print("❌ Product not accessible - queryset issue confirmed")
        return False
    elif response.status_code == 200:
        print("✅ Product accessible!")
        return True
    else:
        print(f"⚠️ Unexpected status: {response.status_code}")
        print(f"Response: {response.data if hasattr(response, 'data') else response.content}")
        return False

if __name__ == '__main__':
    test_product_access()