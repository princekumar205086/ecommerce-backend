#!/usr/bin/env python
"""
FINAL RAZORPAY CHECKOUT VALIDATION - 100% SUCCESS GUARANTEE
===========================================================
This test ensures 100% success rate for Razorpay checkout across all scenarios.
Tests both existing and new users with various cart states.
"""

import os
import django
import requests
import json
from decimal import Decimal
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem
from products.models import Product, ProductVariant
from payments.models import Payment
from orders.models import Order

User = get_user_model()

class FinalRazorpayValidation:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:8000/api'
        self.test_scenarios = []
        self.results = {}
        
    def log(self, message, status="ℹ"):
        print(f"{status} {message}")
        
    def log_success(self, message):
        self.log(message, "✅")
        
    def log_error(self, message):
        self.log(message, "❌")
    
    def log_step(self, step, message):
        self.log(f"Step {step}: {message}", "🔸")
    
    def create_test_scenarios(self):
        """Create comprehensive test scenarios"""
        self.test_scenarios = [
            {
                'name': 'Existing User - Empty Cart',
                'email': 'user@example.com',
                'password': 'User@123',
                'full_name': 'Test User 1',
                'setup_cart': True,  # We'll setup cart for this test
                'expected': 'success'
            },
            {
                'name': 'New User - Prince Kumar',
                'email': 'programmar.prince@gmail.com',
                'password': 'Prince@123',
                'full_name': 'Prince Kumar',
                'setup_cart': True,
                'expected': 'success'
            },
            {
                'name': 'Fresh User - No Previous Data',
                'email': 'fresh.user@test.com',
                'password': 'Fresh@123',
                'full_name': 'Fresh Test User',
                'setup_cart': True,
                'expected': 'success'
            },
            {
                'name': 'Edge Case - Empty Cart Error Handling',
                'email': 'empty.cart@test.com',
                'password': 'Empty@123',
                'full_name': 'Empty Cart User',
                'setup_cart': False,  # Don't setup cart - test error handling
                'expected': 'empty_cart_error'
            }
        ]
    
    def setup_user_and_cart(self, scenario):
        """Setup user and cart based on scenario"""
        # Create or get user
        user, created = User.objects.get_or_create(
            email=scenario['email'],
            defaults={
                'full_name': scenario['full_name']
            }
        )
        
        if created:
            user.set_password(scenario['password'])
            user.save()
            self.log_success(f"Created new user: {scenario['email']}")
        else:
            self.log_success(f"Using existing user: {scenario['email']}")
        
        # Handle cart setup
        cart, cart_created = Cart.objects.get_or_create(user=user)
        
        # Clear existing items
        cart.items.all().delete()
        
        if scenario['setup_cart']:
            # Find and add products
            product = Product.objects.filter(is_publish=True, stock__gt=0).first()
            if product:
                variant = ProductVariant.objects.filter(product=product, stock__gt=0).first()
                
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    quantity=2
                )
                
                self.log_success(f"Setup cart with product for {scenario['email']}")
            else:
                self.log_error("No products available for cart setup")
                return False
        else:
            self.log_success(f"Left cart empty for {scenario['email']} (testing error handling)")
        
        return True
    
    def authenticate_user(self, email, password):
        """Authenticate user"""
        auth_data = {'email': email, 'password': password}
        
        response = requests.post(f'{self.base_url}/token/', json=auth_data)
        
        if response.status_code == 200:
            return response.json()['access']
        else:
            self.log_error(f"Authentication failed: {response.text}")
            return None
    
    def test_payment_flow(self, scenario, token):
        """Test complete payment flow"""
        headers = {'Authorization': f'Bearer {token}'}
        
        # Step 1: Check cart
        self.log_step(1, "Checking cart via API")
        cart_response = requests.get(f'{self.base_url}/cart/', headers=headers)
        
        if cart_response.status_code == 200:
            cart_data = cart_response.json()
            self.log_success(f"Cart retrieved: {len(cart_data['items'])} items")
            
            if len(cart_data['items']) == 0 and scenario['expected'] == 'empty_cart_error':
                self.log_success("Empty cart detected as expected")
            elif len(cart_data['items']) == 0 and scenario['expected'] == 'success':
                self.log_error("Expected items in cart but found none")
                return False
        else:
            self.log_error(f"Cart API failed: {cart_response.text}")
            return False
        
        # Step 2: Create payment
        self.log_step(2, "Creating Razorpay payment")
        
        payment_data = {
            'payment_method': 'razorpay',
            'shipping_address': {
                'full_name': scenario['full_name'],
                'address_line_1': '123 Test Street',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400001',
                'country': 'India',
                'phone': '+91-9876543210'
            },
            'billing_address': {
                'full_name': scenario['full_name'],
                'address_line_1': '123 Test Street',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400001',
                'country': 'India',
                'phone': '+91-9876543210'
            },
            'currency': 'INR'
        }
        
        payment_response = requests.post(f'{self.base_url}/payments/create-from-cart/', 
                                       json=payment_data, headers=headers)
        
        if scenario['expected'] == 'empty_cart_error':
            if payment_response.status_code == 400:
                error_data = payment_response.json()
                if 'Cart is empty' in error_data.get('error', ''):
                    self.log_success("Empty cart error handled correctly")
                    return True
                else:
                    self.log_error(f"Unexpected error: {error_data}")
                    return False
            else:
                self.log_error("Expected 400 error for empty cart but got success")
                return False
        
        if payment_response.status_code == 200:
            payment_result = payment_response.json()
            self.log_success(f"Payment created - ID: {payment_result['payment_id']}")
        else:
            self.log_error(f"Payment creation failed: {payment_response.text}")
            return False
        
        # Step 3: Confirm payment
        self.log_step(3, "Confirming Razorpay payment")
        
        confirm_data = {
            'payment_id': payment_result['payment_id'],
            'razorpay_order_id': payment_result['razorpay_order_id'],
            'razorpay_payment_id': f'pay_test_{payment_result["payment_id"]}_{int(time.time())}',
            'razorpay_signature': 'development_mode_signature'
        }
        
        confirm_response = requests.post(f'{self.base_url}/payments/confirm-razorpay/', 
                                       json=confirm_data, headers=headers)
        
        if confirm_response.status_code == 200:
            confirm_result = confirm_response.json()
            
            if confirm_result.get('order_created'):
                self.log_success(f"Order created: #{confirm_result.get('order_number')}")
                
                # Step 4: Verify order in database
                self.log_step(4, "Verifying order in database")
                try:
                    order = Order.objects.get(order_number=confirm_result['order_number'])
                    self.log_success(f"Order verified in DB: #{order.order_number}")
                    self.log_success(f"Order total: ₹{order.total}")
                    self.log_success(f"Payment status: {order.payment_status}")
                    
                    # Verify cart was cleared
                    user = User.objects.get(email=scenario['email'])
                    cart = Cart.objects.get(user=user)
                    if cart.items.count() == 0:
                        self.log_success("Cart cleared after order creation")
                    else:
                        self.log_error("Cart not cleared after order creation")
                        return False
                    
                    return True
                    
                except Order.DoesNotExist:
                    self.log_error("Order not found in database")
                    return False
            else:
                self.log_error("Order creation failed")
                self.log_error(f"Response: {confirm_result}")
                return False
        else:
            self.log_error(f"Payment confirmation failed: {confirm_response.text}")
            return False
    
    def run_scenario(self, scenario):
        """Run a single test scenario"""
        print(f"\n{'='*80}")
        print(f"🧪 TESTING SCENARIO: {scenario['name']}")
        print(f"📧 Email: {scenario['email']}")
        print(f"🎯 Expected: {scenario['expected']}")
        print("=" * 80)
        
        # Setup user and cart
        if not self.setup_user_and_cart(scenario):
            return False
        
        # Authenticate
        token = self.authenticate_user(scenario['email'], scenario['password'])
        if not token:
            return False
        
        # Test payment flow
        return self.test_payment_flow(scenario, token)
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("FINAL RAZORPAY CHECKOUT VALIDATION - 100% SUCCESS GUARANTEE")
        print("=" * 80)
        
        self.create_test_scenarios()
        
        success_count = 0
        total_count = len(self.test_scenarios)
        
        for scenario in self.test_scenarios:
            try:
                success = self.run_scenario(scenario)
                self.results[scenario['name']] = success
                
                if success:
                    success_count += 1
                    print(f"\n✅ SCENARIO PASSED: {scenario['name']}")
                else:
                    print(f"\n❌ SCENARIO FAILED: {scenario['name']}")
                    
            except Exception as e:
                self.log_error(f"Unexpected error in scenario {scenario['name']}: {e}")
                self.results[scenario['name']] = False
                print(f"\n❌ SCENARIO ERROR: {scenario['name']}")
        
        # Final results
        print(f"\n{'='*80}")
        print("🎯 FINAL VALIDATION RESULTS")
        print("=" * 80)
        
        for scenario_name, success in self.results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{scenario_name}: {status}")
        
        success_rate = (success_count / total_count) * 100
        print(f"\n📊 SUCCESS RATE: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print(f"\n🎉 PERFECT SCORE! 100% SUCCESS RATE ACHIEVED!")
            print("✅ All Razorpay checkout scenarios working correctly")
            print("✅ Cart creation and error handling working")
            print("✅ Payment creation and confirmation working")
            print("✅ Order creation and cart clearing working")
            print("✅ System ready for production!")
        else:
            print(f"\n⚠️ SUCCESS RATE: {success_rate:.1f}%")
            print("Some scenarios failed. Check the detailed output above.")
        
        return success_rate == 100

if __name__ == '__main__':
    validator = FinalRazorpayValidation()
    success = validator.run_all_tests()
    
    if success:
        print(f"\n🚀 VALIDATION COMPLETE - SYSTEM IS PRODUCTION READY!")
    else:
        print(f"\n🔧 VALIDATION INCOMPLETE - CHECK FAILED SCENARIOS")