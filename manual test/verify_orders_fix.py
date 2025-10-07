#!/usr/bin/env python3

"""
Comprehensive test to verify the orders API fix
"""

import os
import sys
import django
import requests
import json

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order

User = get_user_model()

def test_orders_fix_comprehensive():
    print("=== COMPREHENSIVE ORDERS FIX VERIFICATION ===")
    
    # Test both locally and on production
    test_environments = [
        ("Local", "http://127.0.0.1:8000"),
        ("Production", "https://backend.okpuja.in")
    ]
    
    credentials = {
        "email": "user@example.com",
        "password": "User@123"
    }
    
    for env_name, base_url in test_environments:
        print(f"\n🌐 Testing {env_name} Environment: {base_url}")
        print("="*50)
        
        # 1. Test authentication
        print("1️⃣ Testing authentication...")
        try:
            auth_response = requests.post(f"{base_url}/api/accounts/login/", json=credentials)
            print(f"   Auth status: {auth_response.status_code}")
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                access_token = auth_data['access']
                user_info = auth_data['user']
                print(f"   ✅ Login successful")
                print(f"   User: {user_info['full_name']} ({user_info['email']})")
                print(f"   MedixMall mode: {user_info.get('medixmall_mode', 'N/A')}")
                print(f"   Role: {user_info['role']}")
            else:
                print(f"   ❌ Login failed: {auth_response.text}")
                continue
                
        except Exception as e:
            print(f"   ❌ Auth error: {str(e)}")
            continue
        
        # 2. Test orders endpoint
        print("\n2️⃣ Testing orders endpoint...")
        headers = {'Authorization': f'Bearer {access_token}'}
        
        try:
            orders_response = requests.get(f"{base_url}/api/orders/", headers=headers)
            print(f"   Orders status: {orders_response.status_code}")
            
            # Check response headers
            response_headers = dict(orders_response.headers)
            medixmall_header = response_headers.get('X-MedixMall-Mode', 'Not present')
            print(f"   X-MedixMall-Mode header: {medixmall_header}")
            
            if orders_response.status_code == 200:
                orders_data = orders_response.json()
                print(f"   ✅ Orders retrieved successfully")
                print(f"   Total count: {orders_data.get('count', 0)}")
                print(f"   Results returned: {len(orders_data.get('results', []))}")
                
                # Show order summary
                results = orders_data.get('results', [])
                if results:
                    print(f"   📋 Orders summary:")
                    for i, order in enumerate(results, 1):
                        print(f"     {i}. #{order['order_number']} - ${order['total']} ({order['status']})")
                        
                        # Show product types in this order
                        product_types = set()
                        for item in order.get('items', []):
                            product_types.add(item['product']['product_type'])
                        print(f"        Product types: {', '.join(product_types)}")
                else:
                    print(f"   ⚠️ No orders found")
            else:
                print(f"   ❌ Orders request failed: {orders_response.text}")
                
        except Exception as e:
            print(f"   ❌ Orders error: {str(e)}")
        
        # 3. Test single order detail (if orders exist)
        if 'orders_data' in locals() and orders_data.get('results'):
            first_order = orders_data['results'][0]
            order_id = first_order['id']
            
            print(f"\n3️⃣ Testing order detail for Order #{first_order['order_number']}...")
            
            try:
                detail_response = requests.get(f"{base_url}/api/orders/{order_id}/", headers=headers)
                print(f"   Detail status: {detail_response.status_code}")
                
                if detail_response.status_code == 200:
                    print(f"   ✅ Order detail retrieved successfully")
                    detail_headers = dict(detail_response.headers)
                    medixmall_detail_header = detail_headers.get('X-MedixMall-Mode', 'Not present')
                    print(f"   X-MedixMall-Mode header: {medixmall_detail_header}")
                else:
                    print(f"   ❌ Detail request failed: {detail_response.text}")
                    
            except Exception as e:
                print(f"   ❌ Detail error: {str(e)}")

def test_user_medixmall_status():
    print(f"\n🔍 CHECKING USER MEDIXMALL STATUS IN DATABASE:")
    
    try:
        user = User.objects.get(email='user@example.com')
        print(f"   User: {user.full_name} ({user.email})")
        print(f"   MedixMall mode: {user.medixmall_mode}")
        
        orders = Order.objects.filter(user=user)
        print(f"   Total orders: {orders.count()}")
        
        for order in orders:
            product_types = set()
            for item in order.items.all():
                product_types.add(item.product.product_type)
            print(f"     #{order.order_number}: {', '.join(product_types)} products")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    # Test database state first
    test_user_medixmall_status()
    
    # Test API endpoints
    test_orders_fix_comprehensive()
