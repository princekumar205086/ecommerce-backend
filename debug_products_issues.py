#!/usr/bin/env python
"""
Debug script to identify and fix all products API issues
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
from products.models import Product, ProductCategory, Brand, ProductVariant

User = get_user_model()

def debug_permissions_and_data():
    """Debug permissions and data issues"""
    print("🔍 DEBUGGING PRODUCTS API ISSUES")
    print("=" * 50)
    
    # Setup client
    client = APIClient()
    
    # Get users
    admin_user = User.objects.filter(role='admin').first()
    supplier_user = User.objects.filter(role='supplier').first()
    
    if not admin_user:
        print("❌ No admin user found")
        return
    if not supplier_user:
        print("❌ No supplier user found")  
        return
        
    print(f"✅ Found admin: {admin_user.email}")
    print(f"✅ Found supplier: {supplier_user.email}")
    
    # Get JWT tokens
    admin_token = str(RefreshToken.for_user(admin_user).access_token)
    supplier_token = str(RefreshToken.for_user(supplier_user).access_token)
    
    print("\n📋 CHECKING DATA AVAILABILITY")
    print("-" * 30)
    
    # Check available data
    categories = ProductCategory.objects.filter(is_publish=True)
    brands = Brand.objects.filter(is_publish=True)
    products = Product.objects.filter(is_publish=True)
    
    print(f"Published Categories: {categories.count()}")
    print(f"Published Brands: {brands.count()}")
    print(f"Published Products: {products.count()}")
    
    if categories.exists():
        cat = categories.first()
        print(f"Sample Category: {cat.id} - {cat.name}")
    
    if brands.exists():
        brand = brands.first()
        print(f"Sample Brand: {brand.id} - {brand.name}")
    
    if products.exists():
        product = products.first()
        print(f"Sample Product: {product.id} - {product.name}")
    
    print("\n🔧 TESTING VARIANT CREATION PERMISSION")
    print("-" * 40)
    
    # Test variant creation as supplier
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {supplier_token}')
    
    if products.exists():
        product = products.first()
        variant_data = {
            "product": product.id,
            "price": "119.99",
            "stock": 30
        }
        
        print(f"Testing variant creation for product {product.id}")
        response = client.post('/api/products/variants/', data=variant_data)
        print(f"Supplier variant creation: {response.status_code}")
        
        if response.status_code != 201:
            print(f"Response: {response.data if hasattr(response, 'data') else response.content}")
    
    # Test variant creation as admin
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
    
    if products.exists():
        product = products.first()
        variant_data = {
            "product": product.id,
            "price": "129.99", 
            "stock": 25
        }
        
        print(f"Testing admin variant creation for product {product.id}")
        response = client.post('/api/products/variants/', data=variant_data)
        print(f"Admin variant creation: {response.status_code}")
        
        if response.status_code != 201:
            print(f"Response: {response.data if hasattr(response, 'data') else response.content}")
    
    print("\n🔧 TESTING PRODUCT CREATION")
    print("-" * 30)
    
    # Test product creation as supplier
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {supplier_token}')
    
    if categories.exists() and brands.exists():
        category = categories.first()
        brand = brands.first()
        
        # Test simple product first
        simple_product_data = {
            "name": f"Debug Test Product {datetime.now().strftime('%H%M%S')}",
            "description": "Simple test product for debugging",
            "category": category.id,
            "brand": brand.id,
            "product_type": "medicine",
            "price": "99.99",
            "stock": 50
        }
        
        print(f"Testing simple product creation")
        response = client.post('/api/products/products/', data=simple_product_data)
        print(f"Simple product creation: {response.status_code}")
        
        if response.status_code != 201:
            print(f"Response: {response.data if hasattr(response, 'data') else response.content}")
        else:
            print(f"✅ Created product: {response.data['id']}")
            
        # Test medicine product with details
        medicine_product_data = {
            "name": f"Debug Medicine {datetime.now().strftime('%H%M%S')}",
            "description": "Medicine with details",
            "category": category.id,
            "brand": brand.id,
            "product_type": "medicine",
            "price": "149.99",
            "stock": 30,
            "specifications": {
                "weight": "100mg",
                "storage": "Room temperature"
            },
            "medicine_details": {
                "composition": "Active ingredient 100mg",
                "quantity": "30 tablets",
                "manufacturer": "Test Pharma",
                "expiry_date": "2025-12-31",
                "prescription_required": True,
                "form": "Tablet"
            }
        }
        
        print(f"Testing medicine product with details")
        response = client.post('/api/products/products/', data=medicine_product_data, format='json')
        print(f"Medicine product creation: {response.status_code}")
        
        if response.status_code != 201:
            print(f"Response: {response.data if hasattr(response, 'data') else response.content}")
        else:
            print(f"✅ Created medicine: {response.data['id']}")

def fix_variant_permissions():
    """Fix variant creation permissions"""
    print("\n🔧 FIXING VARIANT PERMISSIONS")
    print("-" * 30)
    
    # Read current views.py content to check permissions
    views_file = "c:\\Users\\Prince Raj\\Desktop\\comestro\\ecommerce-backend\\products\\views.py"
    
    try:
        with open(views_file, 'r') as f:
            content = f.read()
            
        if 'class ProductVariantListCreateView' in content:
            print("Found ProductVariantListCreateView")
            
            # Check current permission
            if 'permission_classes = [IsAdminOrReadOnly]' in content:
                print("❌ Current permission: IsAdminOrReadOnly (only admins can create)")
                print("💡 Should be: IsSupplierOrAdmin (both suppliers and admins)")
                
                # The fix would be to replace IsAdminOrReadOnly with IsSupplierOrAdmin
                print("\n🔧 Recommended fix:")
                print("Replace: permission_classes = [IsAdminOrReadOnly]")  
                print("With:    permission_classes = [IsSupplierOrAdmin]")
                
            else:
                print("✅ Permission class looks different, checking...")
    
    except Exception as e:
        print(f"Error reading views.py: {e}")

if __name__ == '__main__':
    debug_permissions_and_data()
    fix_variant_permissions()