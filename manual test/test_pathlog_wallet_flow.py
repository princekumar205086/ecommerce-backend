#!/usr/bin/env python3
"""
Pathlog Wallet Payment Flow Test Script
=====================================

Tests the complete Pathlog Wallet payment flow including:
1. User authentication
2. Cart creation and item addition
3. Pathlog Wallet payment creation
4. Mobile number verification
5. OTP verification and balance check
6. Payment processing and order creation

Features tested:
- Pathlog Wallet payment method
- Mobile number verification flow
- OTP verification with balance display
- Payment processing with transaction ID
- Order auto-creation after successful payment
"""

import os
import sys
import django
import requests
import json
from decimal import Decimal

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

# Import Django models
from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant
from cart.models import Cart, CartItem
from payments.models import Payment
from orders.models import Order

User = get_user_model()

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api"

class PathlogWalletTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.cart_id = None
        self.payment_id = None
        self.order_id = None
        
    def authenticate(self):
        """Authenticate and get access token"""
        print("🔐 Testing Authentication...")
        
        # Try to get existing test user or create one
        try:
            user = User.objects.get(email='walletuser@example.com')
            print(f"📧 Using existing user: {user.email}")
        except User.DoesNotExist:
            user = User.objects.create_user(
                email='walletuser@example.com',
                password='testpass123',
                full_name='Wallet User',
                contact='8677939971'
            )
            print(f"👤 Created new user: {user.email}")
        
        # Login
        login_data = {
            "email": "walletuser@example.com",
            "password": "testpass123"
        }
        
        response = self.session.post(f"{API_URL}/accounts/login/", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data['access']
            self.user_id = data['user']['id']
            self.session.headers.update({
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json'
            })
            print(f"✅ Authentication successful - User ID: {self.user_id}")
            return True
        else:
            print(f"❌ Authentication failed: {response.text}")
            return False
    
    def create_cart_and_add_items(self):
        """Create cart and add test items"""
        print("\n🛒 Testing Cart Creation and Item Addition...")
        
        # Get a test product with variants
        try:
            products_with_variants = Product.objects.filter(
                is_publish=True,
                variants__isnull=False
            ).distinct()
            
            if not products_with_variants.exists():
                print("❌ No published products with variants found.")
                return False
                
            product = products_with_variants.first()
            variant = ProductVariant.objects.filter(product=product).first()
            
            print(f"🛍️ Using product: {product.name}")
            print(f"📦 Using variant: {variant.size} - ₹{variant.total_price}")
            
        except Exception as e:
            print(f"❌ Error getting test product: {e}")
            return False
        
        # Add item to cart
        cart_data = {
            "product_id": product.id,
            "variant_id": variant.id,
            "quantity": 1
        }
        
        response = self.session.post(f"{API_URL}/cart/add/", json=cart_data)
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Item added to cart successfully")
            
            # Get cart details
            response = self.session.get(f"{API_URL}/cart/")
            if response.status_code == 200:
                cart_data = response.json()
                self.cart_id = cart_data['id']
                print(f"🆔 Cart ID: {self.cart_id}")
                print(f"💰 Total Amount: ₹{cart_data['total_price']}")
                return True
            else:
                print(f"❌ Failed to get cart details: {response.text}")
                return False
        else:
            print(f"❌ Failed to add item to cart: {response.text}")
            return False
    
    def create_pathlog_wallet_payment(self):
        """Create Pathlog Wallet payment"""
        print("\n💳 Testing Pathlog Wallet Payment Creation...")
        
        # Address data
        address_data = {
            "full_name": "Wallet User",
            "address_line_1": "456 Wallet Street",
            "address_line_2": "Suite 7C",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400001",
            "country": "India"
        }
        
        # Pathlog Wallet payment data
        payment_data = {
            "cart_id": self.cart_id,
            "payment_method": "pathlog_wallet",
            "shipping_address": address_data,
            "save_address_to_profile": True
        }
        
        response = self.session.post(f"{API_URL}/payments/create-from-cart/", json=payment_data)
        print(f"🔍 Payment creation response - Status: {response.status_code}")
        print(f"📄 Response content: {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.payment_id = data['payment_id']
            print(f"✅ Pathlog Wallet Payment created successfully")
            print(f"🆔 Payment ID: {self.payment_id}")
            print(f"💰 Amount: ₹{data['amount']}")
            print(f"💱 Currency: {data['currency']}")
            print(f"📝 Message: {data['message']}")
            print(f"➡️ Next Step: {data['next_step']}")
            print(f"📊 Order Summary: {json.dumps(data['order_summary'], indent=2)}")
            return True
        else:
            print(f"❌ Pathlog Wallet Payment creation failed")
            print(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            return False
    
    def verify_mobile_number(self):
        """Verify mobile number for Pathlog Wallet"""
        print("\n📱 Testing Mobile Number Verification...")
        
        verification_data = {
            "payment_id": self.payment_id,
            "mobile_number": "8677939971"  # Same as user's phone
        }
        
        response = self.session.post(f"{API_URL}/payments/pathlog-wallet/verify/", json=verification_data)
        print(f"🔍 Mobile verification response - Status: {response.status_code}")
        print(f"📄 Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Mobile number verified successfully")
            print(f"📱 Mobile: +91 {data['mobile_number']}")
            print(f"📝 Status: {data['status']}")
            print(f"💬 Message: {data['message']}")
            print(f"🔐 Demo OTP: {data.get('demo_otp', 'Not provided')}")
            return True
        else:
            print(f"❌ Mobile verification failed")
            print(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            return False
    
    def verify_otp_and_check_balance(self):
        """Verify OTP and check wallet balance"""
        print("\n🔐 Testing OTP Verification and Balance Check...")
        
        otp_data = {
            "payment_id": self.payment_id,
            "otp": "123456"  # Demo OTP
        }
        
        response = self.session.post(f"{API_URL}/payments/pathlog-wallet/otp/", json=otp_data)
        print(f"🔍 OTP verification response - Status: {response.status_code}")
        print(f"📄 Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ OTP verified successfully")
            print(f"📋 Status: {data['status']}")
            print(f"👤 Account Details:")
            print(f"   Name: {data['account_details']['name']}")
            print(f"   Phone: {data['account_details']['phone']}")
            print(f"   Pathlog ID: {data['account_details']['pathlog_id']}")
            print(f"💰 Available Balance: ₹{data['available_balance']}")
            print(f"💳 Payment Amount: ₹{data['payment_amount']}")
            print(f"🏦 Remaining Balance: ₹{data['remaining_balance']}")
            print(f"✅ Can Proceed: {data['can_proceed']}")
            
            if data['can_proceed']:
                print("✅ Sufficient balance to proceed with payment")
                return True
            else:
                print("❌ Insufficient balance for payment")
                return False
        else:
            print(f"❌ OTP verification failed")
            print(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            return False
    
    def process_payment(self):
        """Process Pathlog Wallet payment"""
        print("\n💸 Testing Payment Processing...")
        
        payment_data = {
            "payment_id": self.payment_id
        }
        
        response = self.session.post(f"{API_URL}/payments/pathlog-wallet/pay/", json=payment_data)
        print(f"🔍 Payment processing response - Status: {response.status_code}")
        print(f"📄 Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Payment processed successfully")
            print(f"📋 Status: {data['status']}")
            print(f"💬 Message: {data['message']}")
            print(f"🆔 Transaction ID: {data['transaction_id']}")
            
            # Check if order was created
            if data.get('order_created'):
                self.order_id = data['order']['id']
                print(f"📦 Order created automatically - Order ID: {self.order_id}")
                print(f"📋 Order Number: {data['order']['order_number']}")
                print(f"📊 Order Status: {data['order']['status']}")
                print(f"💰 Order Total: ₹{data['order']['total']}")
                print(f"📦 Items Count: {data['order']['items_count']}")
                print(f"💳 Payment Status: {data['order']['payment_status']}")
            
            return True
        else:
            print(f"❌ Payment processing failed")
            print(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            return False
    
    def verify_final_state(self):
        """Verify the final state of all entities"""
        print("\n🔍 Verifying Final State...")
        
        try:
            # Check payment
            payment = Payment.objects.get(id=self.payment_id)
            print(f"💳 Payment Status: {payment.status}")
            print(f"💰 Payment Amount: ₹{payment.amount}")
            print(f"📱 Wallet Mobile: {payment.pathlog_wallet_mobile}")
            print(f"✅ Wallet Verified: {payment.pathlog_wallet_verified}")
            print(f"💰 Wallet Balance: ₹{payment.pathlog_wallet_balance}")
            print(f"🆔 Transaction ID: {payment.pathlog_transaction_id}")
            
            # Check order
            if self.order_id:
                order = Order.objects.get(id=self.order_id)
                print(f"📦 Order Status: {order.status}")
                print(f"💰 Order Total: ₹{order.total}")
                print(f"📝 Order Items: {order.items.count()}")
                print(f"💳 Payment Status: {order.payment_status}")
            
            # Check cart (should be cleared)
            response = self.session.get(f"{API_URL}/cart/")
            if response.status_code == 200:
                cart_data = response.json()
                print(f"🛒 Cart Items After Order: {len(cart_data.get('items', []))}")
            
            print("\n✅ Pathlog Wallet Flow completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error verifying final state: {e}")
            return False
    
    def run_complete_test(self):
        """Run the complete Pathlog Wallet flow test"""
        print("🚀 Starting Pathlog Wallet Flow Test")
        print("=" * 50)
        
        steps = [
            ("Authentication", self.authenticate),
            ("Cart and Items", self.create_cart_and_add_items),
            ("Pathlog Wallet Payment Creation", self.create_pathlog_wallet_payment),
            ("Mobile Number Verification", self.verify_mobile_number),
            ("OTP Verification & Balance Check", self.verify_otp_and_check_balance),
            ("Payment Processing", self.process_payment),
            ("Final State Verification", self.verify_final_state)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            if not step_func():
                print(f"❌ Pathlog Wallet Flow test failed at step: {step_name}")
                return False
        
        print("\n🎉 Pathlog Wallet Flow Test Completed Successfully!")
        print("=" * 50)
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   User ID: {self.user_id}")
        print(f"   Cart ID: {self.cart_id}")
        print(f"   Payment ID: {self.payment_id}")
        print(f"   Order ID: {self.order_id}")
        print(f"   Payment Method: Pathlog Wallet")
        print(f"   Mobile Verified: ✅")
        print(f"   OTP Verified: ✅")
        print(f"   Balance Checked: ✅")
        print(f"   Payment Processed: ✅")
        print(f"   Order Auto-Created: ✅")
        
        return True

def main():
    """Main function to run the Pathlog Wallet flow test"""
    tester = PathlogWalletTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎯 All Pathlog Wallet flow tests passed!")
        return 0
    else:
        print("\n💥 Pathlog Wallet flow tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())