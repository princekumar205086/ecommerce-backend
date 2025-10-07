#!/usr/bin/env python3
"""
Simple test to check new payment endpoint
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {
    "email": "testuser@example.com",
    "password": "testpass123"
}

def test_simple():
    print("🔍 Testing new payment endpoint...")
    
    # Step 1: Authenticate
    print("\n1. Authenticating...")
    auth_response = requests.post(f"{BASE_URL}/api/token/", data=TEST_USER)
    if auth_response.status_code != 200:
        print(f"❌ Auth failed: {auth_response.status_code}")
        print(auth_response.text)
        return
    
    token = auth_response.json()["access"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authenticated")
    
    # Step 2: Create cart with items
    print("\n2. Setting up cart...")
    
    # Clear cart first
    requests.delete(f"{BASE_URL}/api/cart/clear/", headers=headers)
    
    # Add items to cart
    add_response = requests.post(f"{BASE_URL}/api/cart/add/", 
                               json={"product_id": 46, "quantity": 2}, 
                               headers=headers)
    print(f"Add to cart: {add_response.status_code}")
    
    # Get cart
    cart_response = requests.get(f"{BASE_URL}/api/cart/", headers=headers)
    if cart_response.status_code == 200:
        cart_data = cart_response.json()
        cart_id = cart_data.get('id')
        print(f"✅ Cart ID: {cart_id}")
    else:
        print(f"❌ Cart get failed: {cart_response.status_code}")
        return
    
    # Step 3: Test new payment endpoint
    print("\n3. Testing new payment endpoint...")
    test_data = {
        "cart_id": cart_id,
        "shipping_address": {
            "first_name": "John",
            "last_name": "Doe",
            "address_line_1": "123 Test St",
            "city": "Test City",
            "state": "Test State",
            "postal_code": "12345",
            "country": "IN",
            "phone": "+91-9876543210"
        },
        "billing_address": {
            "first_name": "John",
            "last_name": "Doe",
            "address_line_1": "123 Test St",
            "city": "Test City",
            "state": "Test State",
            "postal_code": "12345",
            "country": "IN",
            "phone": "+91-9876543210"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/payments/create-from-cart/", 
                           json=test_data, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    if 'application/json' in response.headers.get('content-type', ''):
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            if response.status_code == 200:
                print("✅ NEW PAYMENT-FIRST FLOW WORKING!")
                print(f"🎯 Razorpay Order ID: {result.get('order_id')}")
            else:
                print("❌ Payment creation failed")
        except:
            print(f"JSON decode failed: {response.text[:500]}")
    else:
        print(f"HTML Response (first 500 chars): {response.text[:500]}")

if __name__ == "__main__":
    test_simple()