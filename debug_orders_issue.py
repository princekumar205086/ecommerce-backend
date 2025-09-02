#!/usr/bin/env python3

"""
Debug script to investigate why orders endpoint returns empty results
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
from django.db import connection

User = get_user_model()

def debug_orders_issue():
    print("=== DEBUGGING ORDERS ISSUE ===")
    print(f"Current time: {datetime.now()}")
    print()
    
    # 1. Check if user exists
    print("1. Checking user existence...")
    try:
        user = User.objects.get(email='user@example.com')
        print(f"✓ User found: {user.full_name} (ID: {user.id}, Email: {user.email})")
        print(f"  - is_active: {user.is_active}")
        print(f"  - is_staff: {user.is_staff}")
        print(f"  - is_superuser: {user.is_superuser}")
        print(f"  - date_joined: {user.date_joined}")
    except User.DoesNotExist:
        print("✗ User not found with email 'user@example.com'")
        # Check all users with similar emails
        users = User.objects.filter(email__icontains='example.com')
        print(f"Found {users.count()} users with 'example.com' in email:")
        for u in users:
            print(f"  - {u.full_name} ({u.email}) - ID: {u.id}")
        return
    
    print()
    
    # 2. Check orders in database
    print("2. Checking orders in database...")
    all_orders = Order.objects.all()
    print(f"Total orders in database: {all_orders.count()}")
    
    if all_orders.exists():
        print("Recent orders:")
        for order in all_orders.order_by('-created_at')[:5]:
            print(f"  - Order #{order.order_number} (ID: {order.id})")
            print(f"    User: {order.user.full_name} ({order.user.email})")
            print(f"    Status: {order.status}")
            print(f"    Total: ${order.total}")
            print(f"    Created: {order.created_at}")
            print()
    
    # 3. Check orders for specific user
    print(f"3. Checking orders for user {user.email}...")
    user_orders = Order.objects.filter(user=user)
    print(f"Orders for this user: {user_orders.count()}")
    
    if user_orders.exists():
        print("User's orders:")
        for order in user_orders.order_by('-created_at'):
            print(f"  - Order #{order.order_number} (ID: {order.id})")
            print(f"    Status: {order.status}")
            print(f"    Total: ${order.total}")
            print(f"    Created: {order.created_at}")
    
    print()
    
    # 4. Check database tables directly
    print("4. Checking database tables directly...")
    with connection.cursor() as cursor:
        # Check orders table
        cursor.execute("SELECT COUNT(*) FROM orders_order")
        total_orders = cursor.fetchone()[0]
        print(f"Total orders in orders_order table: {total_orders}")
        
        # Check orders for this user
        cursor.execute("SELECT COUNT(*) FROM orders_order WHERE user_id = %s", [user.id])
        user_orders_count = cursor.fetchone()[0]
        print(f"Orders for user ID {user.id}: {user_orders_count}")
        
        # Get sample order data
        cursor.execute("""
            SELECT id, order_number, status, payment_status, total, created_at, user_id 
            FROM orders_order 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 5
        """, [user.id])
        
        orders_data = cursor.fetchall()
        if orders_data:
            print("Raw order data from database:")
            for order_data in orders_data:
                print(f"  - ID: {order_data[0]}, Number: {order_data[1]}, Status: {order_data[2]}")
                print(f"    Payment: {order_data[3]}, Total: {order_data[4]}, Created: {order_data[5]}")
    
    print()
    
    # 5. Test JWT token generation
    print("5. Testing JWT token generation...")
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        print(f"✓ JWT token generated successfully")
        print(f"Token (first 50 chars): {access_token[:50]}...")
        
        # Verify token payload
        from rest_framework_simplejwt.tokens import UntypedToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        try:
            UntypedToken(access_token)
            print("✓ Token is valid")
        except (InvalidToken, TokenError) as e:
            print(f"✗ Token validation failed: {e}")
            
    except Exception as e:
        print(f"✗ Token generation failed: {e}")
    
    print()
    
    # 6. Test API endpoint directly
    print("6. Testing API endpoint directly...")
    
    # First, let's check what the actual API response looks like
    base_url = "https://backend.okpuja.in"
    
    # Test authentication
    auth_data = {
        "email": "user@example.com",
        "password": "User@123"
    }
    
    try:
        print("6a. Testing authentication...")
        auth_response = requests.post(f"{base_url}/api/auth/login/", json=auth_data)
        print(f"Auth status code: {auth_response.status_code}")
        
        if auth_response.status_code == 200:
            auth_result = auth_response.json()
            access_token = auth_result.get('access')
            print(f"✓ Authentication successful")
            print(f"Access token (first 50 chars): {access_token[:50]}...")
            
            # Test orders endpoint
            print("6b. Testing orders endpoint...")
            headers = {'Authorization': f'Bearer {access_token}'}
            orders_response = requests.get(f"{base_url}/api/orders/", headers=headers)
            print(f"Orders endpoint status code: {orders_response.status_code}")
            
            if orders_response.status_code == 200:
                orders_data = orders_response.json()
                print(f"Orders response: {json.dumps(orders_data, indent=2)}")
                print(f"Number of orders returned: {orders_data.get('count', 0)}")
            else:
                print(f"Orders endpoint error: {orders_response.text}")
                
        else:
            print(f"✗ Authentication failed: {auth_response.text}")
            
    except Exception as e:
        print(f"✗ API test failed: {e}")
    
    print()
    
    # 7. Check for any model or serializer issues
    print("7. Checking model and serializer...")
    try:
        from orders.serializers import OrderSerializer
        from rest_framework.request import Request
        from django.test import RequestFactory
        
        # Create a mock request with user
        factory = RequestFactory()
        request = factory.get('/api/orders/')
        request.user = user
        
        # Get user orders and serialize
        user_orders = Order.objects.filter(user=user)
        serializer = OrderSerializer(user_orders, many=True, context={'request': request})
        serialized_data = serializer.data
        
        print(f"✓ Serializer works fine")
        print(f"Serialized orders count: {len(serialized_data)}")
        
        if serialized_data:
            print("Serialized order sample:")
            print(json.dumps(serialized_data[0] if serialized_data else {}, indent=2)[:500])
            
    except Exception as e:
        print(f"✗ Serializer test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_orders_issue()
