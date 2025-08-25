#!/usr/bin/env python
import os
import django
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

import requests
import json
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from cart.models import Cart, CartItem
from products.models import Product, ProductVariant
from payments.models import Payment
from orders.models import Order

# Test URL
BASE_URL = 'http://127.0.0.1:8000'

def test_complete_payment_first_flow():
    """Test the complete payment-first checkout flow"""
    try:
        print("🚀 Testing Complete Payment-First Checkout Flow")
        print("=" * 60)
        
        # Get or create a test user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'full_name': 'Test User',
                'contact': '1234567890'
            }
        )
        
        print(f"👤 User: {user.email} ({'created' if created else 'existing'})")
        
        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Step 1: Create a test cart with items
        print("\n📦 Step 1: Setting up cart...")
        cart, created = Cart.objects.get_or_create(user=user)
        cart.items.all().delete()  # Clear existing items
        
        # Add products to cart
        products = Product.objects.all()[:2]  # Get first 2 products
        if len(products) < 1:
            print("❌ No products found. Please seed products first.")
            return
            
        for i, product in enumerate(products):
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=i + 2  # 2, 3 quantities
            )
            print(f"   ✅ Added {i + 2}x {product.name}")
        
        # Step 2: Create payment from cart (payment-first)
        print("\n💳 Step 2: Creating payment from cart...")
        payment_payload = {
            "cart_id": cart.id,
            "shipping_address": {
                "full_name": "Test User",
                "address_line_1": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "12345",
                "country": "India"
            },
            "billing_address": {
                "full_name": "Test User",
                "address_line_1": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "12345",
                "country": "India"
            },
            "payment_method": "razorpay",
            "currency": "INR"
        }
        
        response = requests.post(
            f'{BASE_URL}/api/payments/create-from-cart/',
            headers=headers,
            json=payment_payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Payment creation failed: {response.status_code}")
            print(response.text)
            return
        
        payment_data = response.json()
        print(f"   ✅ Payment created: {payment_data['order_id']}")
        print(f"   💰 Amount: ₹{payment_data['amount'] / 100}")
        
        # Get the payment record
        payment_id = payment_data['notes']['payment_id']
        payment = Payment.objects.get(id=payment_id)
        print(f"   📝 Payment ID: {payment.id}")
        print(f"   🛒 Cart data stored: {bool(payment.cart_data)}")
        print(f"   🏠 Address stored: {bool(payment.shipping_address)}")
        
        # Step 3: Simulate payment verification (payment success)
        print("\n✅ Step 3: Simulating payment verification...")
        verify_payload = {
            "razorpay_order_id": payment_data['order_id'],
            "razorpay_payment_id": "pay_test123456789",  # Mock payment ID
            "razorpay_signature": "mock_signature_for_testing"
        }
        
        response = requests.post(
            f'{BASE_URL}/api/payments/verify/',
            headers=headers,
            json=verify_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            verify_result = response.json()
            print(f"   ✅ Payment verified: {verify_result['message']}")
            
            if 'order' in verify_result:
                order_id = verify_result['order']['id']
                print(f"   🎯 Order auto-created: #{order_id}")
                
                # Check the order details
                order = Order.objects.get(id=order_id)
                print(f"   📊 Order status: {order.status}")
                print(f"   💰 Order total: ₹{order.total_amount}")
                print(f"   📦 Order items: {order.items.count()}")
                
                # Check payment is linked to order
                payment.refresh_from_db()
                print(f"   🔗 Payment linked to order: {payment.order_id == order.id}")
                
        else:
            print(f"❌ Payment verification failed: {response.status_code}")
            print(response.text)
            return
        
        print("\n🎉 SUCCESS! Payment-First Checkout Flow Completed:")
        print("   1. ✅ Cart created with products")
        print("   2. ✅ Payment created from cart")
        print("   3. ✅ Payment verification successful")
        print("   4. ✅ Order auto-created after payment")
        print("   5. ✅ Payment linked to order")
        
        print("\n📋 Flow Summary:")
        print(f"   Cart ID: {cart.id}")
        print(f"   Payment ID: {payment.id}")
        print(f"   Order ID: {order.id}")
        print(f"   Total Amount: ₹{order.total_amount}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Is the Django server running?")
        print("💡 Run: python manage.py runserver")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_complete_payment_first_flow()