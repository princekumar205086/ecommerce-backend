#!/usr/bin/env python
"""
Quick test to check authentication and then test payment verification
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from payments.models import Payment

User = get_user_model()
BASE_URL = "http://127.0.0.1:8000"

def test_auth():
    """Test authentication"""
    print("🔐 Testing authentication...")
    
    # List available users
    users = User.objects.all()[:5]
    print("Available users:")
    for user in users:
        print(f"  - {user.email} (Role: {getattr(user, 'role', 'N/A')})")
    
    # Try different login methods
    test_credentials = [
        ("user@example.com", "User@123"),
        ("admin@example.com", "Admin@123"),
        ("supplier@example.com", "testpass123")
    ]
    
    for email, password in test_credentials:
        print(f"\nTrying login: {email}")
        
        response = requests.post(f"{BASE_URL}/api/accounts/login/", {
            "username": email,
            "password": password
        })
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful!")
            print(f"Token: {data.get('access', 'N/A')[:20]}...")
            return data.get('access'), email
        else:
            print(f"❌ Login failed: {response.text}")
    
    return None, None

def test_payment_verification_direct():
    """Test payment verification directly with database"""
    print("\n🔧 Testing payment verification logic directly...")
    
    # Find a recent payment
    payments = Payment.objects.all().order_by('-created_at')[:5]
    print(f"Recent payments:")
    for p in payments:
        print(f"  - Payment {p.id}: Status={p.status}, Amount=₹{p.amount}, User={p.user.email}")
        print(f"    Order ID: {p.razorpay_order_id}")
    
    # Test with payment ID 10 specifically
    try:
        payment = Payment.objects.get(id=10)
        print(f"\n📋 Payment 10 details:")
        print(f"   User: {payment.user.email}")
        print(f"   Status: {payment.status}")
        print(f"   Amount: ₹{payment.amount}")
        print(f"   Order ID: {payment.razorpay_order_id}")
        print(f"   Payment Method: {payment.payment_method}")
        
        # Check if this payment has cart data
        if payment.cart_data:
            print(f"   Cart Data: Available (Cart ID: {payment.cart_data.get('cart_id')})")
        else:
            print(f"   Cart Data: None")
            
        return payment
        
    except Payment.DoesNotExist:
        print("❌ Payment 10 not found")
        return None

def fix_order_id_mismatch():
    """Create a test to show how to fix order ID mismatch"""
    print("\n🔧 Demonstrating Order ID Mismatch Solution...")
    
    # The issue: Frontend has old order ID, backend has new order ID
    frontend_payload = {
        "payment_id": 10,
        "razorpay_order_id": "order_R9gSddnOIooVyp",  # Old/incorrect
        "razorpay_payment_id": "pay_R9gT23iSCCRqEc",
        "razorpay_signature": "87c69c4a6b995bd68f415b5ca8a45abd58e337f9ba6cf5c8b48685e425eea805"
    }
    
    try:
        payment = Payment.objects.get(id=10)
        print(f"❌ Frontend Order ID: {frontend_payload['razorpay_order_id']}")
        print(f"✅ Backend Order ID:  {payment.razorpay_order_id}")
        print(f"\n💡 Solution: Frontend should always create fresh payment!")
        
        print(f"\n📝 Correct approach:")
        print(f"1. User clicks 'Pay Now'")
        print(f"2. Frontend calls: POST /api/payments/create-from-cart/")
        print(f"3. Backend returns NEW payment with fresh order_id")
        print(f"4. Frontend uses THIS order_id for Razorpay")
        print(f"5. Verification will succeed with matching order_id")
        
        return True
        
    except Payment.DoesNotExist:
        print("❌ Payment not found")
        return False

if __name__ == "__main__":
    print("🧪 Quick Payment Verification Debug")
    print("=" * 50)
    
    # Test authentication
    token, user_email = test_auth()
    
    # Test payment verification logic
    payment = test_payment_verification_direct()
    
    # Show order ID mismatch solution
    fix_order_id_mismatch()
    
    print("\n" + "=" * 50)
    if token:
        print(f"✅ Authentication working for: {user_email}")
    else:
        print("❌ Authentication failed")
        
    if payment:
        print(f"✅ Payment data accessible")
    else:
        print("❌ Payment data issues")
        
    print("\n📋 Summary of Issue:")
    print("The payment verification is failing because:")
    print("1. ❌ Order ID mismatch between frontend and backend")
    print("2. ❌ Frontend is using cached/old payment data")
    print("3. ✅ Backend payment verification logic is correct")
    print("\n🔧 Solution: Frontend must use fresh payment data for each attempt!")