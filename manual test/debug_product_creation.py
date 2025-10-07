#!/usr/bin/env python
"""
Debug product creation issue
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
from products.models import Product, ProductCategory, Brand

User = get_user_model()

def debug_product_creation():
    """Debug product creation 400 error"""
    client = APIClient()
    
    # Get users
    supplier_user = User.objects.filter(role='supplier').first()
    
    # Authenticate
    token = str(RefreshToken.for_user(supplier_user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Get valid category and brand
    category = ProductCategory.objects.filter(is_publish=True).first()
    brand = Brand.objects.filter(is_publish=True).first()
    
    print(f"Using category: {category.id} ({category.name})")
    print(f"Using brand: {brand.id} ({brand.name})")
    
    # Test simple product creation
    product_data = {
        'name': f"Debug Product {datetime.now().strftime('%Y%m%d%H%M%S')}",
        'description': 'Debug test product',
        'category': category.id,
        'brand': brand.id,
        'product_type': 'medicine',
        'price': '99.99',
        'stock': 50
    }
    
    print(f"Sending data: {json.dumps(product_data, indent=2)}")
    
    response = client.post('/api/products/products/', data=product_data, format='json')
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data if hasattr(response, 'data') else response.content}")
    
    return response.status_code == 201

if __name__ == '__main__':
    success = debug_product_creation()
    if success:
        print("✅ Product creation working!")
    else:
        print("❌ Product creation failed!")