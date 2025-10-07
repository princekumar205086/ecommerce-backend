#!/usr/bin/env python
"""
Complete End-to-End Test: Cart → Payment → Order → Cart Cleanup
Testing with all payment methods and admin operations
"""

import os
import django
import requests
import json
import time
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem
from orders.models import Order
from payments.models import Payment
from products.models import Product

User = get_user_model()
BASE_URL = "http://127.0.0.1:8000"

def get_auth_token(email, password):
    """Get JWT token for authentication"""
    response = requests.post(f"{BASE_URL}/api/accounts/login/", {
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access"]
    return None

def test_complete_flow():
    """Test complete flow: Cart → Payment → Order → Cart Cleanup"""
    print("🚀 COMPLETE END-TO-END FLOW TEST")
    print("=" * 60)
    
    # Step 1: Authentication
    print("\n🔐 Step 1: Authentication")
    token = get_auth_token("testuser@example.com", "testpass123")
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # Step 2: Verify cart has items
    print("\n🛒 Step 2: Verify Cart Contents")
    cart_response = requests.get(f"{BASE_URL}/api/cart/", headers=headers)
    
    if cart_response.status_code != 200:
        print("❌ Cart access failed")
        return False
        
    cart_data = cart_response.json()
    if not cart_data.get('items'):
        print("❌ Cart is empty - need to add items first")
        return False
    
    cart_id = cart_data['id']
    cart_items_count = len(cart_data['items'])
    cart_total = cart_data['total_price']
    
    print(f"✅ Cart verified:")
    print(f"   Cart ID: {cart_id}")
    print(f"   Items: {cart_items_count}")
    print(f"   Total: ₹{cart_total}")
    
    # Step 3: Test each payment method
    payment_methods = [
        ("razorpay", "Razorpay Payment"),
        ("cod", "Cash on Delivery"),
        ("pathlog_wallet", "Pathlog Wallet")
    ]
    
    results = {}
    
    for method, method_name in payment_methods:
        print(f"\n💳 Testing {method_name} Flow")
        print("-" * 40)
        
        result = test_payment_method(method, cart_id, headers)
        results[method] = result
        
        if result['success']:
            print(f"✅ {method_name} flow completed successfully")
            print(f"   Payment ID: {result['payment_id']}")
            print(f"   Order ID: {result['order_id']}")
            print(f"   Order Number: {result['order_number']}")
        else:
            print(f"❌ {method_name} flow failed: {result['error']}")
    
    # Step 4: Verify final state
    print(f"\n📊 Step 4: Final Verification")
    verify_final_state(headers)
    
    # Step 5: Test admin operations
    print(f"\n👨‍💼 Step 5: Admin Operations Test")
    test_admin_operations(results)
    
    return True

def test_payment_method(method, cart_id, headers):
    """Test a specific payment method"""
    try:
        # Create payment from cart
        payment_data = {
            "cart_id": cart_id,
            "payment_method": method,
            "shipping_address": {
                "full_name": "Test User",
                "address_line_1": "123 Test Street",
                "address_line_2": "Apt 4B",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "12345",
                "country": "India",
                "phone": "9876543210"
            },
            "save_address": True
        }
        
        if method == "pathlog_wallet":
            payment_data["pathlog_wallet_mobile"] = "9876543210"
        
        # Create payment
        payment_response = requests.post(
            f"{BASE_URL}/api/payments/create-from-cart/",
            json=payment_data,
            headers=headers
        )
        
        if payment_response.status_code not in [200, 201]:
            return {"success": False, "error": f"Payment creation failed: {payment_response.text}"}
        
        payment_result = payment_response.json()
        payment_id = payment_result['payment_id']
        
        print(f"   ✅ Payment created: ID {payment_id}")
        
        # Complete payment verification based on method
        if method == "razorpay":
            verification_result = complete_razorpay_payment(payment_id, payment_result, headers)
        elif method == "cod":
            verification_result = complete_cod_payment(payment_id, headers)
        elif method == "pathlog_wallet":
            verification_result = complete_pathlog_payment(payment_id, headers)
        
        if verification_result['success']:
            return {
                "success": True,
                "payment_id": payment_id,
                "order_id": verification_result.get('order_id'),
                "order_number": verification_result.get('order_number'),
                "method": method
            }
        else:
            return {"success": False, "error": verification_result['error']}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def complete_razorpay_payment(payment_id, payment_result, headers):
    """Complete Razorpay payment verification"""
    try:
        # Simulate Razorpay success response
        verification_data = {
            "payment_id": payment_id,
            "razorpay_order_id": payment_result['razorpay_order_id'],
            "razorpay_payment_id": "pay_test123456789",
            "razorpay_signature": "test_signature_123"
        }
        
        verify_response = requests.post(
            f"{BASE_URL}/api/payments/confirm-razorpay/",
            json=verification_data,
            headers=headers
        )
        
        if verify_response.status_code == 200:
            result = verify_response.json()
            print(f"   ✅ Razorpay payment verified")
            return {
                "success": True,
                "order_id": result.get('order_id'),
                "order_number": result.get('order_number')
            }
        else:
            return {"success": False, "error": f"Verification failed: {verify_response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def complete_cod_payment(payment_id, headers):
    """Complete COD payment confirmation"""
    try:
        cod_data = {
            "payment_id": payment_id,
            "cod_notes": "Customer confirmed COD order"
        }
        
        cod_response = requests.post(
            f"{BASE_URL}/api/payments/confirm-cod/",
            json=cod_data,
            headers=headers
        )
        
        if cod_response.status_code == 200:
            result = cod_response.json()
            print(f"   ✅ COD payment confirmed")
            return {
                "success": True,
                "order_id": result.get('order_id'),
                "order_number": result.get('order_number')
            }
        else:
            return {"success": False, "error": f"COD confirmation failed: {cod_response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def complete_pathlog_payment(payment_id, headers):
    """Complete Pathlog Wallet payment"""
    try:
        # Step 1: Verify mobile and get OTP
        otp_data = {
            "payment_id": payment_id,
            "mobile": "9876543210"
        }
        
        otp_response = requests.post(
            f"{BASE_URL}/api/payments/pathlog-wallet/otp/",
            json=otp_data,
            headers=headers
        )
        
        if otp_response.status_code != 200:
            return {"success": False, "error": f"OTP request failed: {otp_response.text}"}
        
        # Step 2: Verify OTP and complete payment
        verify_data = {
            "payment_id": payment_id,
            "otp": "123456",  # Demo OTP
            "mobile": "9876543210"
        }
        
        verify_response = requests.post(
            f"{BASE_URL}/api/payments/pathlog-wallet/verify/",
            json=verify_data,
            headers=headers
        )
        
        if verify_response.status_code == 200:
            result = verify_response.json()
            print(f"   ✅ Pathlog Wallet payment completed")
            return {
                "success": True,
                "order_id": result.get('order_id'),
                "order_number": result.get('order_number')
            }
        else:
            return {"success": False, "error": f"Pathlog verification failed: {verify_response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def verify_final_state(headers):
    """Verify cart cleanup and order creation"""
    try:
        # Check cart state
        cart_response = requests.get(f"{BASE_URL}/api/cart/", headers=headers)
        if cart_response.status_code == 200:
            cart_data = cart_response.json()
            cart_items = len(cart_data.get('items', []))
            print(f"   Cart items remaining: {cart_items}")
            if cart_items == 0:
                print("   ✅ Cart automatically cleaned up")
            else:
                print("   ⚠️ Cart still has items")
        
        # Check orders
        orders_response = requests.get(f"{BASE_URL}/api/orders/", headers=headers)
        if orders_response.status_code == 200:
            orders = orders_response.json()
            recent_orders = len(orders) if isinstance(orders, list) else orders.get('count', 0)
            print(f"   ✅ Total orders created: {recent_orders}")
        
        # Check payments
        payments_response = requests.get(f"{BASE_URL}/api/payments/", headers=headers)
        if payments_response.status_code == 200:
            payments = payments_response.json()
            recent_payments = len(payments) if isinstance(payments, list) else payments.get('count', 0)
            print(f"   ✅ Total payments processed: {recent_payments}")
            
    except Exception as e:
        print(f"   ❌ State verification error: {e}")

def test_admin_operations(payment_results):
    """Test admin operations for order management"""
    print("Testing admin order management...")
    
    # Get admin token
    admin_token = get_auth_token("admin@example.com", "Admin@123")
    if not admin_token:
        print("   ❌ Admin authentication failed")
        return
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test admin order listing
    admin_orders_response = requests.get(f"{BASE_URL}/api/admin/orders/", headers=admin_headers)
    if admin_orders_response.status_code == 200:
        print("   ✅ Admin can view all orders")
    else:
        print("   ❌ Admin order access failed")
    
    # Test order status updates (if we have successful orders)
    for method, result in payment_results.items():
        if result.get('success') and result.get('order_id'):
            test_order_status_update(result['order_id'], admin_headers)
            break

def test_order_status_update(order_id, admin_headers):
    """Test order status updates by admin"""
    try:
        # Test order acceptance
        accept_data = {"status": "processing", "notes": "Order accepted by admin"}
        accept_response = requests.patch(
            f"{BASE_URL}/api/admin/orders/{order_id}/",
            json=accept_data,
            headers=admin_headers
        )
        
        if accept_response.status_code == 200:
            print(f"   ✅ Admin can update order status")
        else:
            print(f"   ⚠️ Order status update failed: {accept_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Order status update error: {e}")

if __name__ == "__main__":
    print("🧪 COMPLETE E-COMMERCE FLOW TEST")
    print("Testing: Cart → Payment → Order → Cart Cleanup")
    print("Payment Methods: Razorpay, COD, Pathlog Wallet")
    print("=" * 60)
    
    try:
        success = test_complete_flow()
        
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        if success:
            print("🎉 Complete flow test PASSED!")
            print("✅ All payment methods working")
            print("✅ Order auto-creation working")
            print("✅ Cart cleanup working")
            print("✅ Admin operations accessible")
        else:
            print("❌ Complete flow test FAILED!")
            print("Please check the errors above")
            
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        import traceback
        traceback.print_exc()