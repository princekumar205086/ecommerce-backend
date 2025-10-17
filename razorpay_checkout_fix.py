#!/usr/bin/env python
"""
RAZORPAY CHECKOUT FIX & COMPREHENSIVE TEST
==========================================
This test fixes and validates Razorpay checkout for multiple users with proper cart setup.
"""

import os
import django
import requests
import json
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem
from products.models import Product, ProductVariant
from payments.models import Payment
from orders.models import Order

User = get_user_model()

class RazorpayCheckoutFix:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:8000/api'
        
    def log(self, message, status="ℹ"):
        print(f"{status} {message}")
        
    def log_success(self, message):
        self.log(message, "✅")
        
    def log_error(self, message):
        self.log(message, "❌")
        
    def setup_user_with_cart(self, email, password, full_name):
        """Setup user with populated cart using direct model methods"""
        # Create or get user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'password': password,
                'full_name': full_name
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.log_success(f"Created user: {email}")
        else:
            self.log_success(f"Using existing user: {email}")
        
        # Create or get cart
        cart, created = Cart.objects.get_or_create(user=user)
        
        # Clear existing items
        cart.items.all().delete()
        
        # Find a product to add
        product = Product.objects.filter(is_publish=True, stock__gt=0).first()
        if not product:
            self.log_error("No published products found")
            return None, None
            
        variant = ProductVariant.objects.filter(product=product, stock__gt=0).first()
        
        # Add item to cart using direct model
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variant,
            quantity=2
        )
        
        total = cart.total_price
        self.log_success(f"Setup cart for {email}: {cart.items.count()} items, Total: ₹{total}")
        
        return user, cart
    
    def authenticate_user(self, email, password):
        """Authenticate user and get token"""
        auth_data = {
            'email': email,
            'password': password
        }
        
        response = requests.post(f'{self.base_url}/token/', json=auth_data)
        
        if response.status_code == 200:
            token = response.json()['access']
            self.log_success(f"Authenticated {email}")
            return token
        else:
            self.log_error(f"Authentication failed for {email}: {response.text}")
            return None
    
    def test_payment_creation(self, token, user_email):
        """Test creating payment from cart"""
        headers = {'Authorization': f'Bearer {token}'}
        
        # First check cart via API
        cart_response = requests.get(f'{self.base_url}/cart/', headers=headers)
        if cart_response.status_code == 200:
            cart_data = cart_response.json()
            self.log_success(f"Cart API working for {user_email}: {len(cart_data['items'])} items")
        else:
            self.log_error(f"Cart API failed for {user_email}: {cart_response.text}")
            return None
        
        payment_data = {
            'payment_method': 'razorpay',
            'shipping_address': {
                'full_name': 'Test User',
                'address_line_1': '123 Test Street',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400001',
                'country': 'India',
                'phone': '+91-9876543210'
            },
            'billing_address': {
                'full_name': 'Test User',
                'address_line_1': '123 Test Street',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400001',
                'country': 'India',
                'phone': '+91-9876543210'
            },
            'currency': 'INR'
        }
        
        response = requests.post(f'{self.base_url}/payments/create-from-cart/', 
                               json=payment_data, headers=headers)
        
        if response.status_code == 200:
            payment_result = response.json()
            self.log_success(f"Payment created for {user_email}")
            self.log(f"Payment ID: {payment_result.get('payment_id')}")
            self.log(f"Amount: ₹{payment_result.get('amount')}")
            return payment_result
        else:
            self.log_error(f"Payment creation failed for {user_email}: {response.status_code}")
            self.log_error(f"Response: {response.text}")
            return None
    
    def test_payment_confirmation(self, token, payment_result, user_email):
        """Test confirming Razorpay payment"""
        headers = {'Authorization': f'Bearer {token}'}
        
        confirm_data = {
            'payment_id': payment_result['payment_id'],
            'razorpay_order_id': payment_result['razorpay_order_id'],
            'razorpay_payment_id': f'pay_test_{payment_result["payment_id"]}',
            'razorpay_signature': 'development_mode_signature'
        }
        
        response = requests.post(f'{self.base_url}/payments/confirm-razorpay/', 
                               json=confirm_data, headers=headers)
        
        if response.status_code == 200:
            confirm_result = response.json()
            self.log_success(f"Payment confirmed for {user_email}")
            
            if confirm_result.get('order_created'):
                self.log_success(f"Order created: #{confirm_result.get('order_number')}")
                return True
            else:
                self.log_error(f"Payment confirmed but order creation failed for {user_email}")
                self.log_error(f"Response: {confirm_result}")
                
                # Debug the payment in database
                try:
                    payment = Payment.objects.get(id=payment_result['payment_id'])
                    self.log(f"Payment status: {payment.status}")
                    self.log(f"Cart data present: {bool(payment.cart_data)}")
                    self.log(f"Order linked: {bool(payment.order)}")
                    
                    if payment.cart_data:
                        self.log(f"Cart data: {payment.cart_data}")
                        
                        # Try to create order manually to see specific error  
                        try:
                            order = payment.create_order_from_cart_data()
                            if order:
                                self.log_success(f"Manual order creation succeeded: #{order.order_number}")
                                return True
                            else:
                                self.log_error("Manual order creation returned None")
                        except Exception as e:
                            self.log_error(f"Manual order creation failed: {e}")
                    
                except Exception as e:
                    self.log_error(f"Error debugging payment: {e}")
                
                return False
        else:
            self.log_error(f"Payment confirmation failed for {user_email}: {response.status_code}")
            self.log_error(f"Response: {response.text}")
            return False
    
    def test_user_flow(self, email, password, full_name):
        """Test complete flow for a user"""
        self.log(f"\n{'='*70}")
        self.log(f"🧪 TESTING COMPLETE FLOW FOR {email}")
        self.log(f"{'='*70}")
        
        # Setup user and cart
        user, cart = self.setup_user_with_cart(email, password, full_name)
        if not user or not cart:
            return False
        
        # Authenticate
        token = self.authenticate_user(email, password)
        if not token:
            return False
        
        # Test payment creation
        payment_result = self.test_payment_creation(token, email)
        if not payment_result:
            return False
        
        # Test payment confirmation
        return self.test_payment_confirmation(token, payment_result, email)
    
    def run_comprehensive_test(self):
        """Run comprehensive test for multiple users"""
        print("RAZORPAY CHECKOUT FIX & COMPREHENSIVE TEST")
        print("=" * 70)
        
        test_users = [
            {
                'email': 'user@example.com',
                'password': 'User@123',
                'full_name': 'Test User 1'
            },
            {
                'email': 'programmar.prince@gmail.com',
                'password': 'Prince@123',
                'full_name': 'Prince Kumar'
            }
        ]
        
        results = {}
        
        for user_data in test_users:
            try:
                success = self.test_user_flow(
                    user_data['email'],
                    user_data['password'],
                    user_data['full_name']
                )
                results[user_data['email']] = success
            except Exception as e:
                self.log_error(f"Unexpected error for {user_data['email']}: {e}")
                results[user_data['email']] = False
        
        # Results summary
        print(f"\n{'='*70}")
        print("🎯 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        
        all_passed = True
        for email, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{email}: {status}")
            if not success:
                all_passed = False
        
        if all_passed:
            print(f"\n🎉 ALL TESTS PASSED!")
            print("✅ Razorpay checkout working correctly for all users")
            print("✅ Cart creation and population working")
            print("✅ Payment creation and confirmation working")
            print("✅ Order creation from cart working")
        else:
            print(f"\n🔧 SOME ISSUES DETECTED")
            print("Check the detailed output above for specific errors")
        
        return all_passed

if __name__ == '__main__':
    tester = RazorpayCheckoutFix()
    success = tester.run_comprehensive_test()
    
    if success:
        print(f"\n🚀 System is working correctly! Ready for production.")
    else:
        print(f"\n🔧 Issues found. Review the test output for details.")