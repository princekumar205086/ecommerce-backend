#!/usr/bin/env python3

"""
Focused debug to understand why orders are not showing for user@example.com
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
BASE_URL = "https://backend.okpuja.in"

def test_orders_api_issue():
    print("=== FOCUSED ORDERS API DEBUG ===")
    
    # 1. Check database state
    user = User.objects.get(email='user@example.com')
    orders = Order.objects.filter(user=user)
    
    print(f"📊 DATABASE STATE:")
    print(f"  User: {user.full_name} ({user.email})")
    print(f"  User MedixMall mode: {user.medixmall_mode}")
    print(f"  User role: {user.role}")
    print(f"  Orders count: {orders.count()}")
    
    if orders.exists():
        for order in orders:
            print(f"    Order #{order.order_number} - Status: {order.status}")
            print(f"      Items: {order.items.count()}")
            for item in order.items.all():
                print(f"        - {item.product.name} (Type: {item.product.product_type})")
    
    print()
    
    # 2. Test authentication
    print("🔐 TESTING AUTHENTICATION:")
    auth_response = requests.post(f"{BASE_URL}/api/accounts/login/", json={
        "email": "user@example.com",
        "password": "User@123"
    })
    
    if auth_response.status_code == 200:
        auth_data = auth_response.json()
        access_token = auth_data['access']
        print(f"  ✅ Login successful")
        print(f"  User data: {auth_data['user']}")
        
        # 3. Test orders endpoint
        print("\n📦 TESTING ORDERS ENDPOINT:")
        headers = {'Authorization': f'Bearer {access_token}'}
        
        orders_response = requests.get(f"{BASE_URL}/api/orders/", headers=headers)
        print(f"  Status Code: {orders_response.status_code}")
        print(f"  Response Headers: {dict(orders_response.headers)}")
        
        if orders_response.status_code == 200:
            orders_data = orders_response.json()
            print(f"  Response: {json.dumps(orders_data, indent=2)}")
        else:
            print(f"  Error: {orders_response.text}")
        
        # 4. Test with MedixMall mode explicitly disabled
        print("\n🔄 DISABLING MEDIXMALL MODE:")
        mode_response = requests.put(f"{BASE_URL}/api/accounts/medixmall-mode/", 
                                   json={"medixmall_mode": False},
                                   headers=headers)
        print(f"  Mode toggle status: {mode_response.status_code}")
        if mode_response.status_code == 200:
            print(f"  Mode response: {mode_response.json()}")
        
        # Test orders again
        orders_response2 = requests.get(f"{BASE_URL}/api/orders/", headers=headers)
        print(f"  Orders status after mode toggle: {orders_response2.status_code}")
        print(f"  Response Headers: {dict(orders_response2.headers)}")
        
        if orders_response2.status_code == 200:
            orders_data2 = orders_response2.json()
            print(f"  Orders after mode toggle: {json.dumps(orders_data2, indent=2)}")
    else:
        print(f"  ❌ Login failed: {auth_response.text}")
    
    # 5. Check if there are any view-specific issues
    print("\n🔍 CHECKING ORDERS VIEW:")
    try:
        from orders.views import OrderListAPIView
        from orders.serializers import OrderSerializer
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/api/orders/')
        request.user = user
        
        view = OrderListAPIView()
        view.request = request
        queryset = view.get_queryset()
        
        print(f"  View queryset count: {queryset.count()}")
        if queryset.exists():
            print(f"  Orders in view queryset:")
            for order in queryset:
                print(f"    - Order #{order.order_number}")
                
    except Exception as e:
        print(f"  ❌ View check error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_orders_api_issue()
