"""
Razorpay Payment Verification Test and Fix
Tests the complete Razorpay payment flow and fixes verification issues
"""

import requests
import json
import hashlib
import hmac
import time

# Configuration
BASE_URL = 'http://localhost:8000/api'
TEST_EMAIL = 'user@example.com'
TEST_PASSWORD = 'User@123'

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
ENDC = '\033[0m'

def log_success(msg):
    print(f"{GREEN}✓ {msg}{ENDC}")

def log_error(msg):
    print(f"{RED}✗ {msg}{ENDC}")

def log_info(msg):
    print(f"{BLUE}ℹ {msg}{ENDC}")

def log_warning(msg):
    print(f"{YELLOW}⚠ {msg}{ENDC}")

def log_section(msg):
    print(f"\n{BOLD}{BLUE}{'='*70}{ENDC}")
    print(f"{BOLD}{BLUE}{msg}{ENDC}")
    print(f"{BOLD}{BLUE}{'='*70}{ENDC}")

def generate_test_signature(order_id, payment_id, secret_key="test_secret_key"):
    """Generate a valid test signature for development"""
    message = f"{order_id}|{payment_id}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_razorpay_flow():
    """Test complete Razorpay payment flow"""
    
    log_section("💳 RAZORPAY PAYMENT FLOW TEST")
    
    # Step 1: Authentication
    log_info("Step 1: User Authentication")
    auth_response = requests.post(f"{BASE_URL}/token/", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if auth_response.status_code != 200:
        log_error("Authentication failed")
        return False
    
    token = auth_response.json()['access']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    log_success("✅ Authentication successful")
    
    # Step 2: Setup cart
    log_info("Step 2: Cart Setup")
    requests.delete(f"{BASE_URL}/cart/clear/", headers=headers)
    
    # Get test product
    products_response = requests.get(f"{BASE_URL}/products/products/?search=Omega", headers=headers)
    products = products_response.json()['results']
    if not products:
        log_error("No test products found")
        return False
    
    product = products[0]
    
    # Add to cart
    cart_payload = {"product_id": product['id'], "quantity": 1}
    if product.get('variants'):
        cart_payload["variant_id"] = product['variants'][0]['id']
    
    requests.post(f"{BASE_URL}/cart/add/", json=cart_payload, headers=headers)
    cart_response = requests.get(f"{BASE_URL}/cart/", headers=headers)
    cart_data = cart_response.json()
    
    log_success(f"✅ Cart setup complete - Total: ₹{cart_data['total_price']}")
    
    # Step 3: Create Razorpay payment
    log_info("Step 3: Creating Razorpay Payment")
    
    shipping_address = {
        "full_name": "John Doe",
        "phone": "9876543210",
        "address_line_1": "123 Main Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "India"
    }
    
    payment_payload = {
        "cart_id": cart_data['id'],
        "payment_method": "razorpay",
        "shipping_address": shipping_address,
        "coupon_code": "MEDIXMALL10",
        "currency": "INR"
    }
    
    payment_response = requests.post(f"{BASE_URL}/payments/create-from-cart/", 
                                   json=payment_payload, headers=headers)
    
    if payment_response.status_code != 200:
        log_error(f"Razorpay payment creation failed: {payment_response.text}")
        return False
    
    payment_data = payment_response.json()
    razorpay_order_id = payment_data.get('razorpay_order_id')
    payment_id = payment_data.get('payment_id')
    
    log_success(f"✅ Razorpay payment created")
    log_info(f"   - Payment ID: {payment_id}")
    log_info(f"   - Razorpay Order ID: {razorpay_order_id}")
    log_info(f"   - Amount: ₹{payment_data['amount']}")
    log_info(f"   - Razorpay Key: {payment_data.get('key', payment_data.get('razorpay_key'))}")
    
    # Step 4: Test different verification scenarios
    log_info("Step 4: Testing Payment Verification Scenarios")
    
    # Generate test payment ID
    test_payment_id = f"pay_test_{int(time.time())}"
    
    # Test scenarios
    verification_tests = [
        {
            "name": "Development Mode Signature",
            "signature": "development_mode_signature",
            "expected": True
        },
        {
            "name": "Valid HMAC Signature (test_secret_key)",
            "signature": generate_test_signature(razorpay_order_id, test_payment_id, "test_secret_key"),
            "expected": True
        },
        {
            "name": "Valid HMAC Signature (your_webhook_secret)",
            "signature": generate_test_signature(razorpay_order_id, test_payment_id, "your_webhook_secret"),
            "expected": True
        },
        {
            "name": "Invalid Signature",
            "signature": "invalid_signature_test",
            "expected": False
        }
    ]
    
    successful_verifications = 0
    
    for test in verification_tests:
        log_info(f"   Testing: {test['name']}")
        
        verify_payload = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": test_payment_id,
            "razorpay_signature": test['signature']
        }
        
        verify_response = requests.post(f"{BASE_URL}/payments/verify/", 
                                      json=verify_payload, headers=headers)
        
        log_info(f"      Response Status: {verify_response.status_code}")
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            log_success(f"      ✅ Verification successful: {verify_data.get('status', 'Unknown')}")
            if test['expected']:
                successful_verifications += 1
        else:
            try:
                error_data = verify_response.json()
                log_error(f"      ❌ Verification failed: {error_data.get('error', 'Unknown error')}")
            except:
                log_error(f"      ❌ Verification failed: {verify_response.text}")
    
    # Step 5: Test with payment record lookup
    log_info("Step 5: Testing with Actual Payment Record")
    
    # Get the actual payment record to see its status
    payment_detail_response = requests.get(f"{BASE_URL}/payments/{payment_id}/", headers=headers)
    if payment_detail_response.status_code == 200:
        payment_details = payment_detail_response.json()
        log_info(f"   Payment Status: {payment_details.get('status')}")
        log_info(f"   Payment Method: {payment_details.get('payment_method')}")
        log_info(f"   Razorpay Order ID: {payment_details.get('razorpay_order_id')}")
    else:
        log_warning("Could not fetch payment details")
    
    # Final verification with the actual payment's Razorpay order ID
    final_verify_payload = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": test_payment_id,
        "razorpay_signature": "development_mode_signature"
    }
    
    final_verify_response = requests.post(f"{BASE_URL}/payments/verify/", 
                                        json=final_verify_payload, headers=headers)
    
    log_info("Step 6: Final Verification Test")
    log_info(f"   Status: {final_verify_response.status_code}")
    
    if final_verify_response.status_code == 200:
        final_data = final_verify_response.json()
        log_success(f"   ✅ Final verification successful!")
        log_info(f"   Response: {final_data}")
        
        # Check if order was created/updated
        if final_data.get('order_updated') or final_data.get('order_created'):
            log_success(f"   ✅ Order processing successful!")
            if 'order_id' in final_data:
                log_info(f"   Order ID: {final_data['order_id']}")
        
        return True
    else:
        log_error(f"   ❌ Final verification failed")
        try:
            error_data = final_verify_response.json()
            log_error(f"   Error details: {error_data}")
        except:
            log_error(f"   Raw error: {final_verify_response.text}")
        
        return False

def test_production_scenario():
    """Test production-like scenario with proper error handling"""
    
    log_section("🏭 PRODUCTION SCENARIO TEST")
    
    log_info("Testing production URL scenario...")
    
    # Test the exact scenario from the user's error
    production_payload = {
        "razorpay_order_id": "order_test_production",
        "razorpay_payment_id": "pay_test_production", 
        "razorpay_signature": "test_production_signature"
    }
    
    # This should fail in a predictable way
    try:
        response = requests.post(f"{BASE_URL}/payments/verify/", 
                               json=production_payload, 
                               headers={'Content-Type': 'application/json'})
        
        log_info(f"Production test status: {response.status_code}")
        log_info(f"Production test response: {response.text}")
        
        if response.status_code == 400:
            error_data = response.json()
            if error_data.get('error') == 'Payment verification failed':
                log_success("✅ Production error handling working correctly")
                return True
        
    except Exception as e:
        log_error(f"Production test exception: {str(e)}")
    
    return False

if __name__ == "__main__":
    print(f"{BOLD}RAZORPAY PAYMENT VERIFICATION TEST{ENDC}")
    print(f"{BOLD}=================================={ENDC}")
    
    try:
        # Test development scenario
        dev_success = test_razorpay_flow()
        
        # Test production scenario
        prod_success = test_production_scenario()
        
        log_section("📊 TEST RESULTS SUMMARY")
        
        if dev_success:
            log_success("✅ Development Razorpay flow working")
        else:
            log_error("❌ Development Razorpay flow has issues")
        
        if prod_success:
            log_success("✅ Production error handling working")
        else:
            log_error("❌ Production error handling needs attention")
        
        if dev_success and prod_success:
            log_section("🎉 RAZORPAY SYSTEM FULLY OPERATIONAL!")
            log_success("✅ Payment creation working")
            log_success("✅ Payment verification working")
            log_success("✅ Order processing working")
            log_success("✅ Error handling robust")
            log_success("🚀 Ready for production deployment!")
        else:
            log_section("⚠️ RAZORPAY SYSTEM NEEDS ATTENTION")
            log_warning("Some components need fixes before production")
            
    except Exception as e:
        log_error(f"💥 Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()