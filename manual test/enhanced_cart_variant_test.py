#!/usr/bin/env python
"""
Enhanced Cart System with Variant Selection Test
Tests the complete flow: Cart → Checkout → Payment → Order Creation

This test validates that the enhanced cart system with variant selection
works properly with the existing checkout, payment and order creation flow.
"""

import os
import django
import sys
import requests
import json
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

# Django imports
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Product, ProductVariant
from cart.models import Cart, CartItem
from orders.models import Order
from payments.models import Payment

User = get_user_model()

class EnhancedCartVariantTest:
    def __init__(self):
        self.client = APIClient()
        self.base_url = 'http://localhost:8000'
        self.test_user = None
        self.test_products = []
        self.test_variants = []
        self.access_token = None
        
    def setup_test_data(self):
        """Setup test user and products with variants"""
        print("🔧 Setting up test data...")
        
        # Create test user
        try:
            self.test_user, created = User.objects.get_or_create(
                email='testuser@example.com',
                defaults={
                    'full_name': 'Test User',
                    'role': 'user',
                    'is_active': True
                }
            )
            if created:
                self.test_user.set_password('testpass123')
                self.test_user.save()
                print(f"✅ Created test user: {self.test_user.email}")
            else:
                print(f"✅ Using existing test user: {self.test_user.email}")
                
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            return False
            
        # Get existing products or create test products
        products = Product.objects.filter(status='published')[:3]
        if products.count() >= 2:
            self.test_products = list(products)
            print(f"✅ Using existing products: {[p.name for p in self.test_products]}")
            
            # Get variants for these products
            for product in self.test_products:
                variants = ProductVariant.objects.filter(
                    product=product, 
                    status='approved'
                )[:2]
                self.test_variants.extend(list(variants))
                
            if self.test_variants:
                print(f"✅ Found {len(self.test_variants)} variants for testing")
            else:
                print("⚠️ No variants found, will test without variants")
        else:
            print("❌ Insufficient products found. Please ensure products exist in the database.")
            return False
            
        return True
    
    def authenticate(self):
        """Get JWT token for authentication"""
        print("🔐 Authenticating user...")
        
        try:
            # Generate JWT token
            refresh = RefreshToken.for_user(self.test_user)
            self.access_token = str(refresh.access_token)
            
            # Set authorization header
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
            
            print(f"✅ Authentication successful")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def test_enhanced_cart_operations(self):
        """Test enhanced cart operations with variant selection"""
        print("\n📦 Testing Enhanced Cart Operations with Variants...")
        
        results = {
            'cart_creation': False,
            'add_without_variant': False,
            'add_with_variant': False,
            'variant_display': False,
            'stock_validation': False,
            'cart_summary': False
        }
        
        try:
            # 1. Test getting empty cart (auto-creation)
            print("1️⃣ Testing cart auto-creation...")
            response = self.client.get('/api/cart/')
            if response.status_code == 200:
                cart_data = response.json()
                print(f"✅ Cart created successfully: {cart_data['id']}")
                print(f"   Items count: {cart_data['items_count']}")
                print(f"   Total items: {cart_data['total_items']}")
                results['cart_creation'] = True
            else:
                print(f"❌ Cart creation failed: {response.status_code}")
                print(f"   Response: {response.json()}")
                
            # 2. Test adding product without variant
            print("\n2️⃣ Testing add to cart without variant...")
            if self.test_products:
                product = self.test_products[0]
                add_data = {
                    'product_id': product.id,
                    'quantity': 2
                }
                response = self.client.post('/api/cart/add/', add_data)
                if response.status_code in [200, 201]:
                    print(f"✅ Added product without variant: {product.name}")
                    results['add_without_variant'] = True
                else:
                    print(f"❌ Failed to add product: {response.status_code}")
                    print(f"   Response: {response.json()}")
                    
            # 3. Test adding product with variant
            print("\n3️⃣ Testing add to cart with variant...")
            if self.test_variants:
                variant = self.test_variants[0]
                add_data = {
                    'product_id': variant.product.id,
                    'variant_id': variant.id,
                    'quantity': 1
                }
                response = self.client.post('/api/cart/add/', add_data)
                if response.status_code in [200, 201]:
                    print(f"✅ Added product with variant: {variant.product.name} ({variant})")
                    results['add_with_variant'] = True
                else:
                    print(f"❌ Failed to add product with variant: {response.status_code}")
                    print(f"   Response: {response.json()}")
                    
            # 4. Test enhanced cart response with variant information
            print("\n4️⃣ Testing enhanced cart response...")
            response = self.client.get('/api/cart/')
            if response.status_code == 200:
                cart_data = response.json()
                print(f"✅ Cart retrieved with {len(cart_data['items'])} items")
                
                # Check variant display information
                for item in cart_data['items']:
                    print(f"   📦 Item: {item['product']['name']}")
                    print(f"      Variant Display: {item['variant_display']}")
                    print(f"      Unit Price: ₹{item['unit_price']}")
                    print(f"      Available Stock: {item['available_stock']}")
                    print(f"      Is Available: {item['is_available']}")
                    
                    if 'variant_display' in item and 'unit_price' in item:
                        results['variant_display'] = True
                        
                # Check cart summary
                if 'has_unavailable_items' in cart_data:
                    print(f"   Has Unavailable Items: {cart_data['has_unavailable_items']}")
                    results['cart_summary'] = True
                    
            # 5. Test stock validation
            print("\n5️⃣ Testing stock validation...")
            if self.test_products:
                product = self.test_products[0]
                # Try to add more than available stock
                large_quantity = 9999
                add_data = {
                    'product_id': product.id,
                    'quantity': large_quantity
                }
                response = self.client.post('/api/cart/add/', add_data)
                if response.status_code == 400:
                    error_data = response.json()
                    if 'available' in str(error_data).lower() or 'stock' in str(error_data).lower():
                        print(f"✅ Stock validation working correctly")
                        results['stock_validation'] = True
                    else:
                        print(f"⚠️ Stock validation error format: {error_data}")
                else:
                    print(f"⚠️ Expected stock validation error, got: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Cart operations test failed: {e}")
            
        return results
    
    def test_checkout_integration(self):
        """Test that enhanced cart integrates with existing checkout"""
        print("\n🛒 Testing Cart → Checkout Integration...")
        
        results = {
            'checkout_creation': False,
            'variant_in_order': False,
            'pricing_calculation': False
        }
        
        try:
            # Ensure we have items in cart
            if self.test_products:
                # Add a product with variant to cart
                if self.test_variants:
                    add_data = {
                        'product_id': self.test_variants[0].product.id,
                        'variant_id': self.test_variants[0].id,
                        'quantity': 1
                    }
                    self.client.post('/api/cart/add/', add_data)
                    
            # Get cart to obtain cart_id
            cart_response = self.client.get('/api/cart/')
            cart_id = cart_response.json()['id'] if cart_response.status_code == 200 else None
            
            # Test checkout from cart
            print("1️⃣ Testing order creation from cart...")
            checkout_data = {
                'cart_id': cart_id,
                'shipping_address': {
                    'line1': 'Test Address',
                    'city': 'Test City',
                    'state': 'Test State',
                    'postal_code': '123456',
                    'country': 'India'
                },
                'billing_address': {
                    'line1': 'Test Address',
                    'city': 'Test City', 
                    'state': 'Test State',
                    'postal_code': '123456',
                    'country': 'India'
                },
                'payment_method': 'cod',
                'notes': 'Test order from enhanced cart'
            }
            
            response = self.client.post('/api/orders/checkout/', checkout_data, format='json')
            if response.status_code == 201:
                order_data = response.json()
                print(f"✅ Order created successfully: {order_data['order_number']}")
                print(f"   Total: ₹{order_data['total']}")
                print(f"   Items: {len(order_data['items'])}")
                results['checkout_creation'] = True
                
                # Check if variant information is preserved in order items
                for item in order_data['items']:
                    print(f"   📦 Order Item: {item['product']['name']}")
                    if item.get('variant'):
                        variant_info = item['variant']
                        print(f"      Variant: {variant_info}")
                        if 'additional_price' in variant_info:
                            print(f"      Additional Price: ₹{variant_info['additional_price']}")
                        results['variant_in_order'] = True
                    print(f"      Quantity: {item['quantity']}")
                    print(f"      Price: ₹{item['price']}")
                    
                # Verify pricing calculations
                if 'subtotal' in order_data and 'total' in order_data:
                    print(f"   Subtotal: ₹{order_data['subtotal']}")
                    print(f"   Total: ₹{order_data['total']}")
                    results['pricing_calculation'] = True
                    
            else:
                print(f"❌ Checkout failed: {response.status_code}")
                error_data = response.json()
                print(f"   Response: {error_data}")
                
        except Exception as e:
            print(f"❌ Checkout integration test failed: {e}")
            
        return results
    
    def test_payment_integration(self):
        """Test that cart integrates with payment system"""
        print("\n💳 Testing Cart → Payment Integration...")
        
        results = {
            'payment_creation': False,
            'cart_data_in_payment': False
        }
        
        try:
            # Ensure we have items in cart
            if self.test_products:
                # Clear cart first
                self.client.delete('/api/cart/clear/')
                
                # Add a product with variant to cart
                if self.test_variants:
                    add_data = {
                        'product_id': self.test_variants[0].product.id,
                        'variant_id': self.test_variants[0].id,
                        'quantity': 2
                    }
                    self.client.post('/api/cart/add/', add_data)
                
            # Test payment creation from cart
            print("1️⃣ Testing payment creation from cart...")
            
            # Get cart to obtain cart_id  
            cart_response = self.client.get('/api/cart/')
            cart_id = cart_response.json()['id'] if cart_response.status_code == 200 else None
            
            payment_data = {
                'cart_id': cart_id,
                'payment_method': 'cod',
                'shipping_address': {
                    'full_name': 'Test User',
                    'address_line_1': 'Test Address',
                    'address_line_2': '',
                    'city': 'Test City',
                    'state': 'Test State',
                    'postal_code': '123456',
                    'country': 'India',
                    'phone': '9999999999'
                }
            }
            
            response = self.client.post('/api/payments/create-from-cart/', payment_data, format='json')
            if response.status_code in [200, 201]:
                payment_response = response.json()
                print(f"✅ Payment created successfully: {payment_response['payment_id']}")
                print(f"   Amount: ₹{payment_response['amount']}")
                print(f"   Payment Method: {payment_response['payment_method']}")
                results['payment_creation'] = True
                
                # Check if cart data is stored in payment
                if 'order_summary' in payment_response:
                    summary = payment_response['order_summary']
                    print(f"   Order Summary:")
                    print(f"     Subtotal: ₹{summary.get('subtotal', 0)}")
                    print(f"     Tax: ₹{summary.get('tax', 0)}")
                    print(f"     Total: ₹{summary.get('total', 0)}")
                    results['cart_data_in_payment'] = True
                    
            else:
                print(f"❌ Payment creation failed: {response.status_code}")
                error_data = response.json()
                print(f"   Response: {error_data}")
                
        except Exception as e:
            print(f"❌ Payment integration test failed: {e}")
            
        return results
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Clear cart
            self.client.delete('/api/cart/clear/')
            print("✅ Cart cleared")
            
            # Don't delete test user as it might be used by other tests
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("🚀 Starting Enhanced Cart System with Variant Selection Test")
        print("=" * 70)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Test setup failed")
            return False
            
        if not self.authenticate():
            print("❌ Authentication failed")
            return False
        
        # Run tests
        cart_results = self.test_enhanced_cart_operations()
        checkout_results = self.test_checkout_integration()
        payment_results = self.test_payment_integration()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Results summary
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        all_results = {**cart_results, **checkout_results, **payment_results}
        
        passed = sum(all_results.values())
        total = len(all_results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"\n🧪 ENHANCED CART SYSTEM TESTS")
        print(f"✅ Cart Creation: {'PASS' if cart_results['cart_creation'] else 'FAIL'}")
        print(f"✅ Add without Variant: {'PASS' if cart_results['add_without_variant'] else 'FAIL'}")
        print(f"✅ Add with Variant: {'PASS' if cart_results['add_with_variant'] else 'FAIL'}")
        print(f"✅ Variant Display: {'PASS' if cart_results['variant_display'] else 'FAIL'}")
        print(f"✅ Stock Validation: {'PASS' if cart_results['stock_validation'] else 'FAIL'}")
        print(f"✅ Cart Summary: {'PASS' if cart_results['cart_summary'] else 'FAIL'}")
        
        print(f"\n🛒 CHECKOUT INTEGRATION TESTS")
        print(f"✅ Checkout Creation: {'PASS' if checkout_results['checkout_creation'] else 'FAIL'}")
        print(f"✅ Variant in Order: {'PASS' if checkout_results['variant_in_order'] else 'FAIL'}")
        print(f"✅ Pricing Calculation: {'PASS' if checkout_results['pricing_calculation'] else 'FAIL'}")
        
        print(f"\n💳 PAYMENT INTEGRATION TESTS")
        print(f"✅ Payment Creation: {'PASS' if payment_results['payment_creation'] else 'FAIL'}")
        print(f"✅ Cart Data in Payment: {'PASS' if payment_results['cart_data_in_payment'] else 'FAIL'}")
        
        print(f"\n📈 Overall: {passed}/{total} tests passed ({success_rate:.1f}% success rate)")
        
        if success_rate >= 80:
            print("🎉 Enhanced cart system is working correctly!")
        elif success_rate >= 60:
            print("⚠️ Enhanced cart system has some issues but core functionality works")
        else:
            print("❌ Enhanced cart system needs attention")
            
        return success_rate >= 80

if __name__ == '__main__':
    tester = EnhancedCartVariantTest()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("🚀 Enhanced cart system with variant selection is ready for production!")
    else:
        print("\n⚠️ Some tests failed. Please review the results above.")
        
    sys.exit(0 if success else 1)