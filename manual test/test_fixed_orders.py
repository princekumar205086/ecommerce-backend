#!/usr/bin/env python3

"""
Test the fixed orders endpoint to verify it returns all user orders
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

User = get_user_model()
BASE_URL = "http://127.0.0.1:8000"  # Test locally first

def test_fixed_orders_api():
    print("=== TESTING FIXED ORDERS API ===")
    
    # 1. Authenticate
    print("🔐 Authenticating user...")
    auth_response = requests.post(f"{BASE_URL}/api/accounts/login/", json={
        "email": "user@example.com",
        "password": "User@123"
    })
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.text}")
        return
    
    auth_data = auth_response.json()
    access_token = auth_data['access']
    print(f"✅ Authentication successful")
    print(f"User: {auth_data['user']}")
    
    # 2. Test orders endpoint
    print("\n📦 Testing orders endpoint...")
    headers = {'Authorization': f'Bearer {access_token}'}
    
    orders_response = requests.get(f"{BASE_URL}/api/orders/", headers=headers)
    print(f"Status Code: {orders_response.status_code}")
    print(f"Response Headers: {dict(orders_response.headers)}")
    
    if orders_response.status_code == 200:
        orders_data = orders_response.json()
        print(f"✅ Orders retrieved successfully!")
        print(f"Orders count: {orders_data.get('count', 0)}")
        print(f"Results count: {len(orders_data.get('results', []))}")
        
        # Show basic order info
        for order in orders_data.get('results', []):
            print(f"  - Order #{order['order_number']} (Status: {order['status']}, Total: ${order['total']})")
            items_summary = []
            for item in order.get('items', []):
                product_type = item['product']['product_type']
                items_summary.append(f"{item['product']['name']} ({product_type})")
            print(f"    Items: {', '.join(items_summary)}")
        
        # Check if X-MedixMall-Mode header is removed
        medixmall_header = orders_response.headers.get('X-MedixMall-Mode')
        if medixmall_header:
            print(f"⚠️ X-MedixMall-Mode header still present: {medixmall_header}")
        else:
            print("✅ X-MedixMall-Mode header removed (as expected)")
            
    else:
        print(f"❌ Orders endpoint failed: {orders_response.text}")

if __name__ == "__main__":
    test_fixed_orders_api()
