#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import Product
import json

User = get_user_model()

# Create test client
client = Client()

# Get test users
admin_user = User.objects.filter(is_superuser=True).first()
supplier_user = User.objects.filter(role='supplier').first()

def get_auth_headers(user):
    """Get authentication headers"""
    if not user:
        return {}
    refresh = RefreshToken.for_user(user)
    return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}

# Test product detail URLs
products = Product.objects.all()[:3]

print("🔍 Testing Product Detail URLs...")
print("=" * 50)

for i, product in enumerate(products):
    print(f"\n📦 Product {i+1}: {product.name} (ID: {product.id})")
    
    # Test without authentication
    response = client.get(f'/api/products/products/{product.id}/')
    print(f"   No Auth: {response.status_code}")
    
    # Test with admin authentication
    if admin_user:
        headers = get_auth_headers(admin_user)
        response = client.get(f'/api/products/products/{product.id}/', **headers)
        print(f"   Admin Auth: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS: Retrieved {data.get('name', 'Unknown')}")
        elif response.status_code != 200:
            print(f"   ❌ FAILED: {response.content.decode()[:100]}")
    
    # Test with supplier authentication  
    if supplier_user:
        headers = get_auth_headers(supplier_user)
        response = client.get(f'/api/products/products/{product.id}/', **headers)
        print(f"   Supplier Auth: {response.status_code}")

print("\n" + "=" * 50)
print("URL Debug Complete!")