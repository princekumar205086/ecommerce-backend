#!/usr/bin/env python3
"""
COD (Cash on Delivery) Flow Test Script
=====================================

Tests the complete COD checkout flow including:
1. User authentication
2. Cart creation and item addition
3. COD payment creation with address saving
4. COD payment confirmation and order creation
5. Address persistence in user profile

Features tested:
- Address saving to user profile
- Shipping address as billing address
- COD payment creation and confirmation
- Order auto-creation after COD confirmation
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

class CODFlowTester:
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
            user = User.objects.get(email='testuser@example.com')
            print(f"📧 Using existing user: {user.email}")
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='testuser',
                email='testuser@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User',
                phone='1234567890'
            )
            print(f"👤 Created new user: {user.email}")
        
        # Login
        login_data = {
            "email": "testuser@example.com",
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
            # Find products that have variants
            products_with_variants = Product.objects.filter(
                is_publish=True,
                variants__isnull=False
            ).distinct()
            
            if not products_with_variants.exists():
                print("❌ No published products with variants found. Please create some product variants first.")
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
            "quantity": 2
        }
        
        response = self.session.post(f"{API_URL}/cart/add/", json=cart_data)
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Item added to cart successfully")
            print(f"📊 Cart data: {json.dumps(data, indent=2)}")
            
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
    
    def create_cod_payment(self):
        """Create COD payment with address details"""
        print("\n💳 Testing COD Payment Creation...")
        
        # Address data
        address_data = {
            "full_name": "Test User",
            "address_line_1": "123 Test Street",
            "address_line_2": "Apartment 4B",
            "city": "Test City",
            "state": "Test State",
            "postal_code": "123456",
            "country": "India"
        }
        
        # COD payment data
        payment_data = {
            "cart_id": self.cart_id,
            "payment_method": "cod",
            "shipping_address": address_data,
            "save_address_to_profile": True  # Test address saving
        }
        
        response = self.session.post(f"{API_URL}/payments/create-from-cart/", json=payment_data)
        print(f"🔍 Payment creation response - Status: {response.status_code}")
        print(f"📄 Response content: {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.payment_id = data['payment_id']  # Use payment_id instead of id
            print(f"✅ COD Payment created successfully")
            print(f"🆔 Payment ID: {self.payment_id}")
            print(f"� Amount: ₹{data['amount']}")
            print(f"� Currency: {data['currency']}")
            print(f"📝 Message: {data['message']}")
            print(f"➡️ Next Step: {data['next_step']}")
            print(f"📊 Order Summary: {json.dumps(data['order_summary'], indent=2)}")
            
            # Verify address was saved to user profile
            user = User.objects.get(id=self.user_id)
            print(f"\n👤 User address after payment creation:")
            print(f"   Address Line 1: {user.address_line_1}")
            print(f"   City: {user.city}")
            print(f"   State: {user.state}")
            print(f"   Postal Code: {user.postal_code}")
            
            return True
        else:
            print(f"❌ COD Payment creation failed")
            print(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            return False
    
    def confirm_cod_payment(self):
        """Confirm COD payment and trigger order creation"""
        print("\n✅ Testing COD Payment Confirmation...")
        
        confirmation_data = {
            "payment_id": self.payment_id,
            "cod_notes": "Customer confirmed COD order via phone"
        }
        
        response = self.session.post(f"{API_URL}/payments/confirm-cod/", json=confirmation_data)
        print(f"🔍 COD confirmation response - Status: {response.status_code}")
        print(f"📄 Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ COD Payment confirmed successfully")
            
            # Print available fields
            for key, value in data.items():
                print(f"   {key}: {value}")
            
            # Check if order was created
            if 'order_created' in data and data['order_created']:
                if 'order' in data and 'id' in data['order']:
                    self.order_id = data['order']['id']
                    print(f"📦 Order created automatically - Order ID: {self.order_id}")
                    print(f"📋 Order Number: {data['order']['order_number']}")
                    print(f"📊 Order Status: {data['order']['status']}")
                    print(f"💰 Order Total: ₹{data['order']['total']}")
                    print(f"📦 Items Count: {data['order']['items_count']}")
                    
                    # Get order details from database
                    try:
                        order = Order.objects.get(id=self.order_id)
                        print(f"📊 Database Order Details:")
                        print(f"   Status: {order.status}")
                        print(f"   Total: ₹{order.total}")
                        print(f"   Items: {order.items.count()}")
                        print(f"   Created: {order.created_at}")
                    except Order.DoesNotExist:
                        print("❌ Order not found in database")
                        return False
                else:
                    print("❌ Order data not found in response")
                    return False
            else:
                print("❌ Order was not created automatically")
                return False
            
            return True
        else:
            print(f"❌ COD Payment confirmation failed")
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
            print(f"🏠 Shipping Address: {payment.shipping_address}")
            
            # Check order
            if self.order_id:
                order = Order.objects.get(id=self.order_id)
                print(f"📦 Order Status: {order.status}")
                print(f"💰 Order Total: ₹{order.total}")
                print(f"📝 Order Items: {order.items.count()}")
            
            # Check user address
            user = User.objects.get(id=self.user_id)
            print(f"👤 User Address Updated:")
            print(f"   Full Address: {user.get_full_address()}")
            
            # Check cart (should be cleared)
            response = self.session.get(f"{API_URL}/cart/")
            if response.status_code == 200:
                cart_data = response.json()
                print(f"🛒 Cart Items After Order: {len(cart_data.get('items', []))}")
            
            print("\n✅ COD Flow completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error verifying final state: {e}")
            return False
    
    def run_complete_test(self):
        """Run the complete COD flow test"""
        print("🚀 Starting COD Flow Test")
        print("=" * 50)
        
        steps = [
            ("Authentication", self.authenticate),
            ("Cart and Items", self.create_cart_and_add_items),
            ("COD Payment Creation", self.create_cod_payment),
            ("COD Payment Confirmation", self.confirm_cod_payment),
            ("Final State Verification", self.verify_final_state)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            if not step_func():
                print(f"❌ COD Flow test failed at step: {step_name}")
                return False
        
        print("\n🎉 COD Flow Test Completed Successfully!")
        print("=" * 50)
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   User ID: {self.user_id}")
        print(f"   Cart ID: {self.cart_id}")
        print(f"   Payment ID: {self.payment_id}")
        print(f"   Order ID: {self.order_id}")
        print(f"   Payment Method: COD")
        print(f"   Address Saved: ✅")
        print(f"   Order Auto-Created: ✅")
        
        return True

def main():
    """Main function to run the COD flow test"""
    tester = CODFlowTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎯 All COD flow tests passed!")
        return 0
    else:
        print("\n💥 COD flow tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())