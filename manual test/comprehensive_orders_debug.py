#!/usr/bin/env python3

"""
End-to-end test to debug orders API issue for user@example.com
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

BASE_URL = "https://backend.okpuja.in"

def test_authentication_endpoints():
    print("=== TESTING AUTHENTICATION ENDPOINTS ===")
    
    # Test credentials
    credentials = {
        "email": "user@example.com",
        "password": "User@123"
    }
    
    endpoints_to_test = [
        "/api/accounts/login/",
        "/api/token/",
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🔐 Testing {endpoint}")
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=credentials)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Response keys: {list(data.keys())}")
                access_token = data.get('access')
                if access_token:
                    print(f"Access token (first 50 chars): {access_token[:50]}...")
                    return access_token
                else:
                    print("⚠️ No access token in response")
            else:
                print(f"❌ Failed: {response.text[:500]}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    return None

def test_orders_endpoint_with_token(access_token):
    print(f"\n=== TESTING ORDERS ENDPOINT WITH TOKEN ===")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔍 Testing GET {BASE_URL}/api/orders/")
    
    try:
        response = requests.get(f"{BASE_URL}/api/orders/", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response structure: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
            print(f"Full response: {json.dumps(data, indent=2, default=str)}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def check_order_model_and_serializer():
    print(f"\n=== CHECKING ORDER MODEL AND SERIALIZER ===")
    
    try:
        user = User.objects.get(email='user@example.com')
        orders = Order.objects.filter(user=user)
        
        print(f"User ID: {user.id}")
        print(f"Orders count: {orders.count()}")
        
        if orders.exists():
            order = orders.first()
            print(f"Sample order ID: {order.id}")
            print(f"Order status: {order.status}")
            print(f"Order total: {order.total}")
            print(f"Order created_at: {order.created_at}")
            
            # Check if order has all necessary fields
            print(f"Order fields check:")
            print(f"  - user: {order.user}")
            print(f"  - order_number: {order.order_number}")
            print(f"  - status: {order.status}")
            print(f"  - payment_status: {getattr(order, 'payment_status', 'N/A')}")
            
            # Try to serialize the order manually
            from orders.serializers import OrderSerializer
            from django.test import RequestFactory
            from rest_framework.request import Request
            
            factory = RequestFactory()
            request = factory.get('/api/orders/')
            request.user = user
            
            serializer = OrderSerializer(order, context={'request': request})
            serialized_data = serializer.data
            
            print(f"✅ Serialization successful")
            print(f"Serialized fields: {list(serialized_data.keys())}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def check_orders_view_permissions():
    print(f"\n=== CHECKING ORDERS VIEW PERMISSIONS ===")
    
    try:
        from orders.views import OrderViewSet
        from orders.permissions import IsOwner
        
        print(f"OrderViewSet permission classes: {OrderViewSet.permission_classes}")
        
        # Check if there are any role-based restrictions
        user = User.objects.get(email='user@example.com')
        print(f"User role: {getattr(user, 'role', 'N/A')}")
        
        # Check if user can access their orders
        orders = Order.objects.filter(user=user)
        print(f"User can access {orders.count()} orders")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 COMPREHENSIVE ORDERS DEBUG TEST")
    print("="*50)
    
    # Test local database first
    check_order_model_and_serializer()
    check_orders_view_permissions()
    
    # Test API endpoints
    access_token = test_authentication_endpoints()
    
    if access_token:
        test_orders_endpoint_with_token(access_token)
    else:
        print("\n❌ Could not get access token, skipping API tests")
    
    print("\n🏁 DEBUG TEST COMPLETE")

if __name__ == "__main__":
    main()
