#!/usr/bin/env python
"""
Test script to debug the specific payment verification issue
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from payments.models import Payment
from django.contrib.auth import get_user_model

User = get_user_model()

def test_specific_payment_verification():
    """Test the specific payment verification payload that's failing"""
    
    print("🔍 Testing specific payment verification issue...")
    
    # The payload that's causing issues
    test_payload = {
        "payment_id": 10,
        "razorpay_order_id": "order_R9gSddnOIooVyp",
        "razorpay_payment_id": "pay_R9gT23iSCCRqEc",
        "razorpay_signature": "87c69c4a6b995bd68f415b5ca8a45abd58e337f9ba6cf5c8b48685e425eea805"
    }
    
    print(f"Test payload: {json.dumps(test_payload, indent=2)}")
    
    # Check if payment exists
    try:
        payment = Payment.objects.get(id=test_payload['payment_id'])
        print(f"✅ Payment found: ID {payment.id}")
        print(f"   User: {payment.user.email}")
        print(f"   Status: {payment.status}")
        print(f"   Amount: {payment.amount}")
        print(f"   Razorpay Order ID: {payment.razorpay_order_id}")
        print(f"   Current Razorpay Payment ID: {payment.razorpay_payment_id}")
        
        # Check if the order ID matches
        if payment.razorpay_order_id == test_payload['razorpay_order_id']:
            print("✅ Order ID matches")
        else:
            print(f"❌ Order ID mismatch:")
            print(f"   Expected: {test_payload['razorpay_order_id']}")
            print(f"   Actual: {payment.razorpay_order_id}")
        
        # Test verification manually
        print("\n🔐 Testing manual signature verification...")
        
        # Update payment with the data first
        payment.razorpay_payment_id = test_payload['razorpay_payment_id']
        
        # Test verification
        verification_result = payment.verify_payment(test_payload['razorpay_signature'])
        print(f"Verification result: {verification_result}")
        
        if verification_result:
            print("✅ Signature verification successful!")
            
            # Save the payment
            payment.razorpay_signature = test_payload['razorpay_signature']
            payment.status = 'successful'
            payment.save()
            print("✅ Payment updated and saved")
            
            # Check if order creation is needed
            if payment.cart_data and not payment.order:
                print("📦 Creating order from cart data...")
                order = payment.create_order_from_cart_data()
                if order:
                    print(f"✅ Order created: #{order.order_number}")
                    print(f"   Order ID: {order.id}")
                    print(f"   Order Total: {order.total}")
                    
                    # Test cart cleanup
                    print("\n🛒 Testing cart cleanup...")
                    if hasattr(payment, 'cart_data') and payment.cart_data:
                        cart_id = payment.cart_data.get('cart_id')
                        if cart_id:
                            from cart.models import Cart
                            try:
                                cart = Cart.objects.get(id=cart_id, user=payment.user)
                                print(f"   Cart items before cleanup: {cart.items.count()}")
                                
                                # Clear cart items
                                cart.items.all().delete()
                                print("✅ Cart items cleared successfully")
                                
                                cart_items_after = cart.items.count()
                                print(f"   Cart items after cleanup: {cart_items_after}")
                                
                            except Cart.DoesNotExist:
                                print("❌ Cart not found for cleanup")
                else:
                    print("❌ Order creation failed")
            else:
                print("ℹ️ No order creation needed (already exists or no cart data)")
                
        else:
            print("❌ Signature verification failed!")
            print("   This might be due to:")
            print("   1. Incorrect API secret")
            print("   2. Signature mismatch")
            print("   3. Order ID mismatch")
            
            # Debug the verification parameters
            print(f"\n🔧 Debug info:")
            print(f"   razorpay_order_id: {payment.razorpay_order_id}")
            print(f"   razorpay_payment_id: {test_payload['razorpay_payment_id']}")
            print(f"   razorpay_signature: {test_payload['razorpay_signature']}")
            
    except Payment.DoesNotExist:
        print(f"❌ Payment with ID {test_payload['payment_id']} not found")
        return False
    
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_api_endpoint():
    """Test the actual API endpoint"""
    print("\n\n🌐 Testing API endpoint...")
    
    # Get auth token (you'll need to adjust this based on your user)
    users = User.objects.all()[:5]
    print("Available users:")
    for user in users:
        print(f"  - {user.email} (ID: {user.id})")
    
    # Try to find the user who owns payment ID 10
    try:
        payment = Payment.objects.get(id=10)
        user = payment.user
        print(f"\nPayment 10 belongs to: {user.email}")
        
        # Try to get auth token (this might not work in this script)
        # You'd need to manually get the token from the frontend
        print("⚠️ You'll need to test the API endpoint manually with proper auth token")
        print("Suggested curl command:")
        print(f"""
curl -X POST https://backend.okpuja.in/api/payments/confirm-razorpay/ \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -d '{{"payment_id": 10, "razorpay_order_id": "order_R9gSddnOIooVyp", "razorpay_payment_id": "pay_R9gT23iSCCRqEc", "razorpay_signature": "87c69c4a6b995bd68f415b5ca8a45abd58e337f9ba6cf5c8b48685e425eea805"}}'
        """)
        
    except Payment.DoesNotExist:
        print("❌ Payment ID 10 not found")

if __name__ == "__main__":
    print("🚀 Payment Verification Debug Script")
    print("=" * 50)
    
    # Test the specific verification
    result = test_specific_payment_verification()
    
    # Test API endpoint suggestions
    test_api_endpoint()
    
    print("\n" + "=" * 50)
    if result:
        print("✅ Debug testing completed")
    else:
        print("❌ Debug testing failed")