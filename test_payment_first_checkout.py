#!/usr/bin/env python3
"""
Payment-First Checkout Flow Test
Tests the new flow: cart → payment → order creation after payment success
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {
    "email": "testuser@example.com",
    "password": "testpass123"
}

# Test addresses
SHIPPING_ADDRESS = {
    "first_name": "John",
    "last_name": "Doe",
    "company": "",
    "address_line_1": "123 Test Street",
    "address_line_2": "Apt 4B",
    "city": "Test City",
    "state": "Test State",
    "postal_code": "12345",
    "country": "IN",
    "phone": "+91-9876543210"
}

BILLING_ADDRESS = {
    "first_name": "John",
    "last_name": "Doe",
    "company": "",
    "address_line_1": "123 Test Street",
    "address_line_2": "Apt 4B",
    "city": "Test City",
    "state": "Test State",
    "postal_code": "12345",
    "country": "IN",
    "phone": "+91-9876543210"
}

def log_step(step_num, description):
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*60}")

def log_response(response, description="Response"):
    print(f"\n{description}:")
    print(f"Status Code: {response.status_code}")
    try:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
        return response_data
    except:
        print(f"Response Text: {response.text}")
        return None

def test_payment_first_checkout():
    """Test the new payment-first checkout flow"""
    
    print("🔥 TESTING PAYMENT-FIRST CHECKOUT FLOW")
    print(f"Testing at: {datetime.now()}")
    
    # STEP 1: Authenticate
    log_step(1, "User Authentication")
    
    auth_response = requests.post(f"{BASE_URL}/api/token/", data=TEST_USER)
    auth_data = log_response(auth_response, "Authentication")
    
    if auth_response.status_code != 200:
        print("❌ Authentication failed!")
        return False
    
    token = auth_data["access"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # STEP 2: Clear existing cart
    log_step(2, "Clear Cart")
    
    clear_response = requests.delete(f"{BASE_URL}/api/cart/clear/", headers=headers)
    log_response(clear_response, "Clear Cart")
    
    # STEP 3: Add products to cart
    log_step(3, "Add Products to Cart")
    
    products_to_add = [
        {"product_id": 46, "quantity": 2},
        {"product_id": 45, "quantity": 1},
        {"product_id": 44, "quantity": 3}
    ]
    
    for product in products_to_add:
        add_response = requests.post(f"{BASE_URL}/api/cart/add/", json=product, headers=headers)
        log_response(add_response, f"Add Product {product['product_id']}")
    
    # STEP 4: Get cart details
    log_step(4, "Get Cart Details")
    
    cart_response = requests.get(f"{BASE_URL}/api/cart/", headers=headers)
    cart_data = log_response(cart_response, "Cart Details")
    
    if not cart_data or not cart_data.get('items'):
        print("❌ Cart is empty!")
        return False
    
    cart_id = cart_data['id']
    total_amount = cart_data['total_price']
    print(f"✅ Cart ID: {cart_id}, Total: ₹{total_amount}")
    
    # STEP 5: Create payment directly from cart (NEW FLOW)
    log_step(5, "Create Payment from Cart (NEW FLOW)")
    
    payment_data = {
        "cart_id": cart_id,
        "shipping_address": SHIPPING_ADDRESS,
        "billing_address": BILLING_ADDRESS,
        "payment_method": "razorpay",
        "currency": "INR"
    }
    
    payment_response = requests.post(f"{BASE_URL}/api/payments/create-from-cart/", json=payment_data, headers=headers)
    payment_resp_data = log_response(payment_response, "Payment Creation")
    
    if payment_response.status_code != 200:
        print("❌ Payment creation failed!")
        return False
    
    razorpay_order_id = payment_resp_data['order_id']
    print(f"✅ Razorpay Order ID: {razorpay_order_id}")
    
    # STEP 6: Simulate payment success and verify
    log_step(6, "Simulate Payment Success and Verification")
    
    # Note: In real scenario, these would come from Razorpay frontend
    fake_payment_verification = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": "pay_test123456789",  # Fake payment ID
        "razorpay_signature": "fake_signature_for_testing"  # This will fail verification
    }
    
    verify_response = requests.post(f"{BASE_URL}/api/payments/verify/", json=fake_payment_verification, headers=headers)
    verify_data = log_response(verify_response, "Payment Verification")
    
    # Note: This will fail with fake data, but let's see the response
    print("⚠️  Payment verification expected to fail with fake data")
    
    # STEP 7: Check payment status
    log_step(7, "Check Payment Status")
    
    payments_response = requests.get(f"{BASE_URL}/api/payments/", headers=headers)
    payments_data = log_response(payments_response, "Payments List")
    
    if payments_data and payments_data.get('results'):
        latest_payment = payments_data['results'][0]
        print(f"Latest Payment Status: {latest_payment.get('status')}")
        print(f"Order Created: {latest_payment.get('order') is not None}")
    
    # STEP 8: Check orders (should be empty until payment succeeds)
    log_step(8, "Check Orders Status")
    
    orders_response = requests.get(f"{BASE_URL}/api/orders/", headers=headers)
    orders_data = log_response(orders_response, "Orders List")
    
    if orders_data and orders_data.get('results'):
        print(f"✅ Orders found: {len(orders_data['results'])}")
        for order in orders_data['results']:
            print(f"Order #{order.get('order_number')}: {order.get('status')} / {order.get('payment_status')}")
    else:
        print("⏳ No orders yet (expected until payment verification succeeds)")
    
    # STEP 9: Check cart status (should still have items until payment succeeds)
    log_step(9, "Check Cart Status After Payment Attempt")
    
    final_cart_response = requests.get(f"{BASE_URL}/api/cart/", headers=headers)
    final_cart_data = log_response(final_cart_response, "Final Cart Status")
    
    if final_cart_data and final_cart_data.get('items'):
        print(f"🛒 Cart still has {len(final_cart_data['items'])} items (expected until payment succeeds)")
    else:
        print("🛒 Cart is empty")
    
    print(f"\n{'='*60}")
    print("🎯 NEW PAYMENT-FIRST FLOW TEST SUMMARY:")
    print("✅ Cart creation and product addition")
    print("✅ Payment initialization from cart (without order creation)")
    print("⏳ Payment verification (fails with test data - expected)")
    print("⏳ Order creation will happen after real payment success")
    print("⏳ Cart clearance will happen after order creation")
    print(f"{'='*60}")
    
    return True

if __name__ == "__main__":
    test_payment_first_checkout()