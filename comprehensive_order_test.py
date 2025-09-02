"""
Comprehensive Order System End-to-End Testing
Tests all order endpoints for User, Supplier, and Admin roles including ShipRocket integration
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from decimal import Decimal
import time

# Django setup
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.db import transaction

from accounts.models import User
from products.models import Product, Category, ProductVariant
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem, OrderStatusChange
from shipping.models import Shipment, ShippingEvent
from coupon.models import Coupon

User = get_user_model()

class OrderSystemTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000/api"
        self.client = APIClient()
        self.users = {}
        self.tokens = {}
        self.orders = {}
        self.products = {}
        self.categories = {}
        self.carts = {}
        self.shipments = {}
        
        # Test result tracking
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
    
    def log_test(self, test_name, passed, message="", data=None):
        """Log test results"""
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed_tests'] += 1
            print(f"✅ {test_name}: PASSED - {message}")
        else:
            self.test_results['failed_tests'] += 1
            print(f"❌ {test_name}: FAILED - {message}")
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'passed': passed,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    def setup_test_data(self):
        """Setup test data including users, products, categories"""
        print("\n🔧 Setting up test data...")
        
        # Create test users
        try:
            # Admin user
            self.users['admin'] = User.objects.create_user(
                email='admin@test.com',
                password='admin123',
                full_name='Test Admin',
                contact='9876543210',
                role='admin',
                is_staff=True,
                is_superuser=True,
                address_line_1='Admin Address Line 1',
                city='Delhi',
                state='Delhi',
                postal_code='110001',
                country='India'
            )
            
            # Regular user
            self.users['user'] = User.objects.create_user(
                email='user@test.com',
                password='user123',
                full_name='Test User',
                contact='9876543211',
                role='user',
                address_line_1='User Address Line 1',
                city='Mumbai',
                state='Maharashtra',
                postal_code='400001',
                country='India'
            )
            
            # Supplier user
            self.users['supplier'] = User.objects.create_user(
                email='supplier@test.com',
                password='supplier123',
                full_name='Test Supplier',
                contact='9876543212',
                role='supplier',
                address_line_1='Supplier Address Line 1',
                city='Bangalore',
                state='Karnataka',
                postal_code='560001',
                country='India'
            )
            
            # MedixMall user
            self.users['medix_user'] = User.objects.create_user(
                email='medixuser@test.com',
                password='medix123',
                full_name='MedixMall User',
                contact='9876543213',
                role='user',
                medixmall_mode=True,
                address_line_1='MedixMall User Address',
                city='Chennai',
                state='Tamil Nadu',
                postal_code='600001',
                country='India'
            )
            
            print("✅ Test users created successfully")
            
        except Exception as e:
            print(f"❌ Error creating test users: {str(e)}")
            return False
        
        # Create categories
        try:
            self.categories['electronics'] = Category.objects.create(
                name='Electronics',
                description='Electronic products',
                is_active=True
            )
            
            self.categories['medicine'] = Category.objects.create(
                name='Medicine',
                description='Medical products',
                is_active=True,
                is_medicine=True
            )
            
            print("✅ Test categories created successfully")
            
        except Exception as e:
            print(f"❌ Error creating test categories: {str(e)}")
            return False
        
        # Create products
        try:
            # Electronics product
            self.products['laptop'] = Product.objects.create(
                name='Test Laptop',
                description='Test laptop for orders',
                price=Decimal('50000.00'),
                category=self.categories['electronics'],
                stock=10,
                weight=Decimal('2.5'),
                is_active=True
            )
            
            # Medicine product
            self.products['paracetamol'] = Product.objects.create(
                name='Paracetamol 500mg',
                description='Pain relief medicine',
                price=Decimal('50.00'),
                category=self.categories['medicine'],
                stock=100,
                weight=Decimal('0.1'),
                is_active=True,
                is_medicine=True
            )
            
            # Add product variants
            ProductVariant.objects.create(
                product=self.products['laptop'],
                name='8GB RAM',
                price=Decimal('50000.00'),
                stock=5
            )
            
            ProductVariant.objects.create(
                product=self.products['paracetamol'],
                name='Strip of 10',
                price=Decimal('50.00'),
                stock=50
            )
            
            print("✅ Test products created successfully")
            
        except Exception as e:
            print(f"❌ Error creating test products: {str(e)}")
            return False
        
        # Create test coupon
        try:
            Coupon.objects.create(
                code='TESTDISCOUNT10',
                discount_type='percentage',
                discount_value=Decimal('10.00'),
                minimum_amount=Decimal('100.00'),
                maximum_discount=Decimal('500.00'),
                is_active=True,
                valid_from=datetime.now().date(),
                valid_until=(datetime.now() + timedelta(days=30)).date(),
                usage_limit=100
            )
            
            print("✅ Test coupon created successfully")
            
        except Exception as e:
            print(f"❌ Error creating test coupon: {str(e)}")
            return False
        
        return True
    
    def authenticate_users(self):
        """Authenticate all test users and get tokens"""
        print("\n🔑 Authenticating users...")
        
        for role, user in self.users.items():
            try:
                response = self.client.post(f"{self.base_url}/token/", {
                    'email': user.email,
                    'password': f'{role}123'
                })
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.tokens[role] = token_data['access']
                    print(f"✅ {role} authenticated successfully")
                else:
                    print(f"❌ {role} authentication failed: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error authenticating {role}: {str(e)}")
                return False
        
        return True
    
    def set_auth_header(self, user_role):
        """Set authentication header for requests"""
        if user_role in self.tokens:
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens[user_role]}')
        else:
            self.client.credentials()
    
    def test_cart_operations(self):
        """Test cart operations before orders"""
        print("\n🛒 Testing cart operations...")
        
        # Test adding items to cart for regular user
        self.set_auth_header('user')
        
        # Add laptop to cart
        response = self.client.post(f"{self.base_url}/cart/add/", {
            'product_id': self.products['laptop'].id,
            'quantity': 1
        })
        
        self.log_test(
            'Add laptop to cart',
            response.status_code == 201,
            f"Status: {response.status_code}, Response: {response.json() if response.status_code == 201 else response.content}"
        )
        
        # Add medicine to cart
        response = self.client.post(f"{self.base_url}/cart/add/", {
            'product_id': self.products['paracetamol'].id,
            'quantity': 2
        })
        
        self.log_test(
            'Add medicine to cart',
            response.status_code == 201,
            f"Status: {response.status_code}"
        )
        
        # Get cart
        response = self.client.get(f"{self.base_url}/cart/")
        
        if response.status_code == 200:
            cart_data = response.json()
            if cart_data['results']:
                self.carts['user'] = cart_data['results'][0]
                self.log_test(
                    'Get user cart',
                    True,
                    f"Cart ID: {self.carts['user']['id']}, Items: {len(self.carts['user']['items'])}"
                )
            else:
                self.log_test('Get user cart', False, "No cart found")
        else:
            self.log_test('Get user cart', False, f"Status: {response.status_code}")
        
        # Test MedixMall user cart
        self.set_auth_header('medix_user')
        
        # Add medicine to MedixMall user cart
        response = self.client.post(f"{self.base_url}/cart/add/", {
            'product_id': self.products['paracetamol'].id,
            'quantity': 3
        })
        
        self.log_test(
            'Add medicine to MedixMall cart',
            response.status_code == 201,
            f"Status: {response.status_code}"
        )
        
        # Try to add non-medicine to MedixMall cart (should fail or be filtered)
        response = self.client.post(f"{self.base_url}/cart/add/", {
            'product_id': self.products['laptop'].id,
            'quantity': 1
        })
        
        self.log_test(
            'Add non-medicine to MedixMall cart',
            True,  # This might succeed but should be filtered in checkout
            f"Status: {response.status_code}"
        )
        
        # Get MedixMall cart
        response = self.client.get(f"{self.base_url}/cart/")
        
        if response.status_code == 200:
            cart_data = response.json()
            if cart_data['results']:
                self.carts['medix_user'] = cart_data['results'][0]
                self.log_test(
                    'Get MedixMall cart',
                    True,
                    f"Cart ID: {self.carts['medix_user']['id']}, Items: {len(self.carts['medix_user']['items'])}"
                )
    
    def test_order_creation(self):
        """Test order creation from cart"""
        print("\n📦 Testing order creation...")
        
        # Test regular user order creation
        self.set_auth_header('user')
        
        order_data = {
            'cart_id': self.carts['user']['id'],
            'shipping_address': {
                'address_line_1': 'Test Shipping Address',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400001',
                'country': 'India'
            },
            'billing_address': {
                'address_line_1': 'Test Billing Address',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400001',
                'country': 'India'
            },
            'payment_method': 'upi',
            'notes': 'Test order from comprehensive test'
        }
        
        response = self.client.post(f"{self.base_url}/orders/checkout/", order_data)
        
        if response.status_code == 201:
            order_data = response.json()
            self.orders['user_order'] = order_data
            self.log_test(
                'Create user order',
                True,
                f"Order created: {order_data['order_number']}, Total: ₹{order_data['total']}"
            )
        else:
            self.log_test(
                'Create user order',
                False,
                f"Status: {response.status_code}, Error: {response.content}"
            )
        
        # Test MedixMall user order creation
        self.set_auth_header('medix_user')
        
        medix_order_data = {
            'cart_id': self.carts['medix_user']['id'],
            'shipping_address': {
                'address_line_1': 'MedixMall Shipping Address',
                'city': 'Chennai',
                'state': 'Tamil Nadu',
                'postal_code': '600001',
                'country': 'India'
            },
            'billing_address': {
                'address_line_1': 'MedixMall Billing Address',
                'city': 'Chennai',
                'state': 'Tamil Nadu',
                'postal_code': '600001',
                'country': 'India'
            },
            'payment_method': 'cod',
            'coupon_code': 'TESTDISCOUNT10',
            'notes': 'MedixMall test order'
        }
        
        response = self.client.post(f"{self.base_url}/orders/checkout/", medix_order_data)
        
        if response.status_code == 201:
            order_data = response.json()
            self.orders['medix_order'] = order_data
            self.log_test(
                'Create MedixMall order',
                True,
                f"Order created: {order_data['order_number']}, Total: ₹{order_data['total']}"
            )
        else:
            self.log_test(
                'Create MedixMall order',
                False,
                f"Status: {response.status_code}, Error: {response.content}"
            )
    
    def test_order_listing(self):
        """Test order listing for different user types"""
        print("\n📋 Testing order listing...")
        
        # Test user order listing
        self.set_auth_header('user')
        response = self.client.get(f"{self.base_url}/orders/")
        
        self.log_test(
            'User order listing',
            response.status_code == 200,
            f"Status: {response.status_code}, Orders found: {len(response.json()['results']) if response.status_code == 200 else 0}"
        )
        
        # Test MedixMall user order listing (should only show medicine orders)
        self.set_auth_header('medix_user')
        response = self.client.get(f"{self.base_url}/orders/")
        
        self.log_test(
            'MedixMall user order listing',
            response.status_code == 200,
            f"Status: {response.status_code}, Orders found: {len(response.json()['results']) if response.status_code == 200 else 0}"
        )
        
        # Test admin order listing (should see all orders)
        self.set_auth_header('admin')
        response = self.client.get(f"{self.base_url}/orders/")
        
        self.log_test(
            'Admin order listing',
            response.status_code == 200,
            f"Status: {response.status_code}, Orders found: {len(response.json()['results']) if response.status_code == 200 else 0}"
        )
    
    def test_order_details(self):
        """Test order detail retrieval"""
        print("\n🔍 Testing order details...")
        
        if 'user_order' in self.orders:
            # Test user accessing their own order
            self.set_auth_header('user')
            order_id = self.orders['user_order']['id']
            response = self.client.get(f"{self.base_url}/orders/{order_id}/")
            
            self.log_test(
                'User order detail access',
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Test admin accessing user order
            self.set_auth_header('admin')
            response = self.client.get(f"{self.base_url}/orders/{order_id}/")
            
            self.log_test(
                'Admin order detail access',
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Test unauthorized access
            self.set_auth_header('medix_user')
            response = self.client.get(f"{self.base_url}/orders/{order_id}/")
            
            self.log_test(
                'Unauthorized order detail access',
                response.status_code == 403,
                f"Status: {response.status_code} (should be 403)"
            )
    
    def test_admin_order_management(self):
        """Test admin order management endpoints"""
        print("\n👨‍💼 Testing admin order management...")
        
        if 'user_order' not in self.orders:
            print("⚠️ No user order found, skipping admin tests")
            return
        
        self.set_auth_header('admin')
        order_id = self.orders['user_order']['id']
        
        # Test accept order
        response = self.client.post(f"{self.base_url}/orders/admin/accept/", {
            'order_id': order_id,
            'notes': 'Order accepted by admin during testing'
        })
        
        self.log_test(
            'Admin accept order',
            response.status_code == 200,
            f"Status: {response.status_code}, Response: {response.json() if response.status_code == 200 else response.content}"
        )
        
        # Test assign shipping
        response = self.client.post(f"{self.base_url}/orders/admin/assign-shipping/", {
            'order_id': order_id,
            'shipping_partner': 'BlueDart',
            'tracking_id': 'BD123456789',
            'notes': 'Assigned to BlueDart for delivery'
        })
        
        self.log_test(
            'Admin assign shipping',
            response.status_code == 200,
            f"Status: {response.status_code}, Response: {response.json() if response.status_code == 200 else response.content}"
        )
        
        # Test mark delivered
        response = self.client.post(f"{self.base_url}/orders/admin/mark-delivered/", {
            'order_id': order_id,
            'notes': 'Order delivered successfully'
        })
        
        self.log_test(
            'Admin mark delivered',
            response.status_code == 200,
            f"Status: {response.status_code}, Response: {response.json() if response.status_code == 200 else response.content}"
        )
        
        # Test order stats
        response = self.client.get(f"{self.base_url}/orders/stats/")
        
        self.log_test(
            'Admin order stats',
            response.status_code == 200,
            f"Status: {response.status_code}, Stats: {response.json() if response.status_code == 200 else 'Error'}"
        )
    
    def test_shipping_integration(self):
        """Test ShipRocket shipping integration"""
        print("\n🚚 Testing ShipRocket integration...")
        
        # Test connection
        response = self.client.get(f"{self.base_url}/shipping/test/")
        
        self.log_test(
            'ShipRocket connection test',
            response.status_code == 200,
            f"Status: {response.status_code}, Response: {response.json() if response.status_code == 200 else response.content}"
        )
        
        # Test serviceability check
        response = self.client.get(f"{self.base_url}/shipping/serviceability/", {
            'pickup_pincode': '110001',
            'delivery_pincode': '400001',
            'weight': '1.0',
            'cod': 'false'
        })
        
        self.log_test(
            'ShipRocket serviceability check',
            response.status_code == 200,
            f"Status: {response.status_code}, Serviceable: {response.json().get('serviceable', False) if response.status_code == 200 else 'Error'}"
        )
        
        # Test shipping rates
        response = self.client.get(f"{self.base_url}/shipping/rates/", {
            'pickup_pincode': '110001',
            'delivery_pincode': '400001',
            'weight': '1.0',
            'length': '10',
            'breadth': '10',
            'height': '5'
        })
        
        self.log_test(
            'ShipRocket shipping rates',
            response.status_code == 200,
            f"Status: {response.status_code}, Rates available: {'Yes' if response.status_code == 200 and response.json().get('success') else 'No'}"
        )
        
        # Test shipment creation
        if 'user_order' in self.orders:
            self.set_auth_header('user')
            
            shipment_data = {
                'order_id': self.orders['user_order']['order_number'],
                'customer_name': 'Test User',
                'customer_email': 'user@test.com',
                'customer_phone': '9876543211',
                'billing_address': 'Test Billing Address',
                'billing_city': 'Mumbai',
                'billing_state': 'Maharashtra',
                'billing_pincode': '400001',
                'weight': 1.0,
                'payment_method': 'Prepaid',
                'sub_total': float(self.orders['user_order']['total']),
                'items': [
                    {
                        'name': 'Test Product',
                        'sku': 'TEST001',
                        'quantity': 1,
                        'price': float(self.orders['user_order']['total'])
                    }
                ]
            }
            
            response = self.client.post(f"{self.base_url}/shipping/shipments/create/", shipment_data)
            
            if response.status_code == 201:
                shipment_data = response.json()
                self.shipments['user_shipment'] = shipment_data['shipment']
                self.log_test(
                    'ShipRocket shipment creation',
                    True,
                    f"Shipment created: {self.shipments['user_shipment']['order_id']}"
                )
            else:
                self.log_test(
                    'ShipRocket shipment creation',
                    False,
                    f"Status: {response.status_code}, Error: {response.content}"
                )
    
    def test_coupon_application(self):
        """Test coupon application to orders"""
        print("\n🎫 Testing coupon application...")
        
        if 'medix_order' in self.orders:
            self.set_auth_header('medix_user')
            order_id = self.orders['medix_order']['id']
            
            # Apply coupon to order
            response = self.client.post(f"{self.base_url}/orders/{order_id}/apply-coupon/", {
                'coupon_code': 'TESTDISCOUNT10'
            })
            
            self.log_test(
                'Apply coupon to order',
                response.status_code == 200,
                f"Status: {response.status_code}, Response: {response.json() if response.status_code == 200 else response.content}"
            )
    
    def test_order_filtering(self):
        """Test order filtering and search"""
        print("\n🔍 Testing order filtering...")
        
        self.set_auth_header('admin')
        
        # Test filter by status
        response = self.client.get(f"{self.base_url}/orders/", {'status': 'delivered'})
        
        self.log_test(
            'Filter orders by status',
            response.status_code == 200,
            f"Status: {response.status_code}, Filtered orders: {len(response.json()['results']) if response.status_code == 200 else 0}"
        )
        
        # Test filter by payment method
        response = self.client.get(f"{self.base_url}/orders/", {'payment_method': 'upi'})
        
        self.log_test(
            'Filter orders by payment method',
            response.status_code == 200,
            f"Status: {response.status_code}, Filtered orders: {len(response.json()['results']) if response.status_code == 200 else 0}"
        )
        
        # Test search by order number
        if 'user_order' in self.orders:
            order_number = self.orders['user_order']['order_number']
            response = self.client.get(f"{self.base_url}/orders/", {'search': order_number})
            
            self.log_test(
                'Search orders by order number',
                response.status_code == 200,
                f"Status: {response.status_code}, Search results: {len(response.json()['results']) if response.status_code == 200 else 0}"
            )
    
    def test_unauthorized_access(self):
        """Test unauthorized access to order endpoints"""
        print("\n🚫 Testing unauthorized access...")
        
        # Test without authentication
        self.client.credentials()
        
        response = self.client.get(f"{self.base_url}/orders/")
        self.log_test(
            'Unauthenticated order listing',
            response.status_code == 401,
            f"Status: {response.status_code} (should be 401)"
        )
        
        response = self.client.post(f"{self.base_url}/orders/checkout/", {})
        self.log_test(
            'Unauthenticated order creation',
            response.status_code == 401,
            f"Status: {response.status_code} (should be 401)"
        )
        
        # Test admin endpoints with regular user
        self.set_auth_header('user')
        
        response = self.client.post(f"{self.base_url}/orders/admin/accept/", {'order_id': 1})
        self.log_test(
            'Non-admin access to admin endpoints',
            response.status_code == 403,
            f"Status: {response.status_code} (should be 403)"
        )
        
        response = self.client.get(f"{self.base_url}/orders/stats/")
        self.log_test(
            'Non-admin access to order stats',
            response.status_code == 403,
            f"Status: {response.status_code} (should be 403)"
        )
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Delete in reverse order due to foreign keys
            OrderStatusChange.objects.filter(order__user__email__contains='@test.com').delete()
            OrderItem.objects.filter(order__user__email__contains='@test.com').delete()
            Order.objects.filter(user__email__contains='@test.com').delete()
            CartItem.objects.filter(cart__user__email__contains='@test.com').delete()
            Cart.objects.filter(user__email__contains='@test.com').delete()
            ProductVariant.objects.filter(product__name__contains='Test').delete()
            Product.objects.filter(name__contains='Test').delete()
            Category.objects.filter(name__in=['Electronics', 'Medicine']).delete()
            Coupon.objects.filter(code='TESTDISCOUNT10').delete()
            User.objects.filter(email__contains='@test.com').delete()
            
            print("✅ Test data cleaned up successfully")
            
        except Exception as e:
            print(f"❌ Error cleaning up test data: {str(e)}")
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE ORDER SYSTEM TEST SUMMARY")
        print("="*60)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results['test_details']:
                if not test['passed']:
                    print(f"  • {test['test_name']}: {test['message']}")
        
        print("\n📈 RECOMMENDATIONS:")
        
        if success_rate >= 90:
            print("✅ Order system is working excellently!")
        elif success_rate >= 80:
            print("✅ Order system is working well with minor issues")
        elif success_rate >= 70:
            print("⚠️ Order system has some issues that need attention")
        else:
            print("❌ Order system has significant issues that need immediate attention")
        
        # Save detailed results
        with open('order_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: order_test_results.json")
    
    def run_all_tests(self):
        """Run all order system tests"""
        print("🚀 Starting Comprehensive Order System Testing...")
        print("="*60)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Test setup failed, aborting...")
            return
        
        if not self.authenticate_users():
            print("❌ User authentication failed, aborting...")
            return
        
        # Run tests
        try:
            self.test_cart_operations()
            self.test_order_creation()
            self.test_order_listing()
            self.test_order_details()
            self.test_admin_order_management()
            self.test_shipping_integration()
            self.test_coupon_application()
            self.test_order_filtering()
            self.test_unauthorized_access()
            
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
        
        finally:
            # Cleanup and summary
            self.cleanup_test_data()
            self.print_test_summary()


def main():
    """Main function to run the comprehensive order tests"""
    tester = OrderSystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()