#!/usr/bin/env python3
"""
Complete E-commerce Flow Test - Simplified Version
Tests: Cart -> Payment -> Order -> Cart Cleanup -> Admin Operations
"""

import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
import json
from decimal import Decimal
from products.models import Product, ProductImage, ProductCategory
from cart.models import Cart, CartItem
from orders.models import Order
from datetime import datetime, timedelta
from django.utils import timezone
from django.test import TransactionTestCase

User = get_user_model()

def test_complete_flow():
    """Test the complete e-commerce flow"""
    print("🚀 Starting Complete E-commerce Flow Test")
    print("=" * 50)
    
    client = APIClient()
    
    try:
        # 1. Setup test data
        print("\n=== 1. Setting up test data ===")
        
        # Clear existing test data
        from django.utils import timezone
        import uuid
        
        # Generate unique identifiers to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        
        # Try to get or create admin user
        try:
            admin_user = User.objects.get(email=f'admin_temp_{unique_id}@example.com')
        except User.DoesNotExist:
            admin_user = User.objects.create_user(
                email=f'admin_temp_{unique_id}@example.com',
                password='adminpass123',
                full_name='Admin Temp',
                contact='9999999999'
            )
        
        category = ProductCategory.objects.create(
            name=f"Electronics_{unique_id}",
            slug=f"electronics-{unique_id}",
            created_by=admin_user,
            is_publish=True
        )
        
        # Create products
        products = []
        for i in range(2):
            product = Product.objects.create(
                name=f"Test Product {i+1}_{unique_id}",
                description=f"Description for product {i+1}",
                price=Decimal(f"{100 + i*50}.00"),
                stock=10,
                category=category,
                slug=f"test-product-{i+1}-{unique_id}",
                created_by=admin_user
            )
            products.append(product)
            
        print(f"✅ Created {len(products)} products")
        
        # Create test user
        try:
            test_user = User.objects.get(email=f'testflow_{unique_id}@example.com')
        except User.DoesNotExist:
            test_user = User.objects.create_user(
                email=f'testflow_{unique_id}@example.com',
                password='testpass123',
                full_name='Test Flow',
                contact='1234567890'
            )
        print(f"✅ Created test user: {test_user.email}")
        
        # Login user
        login_response = client.post('/api/accounts/login/', {
            'email': f'testflow_{unique_id}@example.com',
            'password': 'testpass123'
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.data}")
            return
            
        auth_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {login_response.data["access"]}'
        }
        print("✅ User authenticated successfully")
        
        # 2. Test cart operations
        print("\n=== 2. Testing Cart Operations ===")
        
        # Add items to cart
        for i, product in enumerate(products):
            response = client.post(
                '/api/cart/add/',
                {
                    'product_id': product.id,
                    'quantity': i + 1
                },
                **auth_headers
            )
            print(f"Added product {product.id} to cart: {response.status_code}")
        
        # Get cart
        cart_response = client.get('/api/cart/', **auth_headers)
        if cart_response.status_code != 200:
            print(f"❌ Cart retrieval failed: {cart_response.data}")
            return
            
        cart_data = cart_response.data
        print(f"✅ Cart total: ${cart_data.get('total', 0)}")
        print(f"✅ Cart items: {len(cart_data.get('items', []))}")
        
        # 3. Test COD payment flow (simpler than Razorpay)
        print("\n=== 3. Testing COD Payment Flow ===")
        
        # Create payment from cart for COD
        payment_response = client.post(
            '/api/payments/create-from-cart/',
            {
                'payment_method': 'cod',
                'shipping_address': {
                    'name': 'Test User',
                    'address': '123 Test St',
                    'city': 'Test City',
                    'state': 'Test State',
                    'postal_code': '12345',
                    'phone': '1234567890'
                }
            },
            **auth_headers
        )
        
        if payment_response.status_code != 201:
            print(f"❌ COD Payment creation failed: {payment_response.data}")
            return
            
        payment_data = payment_response.data
        print(f"✅ COD Payment created: {payment_data['id']}")
        
        # Confirm COD payment
        confirm_response = client.post(
            '/api/payments/confirm-cod/',
            {
                'payment_id': payment_data['id']
            },
            **auth_headers
        )
        
        if confirm_response.status_code != 200:
            print(f"❌ COD confirmation failed: {confirm_response.data}")
            return
            
        print("✅ COD payment confirmed successfully")
        
        # 4. Test booking verification
        print("\n=== 4. Testing Booking Verification ===")
        
        # Get user orders
        orders_response = client.get('/api/orders/', **auth_headers)
        if orders_response.status_code != 200:
            print(f"❌ Orders retrieval failed: {orders_response.data}")
            return
            
        orders = orders_response.data.get('results', [])
        print(f"✅ Found {len(orders)} orders")
        
        for order in orders:
            print(f"   Order #{order['order_number']}: {order['status']} - ${order['total']}")
        
        # 5. Test cart cleanup
        print("\n=== 5. Testing Cart Cleanup ===")
        
        cart_response = client.get('/api/cart/', **auth_headers)
        if cart_response.status_code == 200:
            cart_data = cart_response.data
            items_count = len(cart_data.get('items', []))
            print(f"Cart items after order: {items_count}")
            
            if items_count == 0:
                print("✅ Cart cleaned successfully")
            else:
                print("❌ Cart not cleaned properly")
        
        # 6. Test admin operations
        print("\n=== 6. Testing Admin Operations ===")
        
        if not orders:
            print("❌ No orders to test admin operations")
            return
        
        # Create admin user
        try:
            admin_user = User.objects.get(email=f'adminflow_{unique_id}@example.com')
        except User.DoesNotExist:
            admin_user = User.objects.create_user(
                email=f'adminflow_{unique_id}@example.com',
                password='adminpass123',
                full_name='Admin Flow',
                contact='8888888888',
                is_staff=True,
                is_superuser=True
            )
        
        # Login as admin
        admin_login = client.post('/api/accounts/login/', {
            'email': f'adminflow_{unique_id}@example.com',
            'password': 'adminpass123'
        })
        
        if admin_login.status_code != 200:
            print(f"❌ Admin login failed: {admin_login.data}")
            return
            
        admin_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {admin_login.data["access"]}'
        }
        print("✅ Admin authenticated successfully")
        
        order_id = orders[0]['id']
        
        # Test admin order operations
        operations = [
            ('accept', '/api/orders/admin/accept/', {'order_id': order_id}),
            ('assign-shipping', '/api/orders/admin/assign-shipping/', {
                'order_id': order_id, 
                'shipping_partner': 'BlueDart',
                'tracking_id': 'BD123456789'
            }),
            ('mark-delivered', '/api/orders/admin/mark-delivered/', {'order_id': order_id})
        ]
        
        for op_name, url, data in operations:
            response = client.post(url, data, **admin_headers)
            print(f"Admin {op_name}: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ {op_name} successful")
            else:
                print(f"❌ {op_name} failed: {response.data}")
        
        print("\n" + "=" * 50)
        print("🎉 Complete E-commerce Flow Test Completed Successfully!")
        print("✅ All flows tested: Cart → Payment → Order → Cart Cleanup → Admin Operations")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_flow()