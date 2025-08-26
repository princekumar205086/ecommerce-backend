#!/usr/bin/env python3
"""
Test COD Complete Flow: Cart → Payment → Order → Cart Cleanup
"""

import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("🚀 Testing COD Complete Flow")
    print("=" * 60)
    
    # Step 1: Login as test user
    print("🔐 Logging in as test user...")
    login_response = requests.post(f"{BASE_URL}/api/accounts/login/", json={
        "email": "testuser@example.com",
        "password": "testpass123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    login_data = login_response.json()
    token = login_data['access']
    headers = {'Authorization': f'Bearer {token}'}
    print(f"✅ Logged in successfully as {login_data['user']['email']}")
    
    # Step 2: Add item to cart
    print("\n🛒 Adding item to cart...")
    cart_response = requests.post(f"{BASE_URL}/api/cart/add/", 
        headers=headers,
        json={
            "product_id": 1,
            "quantity": 2
        }
    )
    
    if cart_response.status_code not in [200, 201]:
        print(f"❌ Cart add failed: {cart_response.text}")
        return False
    
    print("✅ Item added to cart")
    
    # Step 3: View cart
    print("\n📋 Viewing cart...")
    cart_view_response = requests.get(f"{BASE_URL}/api/cart/", headers=headers)
    
    if cart_view_response.status_code != 200:
        print(f"❌ Cart view failed: {cart_view_response.text}")
        return False
    
    cart_data = cart_view_response.json()
    print(f"✅ Cart retrieved: {cart_data.get('items', [])} items, Total: {cart_data.get('total', 'N/A')}")
    
    # Step 4: Create COD payment
    print("\n💰 Creating COD payment...")
    payment_response = requests.post(f"{BASE_URL}/api/payments/create-from-cart/", 
        headers=headers,
        json={
            "payment_method": "cod",
            "shipping_address": {
                "full_name": "Test User COD",
                "address_line_1": "123 COD Test Street",
                "address_line_2": "Apt 1",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "123456",
                "country": "India"
            }
        }
    )
    
    print(f"💳 Payment creation status: {payment_response.status_code}")
    print(f"💳 Payment response: {payment_response.text}")
    
    if payment_response.status_code not in [200, 201]:
        print(f"❌ Payment creation failed: {payment_response.text}")
        return False
    
    payment_data = payment_response.json()
    payment_id = payment_data['payment_id']
    print(f"✅ COD payment created: Payment ID {payment_id}")
    
    # Step 5: Confirm COD payment
    print("\n✅ Confirming COD payment...")
    confirm_response = requests.post(f"{BASE_URL}/api/payments/confirm-cod/", 
        headers=headers,
        json={
            "payment_id": payment_id,
            "cod_notes": "Test COD order"
        }
    )
    
    print(f"✅ COD confirmation status: {confirm_response.status_code}")
    print(f"✅ COD confirmation response: {confirm_response.text}")
    
    if confirm_response.status_code not in [200, 201]:
        print(f"❌ COD confirmation failed: {confirm_response.text}")
        return False
    
    confirm_data = confirm_response.json()
    if confirm_data.get('order_created'):
        order_id = confirm_data['order']['id']
        order_number = confirm_data['order']['order_number']
        print(f"✅ Order created successfully: #{order_number} (ID: {order_id})")
    else:
        print("❌ Order was not created")
        return False
    
    # Step 6: Verify cart is cleaned
    print("\n🗑️ Verifying cart cleanup...")
    cart_cleanup_response = requests.get(f"{BASE_URL}/api/cart/", headers=headers)
    
    if cart_cleanup_response.status_code != 200:
        print(f"❌ Cart verification failed: {cart_cleanup_response.text}")
        return False
    
    cart_cleanup_data = cart_cleanup_response.json()
    items_count = len(cart_cleanup_data.get('items', []))
    
    if items_count == 0:
        print("✅ Cart cleaned successfully after order creation")
    else:
        print(f"❌ Cart still has {items_count} items")
        return False
    
    # Step 7: Verify order exists
    print("\n📦 Verifying order creation...")
    order_response = requests.get(f"{BASE_URL}/api/orders/{order_id}/", headers=headers)
    
    if order_response.status_code != 200:
        print(f"❌ Order verification failed: {order_response.text}")
        return False
    
    order_data = order_response.json()
    print(f"✅ Order verified: #{order_data['order_number']}")
    print(f"   Status: {order_data['status']}")
    print(f"   Payment Status: {order_data['payment_status']}")
    print(f"   Total: {order_data['total']}")
    print(f"   Items: {len(order_data['items'])} items")
    
    print("\n" + "=" * 60)
    print("🎉 COD COMPLETE FLOW TEST SUCCESSFUL!")
    print("✅ Cart → Payment → Order → Cart Cleanup: ALL WORKING")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)