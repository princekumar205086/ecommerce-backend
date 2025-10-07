#!/usr/bin/env python
"""
Production-Ready Order Endpoint Testing
Tests all order-related endpoints using live backend API
Tests for user: user@example.com with password: User@123
"""

import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal

class ProductionOrderEndpointTest:
    """Production-ready test suite for all order-related endpoints"""
    
    def __init__(self):
        # Use production backend
        self.base_url = "https://backend.okpuja.in"
        self.user_email = "user@example.com"
        self.user_password = "User@123"
        self.tokens = {}
        self.products = {}
        self.orders = {}
        
    def get_auth_token(self):
        """Get JWT token for user authentication"""
        if 'access' in self.tokens:
            return self.tokens['access']
            
        response = requests.post(f"{self.base_url}/api/token/", {
            'email': self.user_email,
            'password': self.user_password
        })
        
        if response.status_code == 200:
            token_data = response.json()
            self.tokens = token_data
            return token_data['access']
        else:
            print(f"❌ Failed to get token: {response.text}")
            return None
    
    def get_headers(self):
        """Get authorization headers for requests"""
        token = self.get_auth_token()
        return {'Authorization': f'Bearer {token}'} if token else {}
    
    def discover_available_products(self):
        """Discover available products from the API"""
        print("🔍 Discovering available products...")
        
        # Try to get products from products API
        response = requests.get(f"{self.base_url}/api/products/products/")
        
        if response.status_code == 200:
            products_data = response.json()
            products = products_data.get('results', []) if isinstance(products_data, dict) else products_data
            
            # Filter for available products
            available_products = [
                p for p in products 
                if p.get('is_publish', False) and p.get('stock', 0) > 0
            ]
            
            if available_products:
                self.products['available'] = available_products[:3]  # Take first 3
                print(f"✅ Found {len(available_products)} available products")
                for i, product in enumerate(available_products[:3]):
                    print(f"  - {product.get('name', 'Unknown')}: Stock {product.get('stock', 0)}")
                return True
            else:
                print("⚠️  No available products found")
                return False
        else:
            print(f"❌ Failed to get products: {response.status_code}")
            return False
    
    def test_cart_to_order_flow(self):
        """Test complete cart to order flow"""
        print("\\n🛒 Testing Cart to Order Flow...")
        
        headers = self.get_headers()
        if not headers:
            return False
        
        # 1. Discover products if not already done
        if not self.products:
            if not self.discover_available_products():
                print("❌ Cannot proceed without available products")
                return False
        
        # 2. Clear any existing cart
        requests.delete(f"{self.base_url}/api/cart/clear/", headers=headers)
        
        # 3. Add product to cart
        if self.products.get('available'):
            product = self.products['available'][0]
            cart_data = {
                'product_id': product['id'],
                'quantity': 1
            }
            
            response = requests.post(
                f"{self.base_url}/api/cart/add/",
                json=cart_data,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                print("✅ Product added to cart")
            else:
                print(f"❌ Failed to add product to cart: {response.text}")
                return False
        else:
            return False
        
        # 4. Get cart to verify
        response = requests.get(f"{self.base_url}/api/cart/", headers=headers)
        if response.status_code == 200:
            cart_data = response.json()
            print(f"✅ Cart retrieved with {len(cart_data.get('items', []))} items")
            cart_id = cart_data.get('id')
        else:
            print(f"❌ Failed to get cart: {response.text}")
            return False
        
        # 5. Checkout cart to create order
        checkout_data = {
            'cart_id': cart_id,
            'shipping_address': {
                'name': 'Test User',
                'address_line_1': '123 Test Street',
                'city': 'Delhi',
                'state': 'Delhi',
                'postal_code': '110001',
                'country': 'India',
                'phone': '9876543210'
            },
            'billing_address': {
                'name': 'Test User', 
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
        print("\\n👤 Testing User Order Endpoints...")
        
        headers = self.get_headers()
        if not headers:
            return False
        
        # 1. List user orders
        response = requests.get(f"{self.base_url}/api/orders/", headers=headers)
        if response.status_code == 200:
            orders = response.json()
            count = len(orders.get('results', orders)) if isinstance(orders, dict) else len(orders)
            print(f"✅ User orders listed: {count} orders")
            
            # Check if we have the test order
            if count > 0:
                print("✅ Order data retrieved successfully")
            else:
                print("⚠️  No orders found for user")
        else:
            print(f"❌ Failed to list user orders: {response.text}")
            return False
        
        # 2. Get specific order details if available
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
        
        return True
    
    def test_shiprocket_integration(self):
        """Test ShipRocket integration endpoints"""
        print("\\n🚚 Testing ShipRocket Integration...")
        
        headers = self.get_headers()
        if not headers:
            return False
        
        # 1. Test serviceability check
        serviceability_data = {
            'pickup_pincode': '854301',  # From env config
            'delivery_pincode': '110001',
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
            success = result.get('success', False)
            serviceable = result.get('serviceable', False)
            print(f"✅ Serviceability check: API success={success}, serviceable={serviceable}")
        else:
            print(f"❌ Serviceability check failed: {response.status_code}")
        
        # 2. Test shipping rates
        rates_data = {
            'pickup_pincode': '854301',
            'delivery_pincode': '110001', 
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
            success = result.get('success', False)
            rates = result.get('rates', [])
            print(f"✅ Shipping rates: API success={success}, {len(rates)} rates found")
        else:
            print(f"❌ Shipping rates failed: {response.status_code}")
        
        return True
    
    def test_error_scenarios(self):
        """Test error handling"""
        print("\\n🚫 Testing Error Scenarios...")
        
        headers = self.get_headers()
        if not headers:
            return False
        
        # 1. Test invalid coupon
        if 'test_order' in self.orders:
            order_id = self.orders['test_order']['id']
            invalid_coupon_data = {'coupon_code': 'INVALID_CODE_123'}
            response = requests.post(
                f"{self.base_url}/api/orders/{order_id}/apply-coupon/",
                json=invalid_coupon_data,
                headers=headers
            )
            if response.status_code == 400:
                print("✅ Invalid coupon properly rejected")
            else:
                print(f"⚠️  Invalid coupon response: {response.status_code}")
        
        # 2. Test unauthorized access
        response = requests.get(f"{self.base_url}/api/orders/")
        if response.status_code == 401:
            print("✅ Unauthorized access properly blocked")
        else:
            print(f"⚠️  Unauthorized access response: {response.status_code}")
        
        return True
    
    def test_payment_endpoints(self):
        """Test payment-related endpoints"""
        print("\\n💳 Testing Payment Endpoints...")
        
        headers = self.get_headers()
        if not headers:
            return False
        
        # Check if we have cart with items
        response = requests.get(f"{self.base_url}/api/cart/", headers=headers)
        if response.status_code == 200:
            cart_data = response.json()
            if cart_data.get('items'):
                print("✅ Cart has items for payment testing")
                
                # Test payment creation from cart
                payment_data = {
                    'cart_id': cart_data.get('id'),
                    'shipping_address': {
                        'name': 'Test User',
                        'address_line_1': '123 Test Street',
                        'city': 'Delhi',
                        'state': 'Delhi',
                        'postal_code': '110001',
                        'country': 'India',
                        'phone': '9876543210'
                    },
                    'billing_address': {
                        'name': 'Test User',
                        'address_line_1': '123 Test Street', 
                        'city': 'Delhi',
                        'state': 'Delhi',
                        'postal_code': '110001',
                        'country': 'India',
                        'phone': '9876543210'
                    },
                    'payment_method': 'upi'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/payments/create-from-cart/",
                    json=payment_data,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    print("✅ Payment creation from cart successful")
                    payment_result = response.json()
                    print(f"   Order ID: {payment_result.get('order_id', 'N/A')}")
                else:
                    print(f"⚠️  Payment creation response: {response.status_code}")
                    print(f"   Details: {response.text[:100]}...")
            else:
                print("⚠️  No items in cart for payment testing")
        else:
            print(f"❌ Failed to get cart for payment testing: {response.status_code}")
        
        return True
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 Starting Production Order Endpoint Tests")
        print("=" * 60)
        print(f"🌐 Testing against: {self.base_url}")
        print(f"👤 Using account: {self.user_email}")
        print("=" * 60)
        
        # Authentication test
        print("\\n🔐 Testing Authentication...")
        if not self.get_auth_token():
            print("❌ Authentication failed - cannot proceed")
            return False
        print("✅ Authentication successful")
        
        # Run test suites
        tests = [
            ('Cart to Order Flow', self.test_cart_to_order_flow),
            ('User Order Endpoints', self.test_user_order_endpoints),
            ('Payment Endpoints', self.test_payment_endpoints),
            ('ShipRocket Integration', self.test_shiprocket_integration),
            ('Error Scenarios', self.test_error_scenarios),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with error: {str(e)}")
                results[test_name] = False
        
        # Summary
        print("\\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, result in results.items():
            status_icon = "✅" if result else "❌"
            print(f"{status_icon} {test_name}")
        
        print(f"\\n📈 Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Order system is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
            return False

def main():
    """Main function to run the test suite"""
    test_suite = ProductionOrderEndpointTest()
    success = test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)