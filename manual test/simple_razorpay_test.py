#!/usr/bin/env python3
"""
Simple Razorpay Payment API Test
Tests just the payment creation to verify Razorpay key is returned
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_razorpay_payment_api():
    """Test Razorpay payment creation API"""
    print("🔍 Testing Razorpay Payment Creation API")
    print("="*50)
    
    # Use existing user credentials (from previous tests)
    auth_data = {
        "email": "razorpayuser@example.com",
        "password": "testpass123"
    }
    
    # Step 1: Authenticate
    print("\n1. Authenticating...")
    auth_response = requests.post(f"{BASE_URL}/api/accounts/login/", json=auth_data)
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        print("Response:", auth_response.text)
        return False
    
    auth_result = auth_response.json()
    token = auth_result['access']
    headers = {'Authorization': f'Bearer {token}'}
    print(f"✅ Authentication successful")
    
    # Step 2: Check current cart (use existing cart or add item)
    print("\n2. Checking cart...")
    cart_response = requests.get(f"{BASE_URL}/api/cart/", headers=headers)
    
    if cart_response.status_code == 200:
        cart_data = cart_response.json()
        if cart_data.get('items') and len(cart_data['items']) > 0:
            print(f"✅ Cart has {len(cart_data['items'])} items")
            total = cart_data.get('total', 'Unknown')
            print(f"💰 Cart total: ₹{total}")
        else:
            print("⚠️ Cart is empty, attempting to add item...")
            # Try to add an item (using existing product ID 1)
            add_response = requests.post(f"{BASE_URL}/api/cart/add/", 
                json={"product_id": 1, "quantity": 1}, headers=headers)
            if add_response.status_code in [200, 201]:
                print("✅ Item added to cart")
            else:
                print(f"❌ Could not add item to cart: {add_response.text}")
                return False
    else:
        print(f"❌ Could not fetch cart: {cart_response.status_code}")
        return False
    
    # Step 3: Create Razorpay Payment
    print("\n3. Creating Razorpay Payment...")
    payment_data = {
        "payment_method": "razorpay",
        "shipping_address": {
            "full_name": "Razorpay Test User",
            "address_line_1": "123 Razorpay Street",
            "address_line_2": "Test Building",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400001",
            "country": "India"
        },
        "currency": "INR"
    }
    
    payment_response = requests.post(f"{BASE_URL}/api/payments/create-from-cart/", 
        json=payment_data, headers=headers)
    
    print(f"Status Code: {payment_response.status_code}")
    print(f"Response Headers: {dict(payment_response.headers)}")
    
    if payment_response.status_code == 200:
        try:
            result = payment_response.json()
            print(f"\n📄 Complete Response:")
            print(json.dumps(result, indent=2))
            
            # Check for Razorpay key
            print(f"\n🔍 Checking for Razorpay keys...")
            
            keys_found = []
            if 'razorpay_key' in result:
                keys_found.append(f"razorpay_key: {result['razorpay_key']}")
            if 'key' in result:
                keys_found.append(f"key: {result['key']}")
            if 'razorpay_order_id' in result:
                keys_found.append(f"razorpay_order_id: {result['razorpay_order_id']}")
            
            if keys_found:
                print("✅ Required Razorpay fields found:")
                for key in keys_found:
                    print(f"   {key}")
                
                # Validate key format
                razorpay_key = result.get('razorpay_key') or result.get('key')
                if razorpay_key and razorpay_key.startswith('rzp_'):
                    print(f"✅ Razorpay key format is valid: {razorpay_key}")
                    return True
                else:
                    print(f"❌ Invalid Razorpay key format: {razorpay_key}")
                    return False
            else:
                print("❌ No Razorpay keys found in response")
                print("Available keys:", list(result.keys()))
                return False
                
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            print(f"Raw response: {payment_response.text}")
            return False
    else:
        print(f"❌ Payment creation failed")
        print(f"Response: {payment_response.text}")
        return False

if __name__ == "__main__":
    success = test_razorpay_payment_api()
    if success:
        print("\n🎉 Razorpay API Test PASSED!")
        print("✅ Server is returning Razorpay key correctly")
    else:
        print("\n💥 Razorpay API Test FAILED!")
        print("❌ Server is NOT returning Razorpay key properly")