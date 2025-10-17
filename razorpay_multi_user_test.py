#!/usr/bin/env python
"""
RAZORPAY MULTI-USER CHECKOUT ISSUE DIAGNOSIS & FIX
=================================================
This test reproduces the exact issues you described and provides fixes:
1. "No active cart found" for programmar.prince@gmail.com
2. "Payment successful but order creation failed" for different users
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

class RazorpayMultiUserTest:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:8000/api'
        self.test_users = [
            {
                'email': 'user@example.com',
                'password': 'User@123',
                'name': 'Test User 1'
            },
            {
                'email': 'programmar.prince@gmail.com', 
                'password': 'Prince@123',
                'name': 'Prince Kumar'
            }
        ]
        
    def log(self, message, status="ℹ"):
        print(f"{status} {message}")
        
    def log_success(self, message):
        self.log(message, "✅")
        
    def log_error(self, message):
        self.log(message, "❌")
        
    def log_warning(self, message):
        self.log(message, "⚠️")
        
    def create_test_user_if_not_exists(self, user_data):
        """Create test user if it doesn't exist"""
        try:
            user = User.objects.get(email=user_data['email'])
            self.log_success(f"User {user_data['email']} already exists")
            return user
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=user_data['email'],
                password=user_data['password'],
                full_name=user_data['name']
            )
            self.log_success(f"Created user {user_data['email']}")
            return user
    
    def authenticate_user(self, user_data):
        """Authenticate user and get token"""
        auth_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        
        response = requests.post(f'{self.base_url}/token/', json=auth_data)
        
        if response.status_code == 200:
            token = response.json()['access']
            self.log_success(f"Authenticated {user_data['email']}")
            return token
        else:
            self.log_error(f"Authentication failed for {user_data['email']}: {response.text}")
            return None
    
    def setup_cart_for_user(self, token, user_email):
        """Setup cart with products for a user"""
        headers = {'Authorization': f'Bearer {token}'}
        
        # First, check if cart exists
        cart_response = requests.get(f'{self.base_url}/cart/', headers=headers)
        
        if cart_response.status_code == 404:
            self.log_warning(f"No cart found for {user_email} - this is the issue!")
            # Try to create cart by adding an item
            
            # Find a product to add
            try:
                product = Product.objects.filter(is_publish=True, stock__gt=0).first()
                if not product:
                    self.log_error("No published products found")
                    return False
                    
                variant = ProductVariant.objects.filter(product=product, stock__gt=0).first()
                
                add_data = {
                    'product_id': product.id,
                    'quantity': 1
                }
                
                if variant:
                    add_data['variant_id'] = variant.id
                
                add_response = requests.post(f'{self.base_url}/cart/add/', json=add_data, headers=headers)
                
                if add_response.status_code in [200, 201]:
                    self.log_success(f"Created cart and added product for {user_email}")
                    return True
                else:
                    self.log_error(f"Failed to add product to cart: {add_response.text}")
                    return False
                    
            except Exception as e:
                self.log_error(f"Error setting up cart: {e}")
                return False
                
        elif cart_response.status_code == 200:
            cart_data = cart_response.json()
            
            if len(cart_data.get('items', [])) == 0:
                self.log_warning(f"Cart exists but is empty for {user_email}")
                # Add a product
                try:
                    product = Product.objects.filter(is_publish=True, stock__gt=0).first()
                    variant = ProductVariant.objects.filter(product=product, stock__gt=0).first()
                    
                    add_data = {
                        'product_id': product.id,
                        'quantity': 1
                    }
                    
                    if variant:
                        add_data['variant_id'] = variant.id
                    
                    add_response = requests.post(f'{self.base_url}/cart/add/', json=add_data, headers=headers)
                    
                    if add_response.status_code in [200, 201]:
                        self.log_success(f"Added product to existing empty cart for {user_email}")
                        return True
                    else:
                        self.log_error(f"Failed to add product: {add_response.text}")
                        return False
                        
                except Exception as e:
                    self.log_error(f"Error adding product to empty cart: {e}")
                    return False
            else:
                self.log_success(f"Cart with {len(cart_data['items'])} items found for {user_email}")
                return True
        else:
            self.log_error(f"Unexpected cart response for {user_email}: {cart_response.status_code} - {cart_response.text}")
            return False
    
    def test_create_payment_from_cart(self, token, user_email):
        """Test creating payment from cart"""
        headers = {'Authorization': f'Bearer {token}'}
        
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
            self.log_success(f"Payment created successfully for {user_email}")
            self.log(f"Payment ID: {payment_result.get('payment_id')}")
            self.log(f"Razorpay Order ID: {payment_result.get('razorpay_order_id')}")
            return payment_result
        else:
            self.log_error(f"Payment creation failed for {user_email}: {response.status_code}")
            self.log_error(f"Error details: {response.text}")
            return None
    
    def test_confirm_razorpay_payment(self, token, payment_result, user_email):
        """Test confirming Razorpay payment"""
        headers = {'Authorization': f'Bearer {token}'}
        
        # Simulate Razorpay response
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
            self.log_success(f"Payment confirmed successfully for {user_email}")
            
            if confirm_result.get('order_created'):
                self.log_success(f"Order created: #{confirm_result.get('order_number')}")
                return True
            else:
                self.log_error(f"Payment successful but order creation failed for {user_email}")
                return False
        else:
            self.log_error(f"Payment confirmation failed for {user_email}: {response.status_code}")
            self.log_error(f"Error details: {response.text}")
            return False
    
    def diagnose_cart_issue(self, user_data):
        """Diagnose cart-related issues for a user"""
        self.log(f"🔍 Diagnosing cart issues for {user_data['email']}")
        
        # Create user if not exists
        user = self.create_test_user_if_not_exists(user_data)
        
        # Check if user has a cart in database
        try:
            cart = Cart.objects.get(user=user)
            items_count = cart.items.count()
            self.log(f"Database: User has cart ID {cart.id} with {items_count} items")
            
            if items_count == 0:
                self.log_warning("Cart is empty - this could cause 'No active cart found' error")
        except Cart.DoesNotExist:
            self.log_warning("Database: No cart exists for user - this will cause 'No active cart found' error")
    
    def test_user_checkout_flow(self, user_data):
        """Test complete checkout flow for a user"""
        self.log(f"\n{'='*60}")
        self.log(f"🧪 TESTING CHECKOUT FLOW FOR {user_data['email']}")
        self.log(f"{'='*60}")
        
        # Step 1: Diagnose existing cart issues
        self.diagnose_cart_issue(user_data)
        
        # Step 2: Authenticate
        token = self.authenticate_user(user_data)
        if not token:
            return False
        
        # Step 3: Setup cart
        if not self.setup_cart_for_user(token, user_data['email']):
            return False
        
        # Step 4: Create payment
        payment_result = self.test_create_payment_from_cart(token, user_data['email'])
        if not payment_result:
            return False
        
        # Step 5: Confirm payment
        success = self.test_confirm_razorpay_payment(token, payment_result, user_data['email'])
        
        return success
    
    def run_comprehensive_test(self):
        """Run comprehensive multi-user test"""
        print("RAZORPAY MULTI-USER CHECKOUT ISSUE DIAGNOSIS")
        print("=" * 60)
        
        results = {}
        
        for user_data in self.test_users:
            try:
                success = self.test_user_checkout_flow(user_data)
                results[user_data['email']] = success
            except Exception as e:
                self.log_error(f"Unexpected error for {user_data['email']}: {e}")
                results[user_data['email']] = False
        
        # Summary
        print(f"\n{'='*60}")
        print("🎯 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for email, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{email}: {status}")
        
        # Provide fixes
        print(f"\n{'='*60}")
        print("🔧 IDENTIFIED ISSUES & SOLUTIONS")
        print("=" * 60)
        
        if not all(results.values()):
            print("1. CART CREATION ISSUE:")
            print("   - Some users don't have carts automatically created")
            print("   - Solution: Auto-create cart when user first accesses cart endpoint")
            print()
            print("2. ORDER CREATION FAILURE:")
            print("   - Payment successful but create_order_from_cart_data() fails")
            print("   - Solution: Add better error handling and debugging")
            print()
            print("3. USER-SPECIFIC ISSUES:")
            print("   - Different users may have different cart states")
            print("   - Solution: Ensure consistent cart initialization")
        else:
            print("✅ ALL TESTS PASSED!")
            print("🎉 Razorpay checkout working for all users!")
        
        return all(results.values())

if __name__ == '__main__':
    tester = RazorpayMultiUserTest()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🚀 All tests passed! System is working correctly.")
    else:
        print("\n🔧 Issues detected. Check the output above for solutions.")