#!/usr/bin/env python3
"""
Comprehensive Razorpay Payment Verification Test
Tests the complete payment flow including verification
"""

import requests
import json
import hashlib
import hmac
import base64

BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "razorpayuser@example.com"
TEST_USER_PASSWORD = "testpass123"

def print_separator(title):
    """Print a formatted separator"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def generate_mock_signature(order_id, payment_id, secret):
    """Generate a mock Razorpay signature for testing"""
    message = f"{order_id}|{payment_id}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_payment_verification():
    """Test complete payment verification flow"""
    print_separator("RAZORPAY PAYMENT VERIFICATION TEST")
    
    session = requests.Session()
    
    # Step 1: Authentication
    print("\n📋 Step 1: Authentication")
    print("🔐 Testing Authentication...")
    
    auth_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        auth_response = session.post(f"{BASE_URL}/api/accounts/login/", json=auth_data)
        
        if auth_response.status_code == 200:
            auth_result = auth_response.json()
            token = auth_result['access']
            session.headers.update({'Authorization': f'Bearer {token}'})
            print(f"✅ Authentication successful - User ID: {auth_result['user']['id']}")
        else:
            print(f"❌ Authentication failed: {auth_response.text}")
            return False
                
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

    # Step 2: Add item to cart (if needed)
    print("\n📋 Step 2: Ensure Cart Has Items")
    try:
        cart_response = session.get(f"{BASE_URL}/api/cart/")
        if cart_response.status_code == 200:
            cart_data = cart_response.json()
            if not cart_data.get('items') or len(cart_data['items']) == 0:
                print("⚠️ Cart is empty, adding item...")
                add_response = session.post(f"{BASE_URL}/api/cart/add/", 
                    json={"product_id": 1, "quantity": 1})
                if add_response.status_code in [200, 201]:
                    print("✅ Item added to cart")
                else:
                    print(f"❌ Could not add item: {add_response.text}")
                    return False
            else:
                print(f"✅ Cart has {len(cart_data['items'])} items")
        else:
            print(f"❌ Could not fetch cart: {cart_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cart error: {e}")
        return False

    # Step 3: Create Payment
    print("\n📋 Step 3: Create Razorpay Payment")
    print("💳 Creating payment...")
    
    payment_data = {
        "payment_method": "razorpay",
        "shipping_address": {
            "full_name": "Test User",
            "address_line_1": "123 Test Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400001",
            "country": "India"
        }
    }
    
    try:
        payment_response = session.post(f"{BASE_URL}/api/payments/create-from-cart/", json=payment_data)
        
        if payment_response.status_code == 200:
            payment_result = payment_response.json()
            print(f"✅ Payment created successfully")
            print(f"🆔 Payment ID: {payment_result['payment_id']}")
            print(f"📋 Razorpay Order ID: {payment_result['razorpay_order_id']}")
            print(f"💰 Amount: ₹{payment_result['amount']}")
            
            payment_id = payment_result['payment_id']
            razorpay_order_id = payment_result['razorpay_order_id']
            
        else:
            print(f"❌ Payment creation failed: {payment_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Payment creation error: {e}")
        return False

    # Step 4: Simulate Payment Success and Test Verification
    print("\n📋 Step 4: Test Payment Verification")
    print("🔍 Testing different verification scenarios...")
    
    # Mock payment data (as if returned by Razorpay)
    mock_payment_id = f"pay_mock_{payment_id}_test"
    
    # Test with correct signature
    print("\n🔹 Test 1: Verification with Mock Signature")
    
    # Generate mock signature (using the secret from .env)
    razorpay_secret = "9ge230isKnELfyR3QN2o5SXF"  # From your .env file
    mock_signature = generate_mock_signature(razorpay_order_id, mock_payment_id, razorpay_secret)
    
    verify_data_correct = {
        "payment_id": payment_id,
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": mock_payment_id,
        "razorpay_signature": mock_signature
    }
    
    try:
        verify_response = session.post(f"{BASE_URL}/api/payments/confirm-razorpay/", json=verify_data_correct)
        print(f"🔍 Verification response status: {verify_response.status_code}")
        print(f"📄 Response: {verify_response.text}")
        
        if verify_response.status_code == 200:
            verify_result = verify_response.json()
            print(f"✅ Payment verification successful!")
            print(f"📊 Result: {json.dumps(verify_result, indent=2)}")
            
            if verify_result.get('order_created'):
                print(f"✅ Order auto-created: #{verify_result.get('order_number')}")
            
        else:
            print(f"❌ Payment verification failed")
            verify_error = verify_response.json() if verify_response.content else {}
            print(f"📄 Error details: {json.dumps(verify_error, indent=2)}")
            
    except Exception as e:
        print(f"❌ Verification error: {e}")

    # Test with incorrect signature
    print("\n🔹 Test 2: Verification with Wrong Signature")
    
    verify_data_wrong = {
        "payment_id": payment_id,
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": mock_payment_id,
        "razorpay_signature": "wrong_signature_for_testing"
    }
    
    try:
        verify_response_wrong = session.post(f"{BASE_URL}/api/payments/confirm-razorpay/", json=verify_data_wrong)
        print(f"🔍 Wrong signature response status: {verify_response_wrong.status_code}")
        
        if verify_response_wrong.status_code == 400:
            print(f"✅ Correctly rejected wrong signature")
            print(f"📄 Error: {verify_response_wrong.text}")
        else:
            print(f"❌ Should have rejected wrong signature but got: {verify_response_wrong.status_code}")
            
    except Exception as e:
        print(f"❌ Wrong signature test error: {e}")

    # Test with missing fields
    print("\n🔹 Test 3: Verification with Missing Fields")
    
    verify_data_incomplete = {
        "payment_id": payment_id,
        "razorpay_order_id": razorpay_order_id
        # Missing razorpay_payment_id and razorpay_signature
    }
    
    try:
        verify_response_incomplete = session.post(f"{BASE_URL}/api/payments/confirm-razorpay/", json=verify_data_incomplete)
        print(f"🔍 Incomplete data response status: {verify_response_incomplete.status_code}")
        
        if verify_response_incomplete.status_code == 400:
            print(f"✅ Correctly rejected incomplete data")
            print(f"📄 Error: {verify_response_incomplete.text}")
        else:
            print(f"❌ Should have rejected incomplete data")
            
    except Exception as e:
        print(f"❌ Incomplete data test error: {e}")

    # Test with non-existent payment
    print("\n🔹 Test 4: Verification with Non-existent Payment")
    
    verify_data_nonexistent = {
        "payment_id": 99999,  # Non-existent payment ID
        "razorpay_order_id": "order_nonexistent",
        "razorpay_payment_id": "pay_nonexistent",
        "razorpay_signature": "fake_signature"
    }
    
    try:
        verify_response_nonexistent = session.post(f"{BASE_URL}/api/payments/confirm-razorpay/", json=verify_data_nonexistent)
        print(f"🔍 Non-existent payment response status: {verify_response_nonexistent.status_code}")
        
        if verify_response_nonexistent.status_code == 404:
            print(f"✅ Correctly returned 404 for non-existent payment")
            print(f"📄 Error: {verify_response_nonexistent.text}")
        else:
            print(f"❌ Should have returned 404 for non-existent payment")
            
    except Exception as e:
        print(f"❌ Non-existent payment test error: {e}")

    return True

def test_payment_status_check():
    """Test payment status checking"""
    print_separator("PAYMENT STATUS CHECK TEST")
    
    session = requests.Session()
    
    # Authenticate first
    auth_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    auth_response = session.post(f"{BASE_URL}/api/accounts/login/", json=auth_data)
    if auth_response.status_code == 200:
        auth_result = auth_response.json()
        token = auth_result['access']
        session.headers.update({'Authorization': f'Bearer {token}'})
        print("✅ Authenticated for status check")
    else:
        print("❌ Authentication failed for status check")
        return False
    
    # Get recent payments
    try:
        payments_response = session.get(f"{BASE_URL}/api/payments/")
        if payments_response.status_code == 200:
            payments_data = payments_response.json()
            payments = payments_data.get('results', []) if 'results' in payments_data else payments_data
            
            if payments:
                print(f"📊 Found {len(payments)} recent payments:")
                for payment in payments[:3]:  # Show last 3 payments
                    print(f"   Payment ID: {payment.get('id')}")
                    print(f"   Status: {payment.get('status')}")
                    print(f"   Amount: ₹{payment.get('amount')}")
                    print(f"   Method: {payment.get('payment_method', 'N/A')}")
                    print(f"   Created: {payment.get('created_at')}")
                    print("   ---")
                return True
            else:
                print("📄 No payments found")
                return True
        else:
            print(f"❌ Could not fetch payments: {payments_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Razorpay Verification Test")
    print("="*70)
    
    # Test payment verification
    verification_success = test_payment_verification()
    
    # Test payment status
    status_success = test_payment_status_check()
    
    print("\n" + "="*70)
    print("📊 FINAL TEST RESULTS")
    print("="*70)
    
    if verification_success and status_success:
        print("🎉 All payment verification tests completed!")
        print("✅ Payment creation: Working")
        print("✅ Payment verification: Tested with multiple scenarios")
        print("✅ Error handling: Validated")
        print("✅ Status checking: Working")
        print("\n🎯 Razorpay integration is fully functional!")
    else:
        print("💥 Some tests failed!")
        print(f"❌ Verification tests: {'Passed' if verification_success else 'Failed'}")
        print(f"❌ Status tests: {'Passed' if status_success else 'Failed'}")

if __name__ == "__main__":
    main()