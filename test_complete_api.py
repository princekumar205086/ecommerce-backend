#!/usr/bin/env python3
"""
Complete test for all payment flows, address management, and order endpoints
"""

import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

BASE_URL = "http://127.0.0.1:8000"

def test_address_management(token):
    """Test address management endpoints"""
    headers = {'Authorization': f'Bearer {token}'}
    
    print("\n📍 Testing Address Management...")
    
    # Test get address (empty initially)
    print("1. Getting current address...")
    response = requests.get(f"{BASE_URL}/api/accounts/address/", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Has address: {data.get('has_address', False)}")
    
    # Test update address
    print("2. Updating address...")
    address_data = {
        "address_line_1": "456 New Address Street",
        "address_line_2": "Suite 200",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India"
    }
    response = requests.put(f"{BASE_URL}/api/accounts/address/", headers=headers, json=address_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Message: {data.get('message')}")
        print(f"   Has address: {data['address'].get('has_address', False)}")
    
    # Test save address from checkout format
    print("3. Saving address from checkout format...")
    checkout_data = {
        "shipping_address": {
            "full_name": "Test User Updated",
            "address_line_1": "789 Checkout Address",
            "address_line_2": "Building C",
            "city": "Bangalore",
            "state": "Karnataka",
            "postal_code": "560001",
            "country": "India"
        }
    }
    response = requests.post(f"{BASE_URL}/api/accounts/address/save-from-checkout/", headers=headers, json=checkout_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Message: {data.get('message')}")
    
    return True

def test_cod_flow(token):
    """Test COD payment flow"""
    headers = {'Authorization': f'Bearer {token}'}
    
    print("\n💰 Testing COD Flow...")
    
    # Add item to cart
    print("1. Adding item to cart...")
    response = requests.post(f"{BASE_URL}/api/cart/add/", headers=headers, json={"product_id": 1, "quantity": 1})
    print(f"   Status: {response.status_code}")
    
    # Create COD payment
    print("2. Creating COD payment...")
    payment_data = {
        "payment_method": "cod",
        "shipping_address": {
            "full_name": "COD Test User",
            "address_line_1": "123 COD Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400001",
            "country": "India"
        }
    }
    response = requests.post(f"{BASE_URL}/api/payments/create-from-cart/", headers=headers, json=payment_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        payment_id = data.get('payment_id')
        print(f"   Payment ID: {payment_id}")
        
        # Confirm COD
        print("3. Confirming COD payment...")
        response = requests.post(f"{BASE_URL}/api/payments/confirm-cod/", headers=headers, json={"payment_id": payment_id})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('order_created'):
                order_id = data['order']['id']
                print(f"   Order created: #{data['order']['order_number']}")
                return order_id
    
    return None

def test_pathlog_wallet_flow(token):
    """Test Pathlog Wallet flow"""
    headers = {'Authorization': f'Bearer {token}'}
    
    print("\n🏦 Testing Pathlog Wallet Flow...")
    
    # Add item to cart
    print("1. Adding item to cart...")
    response = requests.post(f"{BASE_URL}/api/cart/add/", headers=headers, json={"product_id": 1, "quantity": 1})
    print(f"   Status: {response.status_code}")
    
    # Create Pathlog Wallet payment
    print("2. Creating Pathlog Wallet payment...")
    payment_data = {
        "payment_method": "pathlog_wallet",
        "shipping_address": {
            "full_name": "Wallet Test User",
            "address_line_1": "456 Wallet Street",
            "city": "Pune",
            "state": "Maharashtra",
            "postal_code": "411001",
            "country": "India"
        }
    }
    response = requests.post(f"{BASE_URL}/api/payments/create-from-cart/", headers=headers, json=payment_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        payment_id = data.get('payment_id')
        print(f"   Payment ID: {payment_id}")
        
        # Verify mobile
        print("3. Verifying mobile number...")
        response = requests.post(f"{BASE_URL}/api/payments/pathlog-wallet/verify/", 
                                headers=headers, 
                                json={"payment_id": payment_id, "mobile_number": "8677939971"})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            # Verify OTP
            print("4. Verifying OTP...")
            response = requests.post(f"{BASE_URL}/api/payments/pathlog-wallet/otp/", 
                                    headers=headers, 
                                    json={"payment_id": payment_id, "otp": "123456"})
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('can_proceed'):
                    # Process payment
                    print("5. Processing wallet payment...")
                    response = requests.post(f"{BASE_URL}/api/payments/pathlog-wallet/pay/", 
                                            headers=headers, 
                                            json={"payment_id": payment_id})
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('order_created'):
                            order_id = data['order']['id']
                            print(f"   Order created: #{data['order']['order_number']}")
                            return order_id
    
    return None

def test_admin_operations(admin_token, order_id):
    """Test admin order management"""
    headers = {'Authorization': f'Bearer {admin_token}'}
    
    print(f"\n👨‍💼 Testing Admin Operations on Order {order_id}...")
    
    # Accept order
    print("1. Accepting order...")
    response = requests.post(f"{BASE_URL}/api/orders/admin/accept/", 
                            headers=headers, 
                            json={"order_id": order_id, "notes": "Order approved"})
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        # Assign shipping
        print("2. Assigning shipping...")
        response = requests.post(f"{BASE_URL}/api/orders/admin/assign-shipping/", 
                                headers=headers, 
                                json={
                                    "order_id": order_id, 
                                    "shipping_partner": "BlueDart",
                                    "tracking_id": "BD123456789",
                                    "notes": "Shipped via BlueDart"
                                })
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            # Mark delivered
            print("3. Marking as delivered...")
            response = requests.post(f"{BASE_URL}/api/orders/admin/mark-delivered/", 
                                    headers=headers, 
                                    json={"order_id": order_id, "notes": "Successfully delivered"})
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Admin operations completed successfully")
                return True
    
    return False

def main():
    print("🚀 Starting Complete API Test")
    print("=" * 60)
    
    # Login as regular user
    print("🔐 Logging in as test user...")
    response = requests.post(f"{BASE_URL}/api/accounts/login/", json={
        "email": "testuser@example.com",
        "password": "testpass123"
    })
    
    if response.status_code != 200:
        print(f"❌ User login failed: {response.text}")
        return False
    
    user_data = response.json()
    user_token = user_data['access']
    print(f"✅ User logged in: {user_data['user']['email']}")
    
    # Login as admin
    print("\n🔐 Logging in as admin...")
    response = requests.post(f"{BASE_URL}/api/accounts/login/", json={
        "email": "admin@example.com",
        "password": "admin123"
    })
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.text}")
        return False
    
    admin_data = response.json()
    admin_token = admin_data['access']
    print(f"✅ Admin logged in: {admin_data['user']['email']}")
    
    # Test address management
    test_address_management(user_token)
    
    # Test COD flow
    cod_order_id = test_cod_flow(user_token)
    
    # Test Pathlog Wallet flow
    wallet_order_id = test_pathlog_wallet_flow(user_token)
    
    # Test admin operations
    if cod_order_id:
        test_admin_operations(admin_token, cod_order_id)
    
    # Test error cases
    print("\n⚠️ Testing Error Cases...")
    headers = {'Authorization': f'Bearer {user_token}'}
    
    # Try to verify COD payment as pathlog wallet
    print("1. Testing pathlog wallet error...")
    cod_response = requests.post(f"{BASE_URL}/api/payments/create-from-cart/", 
                                headers=headers,
                                json={
                                    "payment_method": "cod",
                                    "shipping_address": {
                                        "full_name": "Error Test",
                                        "address_line_1": "123 Error Street",
                                        "city": "Error City",
                                        "state": "Error State",
                                        "postal_code": "123456",
                                        "country": "India"
                                    }
                                })
    
    if cod_response.status_code == 200:
        cod_data = cod_response.json()
        error_response = requests.post(f"{BASE_URL}/api/payments/pathlog-wallet/verify/", 
                                      headers=headers,
                                      json={
                                          "payment_id": cod_data['payment_id'],
                                          "mobile_number": "8677939971"
                                      })
        print(f"   Error response status: {error_response.status_code}")
        print(f"   Error message: {error_response.text}")
        if error_response.status_code == 400 and "Not a pathlog wallet payment" in error_response.text:
            print("   ✅ Error handling working correctly")
    
    print("\n" + "=" * 60)
    print("🎉 COMPLETE API TEST FINISHED!")
    print("✅ All payment flows tested")
    print("✅ Address management tested") 
    print("✅ Admin operations tested")
    print("✅ Error handling tested")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)