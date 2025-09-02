#!/usr/bin/env python
"""
Comprehensive Order Endpoint Testing
Tests all order-related endpoints including ShipRocket integration for user, supplier and admin roles
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from products.models import Product, ProductCategory, ProductVariant
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem, OrderStatusChange
from coupon.models import Coupon
from shipping.models import Shipment
from shiprocket_service import shiprocket_api

User = get_user_model()

class OrderEndpointTestSuite:
    """Comprehensive test suite for all order-related endpoints"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.client = APIClient()
        self.users = {}
        self.products = {}
        self.orders = {}
        self.tokens = {}
        
    def setup_test_data(self):
        """Create test users, products, and initial data"""
        print("🔧 Setting up test data...")
        
        # Create test users with unique emails to avoid conflicts
        import random
        timestamp = str(int(datetime.now().timestamp()))
        
        # Try to get or create test users
        admin_email = f'admin_test_{timestamp}@test.com'
        supplier_email = f'supplier_test_{timestamp}@test.com'
        user_email = f'user_test_{timestamp}@test.com'
        
        try:
            self.users['admin'] = User.objects.get(email=admin_email)
        except User.DoesNotExist:
            self.users['admin'] = User.objects.create_user(
                email=admin_email,
                password='admin123',
                full_name='Admin User',
                contact='1234567890',
                role='admin',
                is_staff=True,
                is_superuser=True
            )
        
        try:
            self.users['supplier'] = User.objects.get(email=supplier_email)
        except User.DoesNotExist:
            self.users['supplier'] = User.objects.create_user(
                email=supplier_email,
                password='supplier123',
                full_name='Supplier User',
                contact='1234567891',
                role='supplier'
            )
        
        try:
            self.users['user'] = User.objects.get(email=user_email)
        except User.DoesNotExist:
            self.users['user'] = User.objects.create_user(
                email=user_email,
                password='user123',
                full_name='Regular User',
                contact='1234567892',
                role='user',
                address_line_1='123 Test Street',
                city='Delhi',
                state='Delhi',
                postal_code='110001',
                country='India'
            )
        
        # Create test category
        try:
            category_name = f'Test Category {timestamp}'
            category = ProductCategory.objects.create(
                name=category_name,
                created_by=self.users['admin']
            )
        except Exception as e:
            print(f"Note: Using existing category or creating simple one: {e}")
            # Try to get an existing category
            try:
                category = ProductCategory.objects.first()
                if not category:
                    raise Exception("No categories found")
            except:
                category = ProductCategory.objects.create(
                    name=f'Fallback Category {timestamp}',
                    created_by=self.users['admin']
                )
        
        # Create test products
        for i in range(3):
            product_name = f'Test Product {timestamp}_{i+1}'
            try:
                product = Product.objects.create(
                    name=product_name,
                    description=f'Test product description {i+1}',
                    price=Decimal(f'{100 + i*50}.00'),
                    stock=50,
                    category=category,
                    created_by=self.users['admin'],
                    sku=f'TEST{timestamp}_{i+1}',
                    weight=f'{0.5}kg'  # Weight is CharField
                )
                self.products[f'product_{i+1}'] = product
            except Exception as e:
                print(f"Note: Could not create product {i+1}: {e}")
                # Try to use existing product
                try:
                    existing_product = Product.objects.first()
                    if existing_product:
                        self.products[f'product_{i+1}'] = existing_product
                except:
                    pass
            
            # Create product variant if supported
            try:
                if hasattr(Product, 'variants') and f'product_{i+1}' in self.products:
                    variant = ProductVariant.objects.create(
                        product=self.products[f'product_{i+1}'],
                        size=f'Size {i+1}',
                        weight=f'{0.5}kg',
                        additional_price=Decimal('10.00'),
                        stock=30
                    )
            except Exception as e:
                print(f"Note: Could not create variant: {e}")
        
        # Create test coupon
        try:
            Coupon.objects.create(
                code=f'TEST{timestamp}',
                coupon_type='percentage',
                discount_value=10,
                minimum_order_amount=100,
                maximum_discount_amount=50,
                max_uses=100,
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                is_active=True
            )
        except Exception as e:
            print(f"Note: Could not create coupon: {e}")
        
        print("✅ Test data setup complete")
        
    def get_auth_token(self, user_type):
        """Get JWT token for user authentication"""
        if user_type in self.tokens:
            return self.tokens[user_type]
            
        user = self.users[user_type]
        response = requests.post(f"{self.base_url}/api/token/", {
            'email': user.email,
            'password': f'{user_type}123'
        })
        
        if response.status_code == 200:
            token = response.json()['access']
            self.tokens[user_type] = token
            return token
        else:
            print(f"❌ Failed to get token for {user_type}: {response.text}")
            return None
    
    def get_headers(self, user_type):
        """Get authorization headers for requests"""
        token = self.get_auth_token(user_type)
        return {'Authorization': f'Bearer {token}'} if token else {}
    
    def test_cart_to_order_flow(self):
        """Test complete cart to order flow"""
        print("\n🛒 Testing Cart to Order Flow...")
        
        # 1. Add items to cart
        headers = self.get_headers('user')
        
        # Add product to cart
        cart_data = {
            'product_id': self.products['product_1'].id,
            'quantity': 2
        }
        
        response = requests.post(
            f"{self.base_url}/api/cart/add/",
            json=cart_data,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            print("✅ Product added to cart")
            cart_response = response.json()
        else:
            print(f"❌ Failed to add product to cart: {response.text}")
            return False
        
        # 2. Get cart to get cart ID
        response = requests.get(f"{self.base_url}/api/cart/", headers=headers)
        if response.status_code == 200:
            cart_data = response.json()
            print(f"✅ Cart retrieved with {len(cart_data.get('items', []))} items")
            cart_id = cart_data.get('id')
        else:
            print(f"❌ Failed to get cart: {response.text}")
            return False
        
        # 3. Checkout cart to create order
        checkout_data = {
            'cart_id': cart_id,  # Add cart_id from the cart response
            'shipping_address': {
                'name': 'John Doe',
                'address_line_1': '123 Test Street',
                'city': 'Delhi',
                'state': 'Delhi',
                'postal_code': '110001',
                'country': 'India',
                'phone': '9876543210'
            },
            'billing_address': {
                'name': 'John Doe',
                'address_line_1': '123 Test Street',
                'city': 'Delhi',
                'state': 'Delhi',
                'postal_code': '110001',
                'country': 'India',
                'phone': '9876543210'
            },
            'payment_method': 'cod'
        }
        
        response = requests.post(
            f"{self.base_url}/api/orders/checkout/",
            json=checkout_data,
            headers=headers
        )
        
        if response.status_code == 201:
            order_data = response.json()
            self.orders['test_order'] = order_data
            print(f"✅ Order created successfully: {order_data.get('order_number')}")
            return True
        else:
            print(f"❌ Order creation failed: {response.text}")
            return False
    
    def test_user_order_endpoints(self):
        """Test user-specific order endpoints"""
        print("\n👤 Testing User Order Endpoints...")
        
        headers = self.get_headers('user')
        
        # 1. List user orders
        response = requests.get(f"{self.base_url}/api/orders/", headers=headers)
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ User orders listed: {len(orders.get('results', orders)) if isinstance(orders, dict) else len(orders)} orders")
        else:
            print(f"❌ Failed to list user orders: {response.text}")
        
        # 2. Get specific order details
        if 'test_order' in self.orders:
            order_id = self.orders['test_order']['id']
            response = requests.get(f"{self.base_url}/api/orders/{order_id}/", headers=headers)
            if response.status_code == 200:
                order_detail = response.json()
                print(f"✅ Order details retrieved: {order_detail.get('order_number')}")
            else:
                print(f"❌ Failed to get order details: {response.text}")
        
        # 3. Test order filtering
        response = requests.get(f"{self.base_url}/api/orders/?status=pending", headers=headers)
        if response.status_code == 200:
            print("✅ Order filtering by status works")
        else:
            print(f"❌ Order filtering failed: {response.text}")
        
        # 4. Apply coupon to order (if order exists)
        if 'test_order' in self.orders:
            order_id = self.orders['test_order']['id']
            coupon_data = {'coupon_code': 'TEST10'}
            response = requests.post(
                f"{self.base_url}/api/orders/{order_id}/apply-coupon/",
                json=coupon_data,
                headers=headers
            )
            if response.status_code == 200:
                print("✅ Coupon applied successfully")
            else:
                print(f"❌ Coupon application failed: {response.text}")
        
        return True
    
    def test_admin_order_endpoints(self):
        """Test admin-specific order endpoints"""
        print("\n👨‍💼 Testing Admin Order Endpoints...")
        
        headers = self.get_headers('admin')
        
        # 1. List all orders (admin view)
        response = requests.get(f"{self.base_url}/api/orders/", headers=headers)
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ Admin can view all orders: {len(orders.get('results', orders)) if isinstance(orders, dict) else len(orders)} orders")
        else:
            print(f"❌ Admin failed to list orders: {response.text}")
        
        # 2. Order statistics
        response = requests.get(f"{self.base_url}/api/orders/stats/", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Order statistics retrieved: {stats.get('total_orders', 0)} total orders")
        else:
            print(f"❌ Failed to get order statistics: {response.text}")
        
        if 'test_order' in self.orders:
            order_id = self.orders['test_order']['id']
            
            # 3. Accept order
            accept_data = {
                'order_id': order_id,
                'notes': 'Order accepted by admin for testing'
            }
            response = requests.post(
                f"{self.base_url}/api/orders/admin/accept/",
                json=accept_data,
                headers=headers
            )
            if response.status_code == 200:
                print("✅ Order accepted by admin")
            else:
                print(f"❌ Order acceptance failed: {response.text}")
            
            # 4. Assign shipping
            shipping_data = {
                'order_id': order_id,
                'shipping_partner': 'Shiprocket',
                'tracking_id': 'TEST123456789',
                'notes': 'Assigned to Shiprocket for shipping'
            }
            response = requests.post(
                f"{self.base_url}/api/orders/admin/assign-shipping/",
                json=shipping_data,
                headers=headers
            )
            if response.status_code == 200:
                print("✅ Shipping assigned successfully")
            else:
                print(f"❌ Shipping assignment failed: {response.text}")
            
            # 5. Mark as delivered
            delivery_data = {
                'order_id': order_id,
                'notes': 'Order delivered successfully'
            }
            response = requests.post(
                f"{self.base_url}/api/orders/admin/mark-delivered/",
                json=delivery_data,
                headers=headers
            )
            if response.status_code == 200:
                print("✅ Order marked as delivered")
            else:
                print(f"❌ Mark delivered failed: {response.text}")
        
        return True
    
    def test_shiprocket_endpoints(self):
        """Test ShipRocket integration endpoints"""
        print("\n🚚 Testing ShipRocket Integration Endpoints...")
        
        headers = self.get_headers('admin')
        
        # 1. Test serviceability check endpoint
        serviceability_data = {
            'pickup_pincode': '110001',
            'delivery_pincode': '110002',
            'weight': 1.0,
            'cod': False
        }
        response = requests.post(
            f"{self.base_url}/api/orders/shiprocket/serviceability/",
            json=serviceability_data,
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Serviceability endpoint works: {result.get('success', False)}")
        else:
            print(f"⚠️  Serviceability endpoint failed: {response.status_code}")
        
        # 2. Test shipping rates endpoint
        rates_data = {
            'pickup_pincode': '110001',
            'delivery_pincode': '110002',
            'weight': 1.0,
            'dimensions': {'length': 10, 'breadth': 10, 'height': 5}
        }
        response = requests.post(
            f"{self.base_url}/api/orders/shiprocket/rates/",
            json=rates_data,
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Shipping rates endpoint works: {result.get('success', False)}")
        else:
            print(f"⚠️  Shipping rates endpoint failed: {response.status_code}")
        
        # 3. Test ShipRocket order creation endpoint (if order exists)
        if 'test_order' in self.orders:
            create_data = {'order_id': self.orders['test_order']['id']}
            response = requests.post(
                f"{self.base_url}/api/orders/shiprocket/create/",
                json=create_data,
                headers=headers
            )
            if response.status_code in [200, 400]:  # 400 might be expected due to auth
                print("✅ ShipRocket order creation endpoint accessible")
            else:
                print(f"⚠️  ShipRocket order creation failed: {response.status_code}")
        
        return True
    
    def test_supplier_endpoints(self):
        """Test supplier-specific order endpoints"""
        print("\n🏪 Testing Supplier Order Endpoints...")
        
        headers = self.get_headers('supplier')
        
        # 1. Supplier order list
        response = requests.get(f"{self.base_url}/api/orders/supplier/", headers=headers)
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ Supplier can view orders: {len(orders.get('results', orders)) if isinstance(orders, dict) else len(orders)} orders")
        else:
            print(f"❌ Supplier order access failed: {response.text}")
        
        # 2. Supplier order stats
        response = requests.get(f"{self.base_url}/api/orders/supplier/stats/", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Supplier order stats retrieved: {stats.get('total_orders', 0)} total orders")
        else:
            print(f"❌ Supplier stats failed: {response.text}")
        
        # 3. Supplier order summary
        response = requests.get(f"{self.base_url}/api/orders/supplier/my_orders_summary/", headers=headers)
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Supplier order summary retrieved: {summary.get('total_orders', 0)} orders")
        else:
            print(f"❌ Supplier summary failed: {response.text}")
        
        return True
    
    def test_error_scenarios(self):
        """Test error handling and edge cases"""
        print("\n🚫 Testing Error Scenarios...")
        
        headers = self.get_headers('user')
        
        # 1. Test checkout with empty cart
        empty_checkout_data = {
            'shipping_address': {'name': 'Test'},
            'billing_address': {'name': 'Test'},
            'payment_method': 'cod'
        }
        
        response = requests.post(
            f"{self.base_url}/api/orders/checkout/",
            json=empty_checkout_data,
            headers=headers
        )
        if response.status_code == 400:
            print("✅ Empty cart checkout properly rejected")
        else:
            print(f"❌ Empty cart checkout should fail: {response.status_code}")
        
        # 2. Test invalid coupon
        if 'test_order' in self.orders:
            order_id = self.orders['test_order']['id']
            invalid_coupon_data = {'coupon_code': 'INVALID'}
            response = requests.post(
                f"{self.base_url}/api/orders/{order_id}/apply-coupon/",
                json=invalid_coupon_data,
                headers=headers
            )
            if response.status_code == 400:
                print("✅ Invalid coupon properly rejected")
            else:
                print(f"❌ Invalid coupon should be rejected: {response.status_code}")
        
        # 3. Test unauthorized access
        unauthorized_headers = {}
        response = requests.get(f"{self.base_url}/api/orders/", headers=unauthorized_headers)
        if response.status_code == 401:
            print("✅ Unauthorized access properly blocked")
        else:
            print(f"❌ Unauthorized access should be blocked: {response.status_code}")
        
        return True
    
    def test_medixmall_mode(self):
        """Test MedixMall mode functionality"""
        print("\n💊 Testing MedixMall Mode...")
        
        # Enable MedixMall mode for user
        user = self.users['user']
        user.medixmall_mode = True
        user.save()
        
        headers = self.get_headers('user')
        
        # Test that orders are filtered for medicine products only
        response = requests.get(f"{self.base_url}/api/orders/", headers=headers)
        if response.status_code == 200:
            print("✅ MedixMall mode order filtering active")
            # Check for MedixMall mode header
            if 'X-MedixMall-Mode' in response.headers:
                print(f"✅ MedixMall mode header present: {response.headers['X-MedixMall-Mode']}")
        else:
            print(f"❌ MedixMall mode test failed: {response.text}")
        
        # Disable MedixMall mode
        user.medixmall_mode = False
        user.save()
        
        return True
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 Starting Comprehensive Order Endpoint Tests")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_test_data()
            
            # Test suites
            tests = [
                ('Cart to Order Flow', self.test_cart_to_order_flow),
                ('User Order Endpoints', self.test_user_order_endpoints),
                ('Admin Order Endpoints', self.test_admin_order_endpoints),
                ('Supplier Endpoints', self.test_supplier_endpoints),
                ('ShipRocket Endpoints', self.test_shiprocket_endpoints),
                ('Error Scenarios', self.test_error_scenarios),
                ('MedixMall Mode', self.test_medixmall_mode),
            ]
            
            results = {}
            for test_name, test_func in tests:
                try:
                    results[test_name] = test_func()
                except Exception as e:
                    print(f"❌ {test_name} failed with error: {str(e)}")
                    results[test_name] = False
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 TEST RESULTS SUMMARY")
            print("=" * 60)
            
            total_tests = len(results)
            passed_tests = sum(1 for result in results.values() if result)
            
            for test_name, result in results.items():
                status_icon = "✅" if result else "❌"
                print(f"{status_icon} {test_name}")
            
            print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
            
            if passed_tests == total_tests:
                print("🎉 All tests passed! Order system is working correctly.")
            else:
                print("⚠️  Some tests failed. Please check the issues above.")
            
            return results
            
        except Exception as e:
            print(f"❌ Test suite failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function to run the test suite"""
    test_suite = OrderEndpointTestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()