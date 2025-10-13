#!/usr/bin/env python
"""
API CART CLEARING TEST FOR PATHLOG WALLET
=========================================
This test validates cart clearing through API endpoints to match real frontend usage.
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart
from products.models import Product, ProductVariant

User = get_user_model()

class APICartClearingTest:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:8000/api'
        self.token = None
        self.cart_id = None
        self.payment_id = None
        
    def log(self, message, status="ℹ"):
        print(f"{status} {message}")
        
    def log_success(self, message):
        self.log(message, "✓")
        
    def log_error(self, message):
        self.log(message, "✗")
    
    def authenticate(self):
        """Authenticate and get JWT token"""
        self.log("Step 1: Authentication")
        
        auth_data = {
            'email': 'user@example.com',
            'password': 'User@123'
        }
        
        response = requests.post(f'{self.base_url}/token/', json=auth_data)
        
        if response.status_code == 200:
            self.token = response.json()['access']
            self.log_success("Authentication successful")
            return True
        else:
            self.log_error(f"Authentication failed: {response.text}")
            return False
    
    def setup_cart_via_api(self):
        """Setup cart using API endpoints"""
        self.log("Step 2: Setting up cart via API")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Get cart
        response = requests.get(f'{self.base_url}/cart/', headers=headers)
        if response.status_code != 200:
            self.log_error(f"Failed to get cart: {response.text}")
            return False
            
        cart_data = response.json()
        self.cart_id = cart_data['id']
        
        # Clear existing cart
        requests.delete(f'{self.base_url}/cart/clear/', headers=headers)
        
        # Add product via API
        try:
            product = Product.objects.filter(is_publish=True, stock__gt=0).first()
            variant = ProductVariant.objects.filter(product=product, stock__gt=0).first()
            
            add_data = {
                'product_id': product.id,
                'variant_id': variant.id,
                'quantity': 2
            }
            
            response = requests.post(f'{self.base_url}/cart/add/', json=add_data, headers=headers)
            
            if response.status_code in [200, 201]:
                # Get updated cart
                response = requests.get(f'{self.base_url}/cart/', headers=headers)
                if response.status_code == 200:
                    cart_data = response.json()
                    self.log_success(f"Cart setup via API - {len(cart_data['items'])} items, Total: ₹{cart_data['total_price']}")
                    return True
            
            self.log_error(f"Failed to add to cart via API: {response.text}")
            return False
            
        except Exception as e:
            self.log_error(f"Cart setup error: {e}")
            return False
    
    def check_cart_items_count(self, step_name):
        """Check current cart items count"""
        headers = {'Authorization': f'Bearer {self.token}'}
        
        response = requests.get(f'{self.base_url}/cart/', headers=headers)
        if response.status_code == 200:
            cart_data = response.json()
            items_count = len(cart_data['items'])
            total = cart_data['total_price']
            self.log(f"{step_name}: Cart has {items_count} items, Total: ₹{total}")
            return items_count
        else:
            self.log_error(f"Failed to get cart: {response.text}")
            return -1
    
    def simulate_pathlog_checkout_api(self):
        """Simulate Pathlog checkout using API (if endpoints exist)"""
        self.log("Step 3: Simulating Pathlog checkout")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Get current cart data
        response = requests.get(f'{self.base_url}/cart/', headers=headers)
        if response.status_code != 200:
            self.log_error("Failed to get cart data")
            return False
            
        cart_data = response.json()
        
        # Check items before checkout
        items_before = self.check_cart_items_count("Before checkout")
        
        # Try to create Pathlog payment via API
        payment_data = {
            'amount': float(cart_data['total_price']),
            'currency': 'INR',
            'payment_method': 'pathlog_wallet',
            'cart_data': {
                'cart_id': cart_data['id'],
                'total_price': cart_data['total_price'],
                'items': cart_data['items']
            },
            'shipping_address': {
                'name': 'Test User',
                'phone': '9876543210',
                'address': '123 Test Street',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456'
            },
            'billing_address': {
                'name': 'Test User',
                'phone': '9876543210',
                'address': '123 Test Street',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456'
            }
        }
        
        # Try payment creation endpoint
        response = requests.post(f'{self.base_url}/payments/create/', json=payment_data, headers=headers)
        
        if response.status_code in [200, 201]:
            payment_response = response.json()
            self.payment_id = payment_response.get('payment_id')
            self.log_success(f"Payment created via API: ID {self.payment_id}")
            
            # Check cart after payment creation (should still have items)
            items_after_payment_creation = self.check_cart_items_count("After payment creation")
            
            # Try to process payment (simulate wallet verification and processing)
            # Note: These endpoints may not exist, so we'll use direct model methods as fallback
            try:
                # Simulate wallet verification and processing using model methods
                from payments.models import Payment
                payment = Payment.objects.get(id=self.payment_id)
                
                # Verify wallet
                success, message = payment.verify_pathlog_wallet('9876543210', '123456')
                if success:
                    self.log_success("Wallet verified")
                    
                    # Process payment
                    success, message = payment.process_pathlog_wallet_payment()
                    if success:
                        self.log_success(f"Payment processed: {message}")
                        
                        # Check cart after payment processing (should be cleared)
                        items_after_processing = self.check_cart_items_count("After payment processing")
                        
                        return {
                            'before': items_before,
                            'after_creation': items_after_payment_creation,
                            'after_processing': items_after_processing,
                            'order_created': payment.order is not None
                        }
                    else:
                        self.log_error(f"Payment processing failed: {message}")
                        return None
                else:
                    self.log_error(f"Wallet verification failed: {message}")
                    return None
                    
            except Exception as e:
                self.log_error(f"Payment processing error: {e}")
                return None
                
        else:
            self.log_error(f"Payment creation failed: {response.text}")
            return None
    
    def run_test(self):
        """Run the complete API cart clearing test"""
        print("API CART CLEARING TEST FOR PATHLOG WALLET")
        print("=" * 55)
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            return False
        
        # Step 2: Setup cart via API
        if not self.setup_cart_via_api():
            return False
        
        # Step 3: Pathlog checkout simulation
        result = self.simulate_pathlog_checkout_api()
        
        if result:
            print()
            print("=" * 55)
            print("CART CLEARING TEST RESULTS")
            print("=" * 55)
            
            self.log(f"Items before checkout: {result['before']}")
            self.log(f"Items after payment creation: {result['after_creation']}")
            self.log(f"Items after payment processing: {result['after_processing']}")
            self.log(f"Order created: {result['order_created']}")
            
            if result['after_processing'] == 0 and result['order_created']:
                self.log_success("🎉 CART CLEARING WORKS CORRECTLY VIA API!")
                self.log_success("✅ Cart is properly cleared after Pathlog Wallet checkout")
                self.log_success("✅ Order was successfully created")
                return True
            else:
                self.log_error("❌ CART CLEARING ISSUE DETECTED VIA API!")
                if result['after_processing'] > 0:
                    self.log_error(f"🔧 Cart still has {result['after_processing']} items after processing")
                if not result['order_created']:
                    self.log_error("🔧 No order was created")
                return False
        else:
            self.log_error("❌ TEST FAILED - Could not complete checkout simulation")
            return False

if __name__ == '__main__':
    tester = APICartClearingTest()
    success = tester.run_test()
    
    if success:
        print("\nAPI Test PASSED - Cart clearing works correctly!")
    else:
        print("\nAPI Test FAILED - Cart clearing needs attention!")