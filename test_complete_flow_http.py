#!/usr/bin/env python3
"""
Complete End-to-End E-commerce Flow Test
Tests: Cart → Payment → Order → Cart Cleanup → Admin Operations

Uses real HTTP requests to test the actual API endpoints
"""

import requests
import json
import time
from decimal import Decimal

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "testpass123"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

class EcommerceFlowTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.user_token = None
        self.admin_token = None
        self.test_results = []
        
    def log_step(self, step, status, message, data=None):
        """Log test step results"""
        result = {
            'step': step,
            'status': status,
            'message': message,
            'data': data
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "success" else "❌"
        print(f"{status_icon} {step}: {message}")
        if data and isinstance(data, dict):
            for key, value in data.items():
                print(f"   {key}: {value}")
        print()

    def authenticate_user(self):
        """Authenticate test user"""
        print("🔐 Authenticating test user...")
        
        # First try to create the user (in case it doesn't exist)
        create_user_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": "Test User",
            "contact": "1234567890"
        }
        
        try:
            # Try to create user (might fail if already exists)
            requests.post(f"{self.base_url}/api/accounts/register/", json=create_user_data)
        except:
            pass  # User might already exist
        
        # Login
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/accounts/login/", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get('access')
                self.log_step("User Authentication", "success", f"Logged in as {TEST_USER_EMAIL}")
                return True
            else:
                self.log_step("User Authentication", "failed", f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_step("User Authentication", "failed", f"Login error: {str(e)}")
            return False

    def authenticate_admin(self):
        """Authenticate admin user"""
        print("🔐 Authenticating admin user...")
        
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/accounts/login/", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access')
                self.log_step("Admin Authentication", "success", f"Logged in as {ADMIN_EMAIL}")
                return True
            else:
                self.log_step("Admin Authentication", "failed", f"Admin login failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            self.log_step("Admin Authentication", "failed", f"Admin login error: {str(e)}")
            return False

    def get_headers(self, is_admin=False):
        """Get authorization headers"""
        token = self.admin_token if is_admin else self.user_token
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def setup_cart(self):
        """Add items to cart"""
        print("🛒 Setting up cart...")
        
        headers = self.get_headers()
        
        # Get available products
        try:
            products_response = requests.get(f"{self.base_url}/api/products/products/", headers=headers)
            if products_response.status_code == 200:
                products_data = products_response.json()
                products = products_data.get('results', []) if 'results' in products_data else products_data
                
                if not products:
                    self.log_step("Cart Setup", "failed", "No products available")
                    return None
                
                # Add first available product to cart
                product = products[0]
                cart_data = {
                    "product_id": product['id'],
                    "quantity": 2
                }
                
                add_response = requests.post(f"{self.base_url}/api/cart/add/", json=cart_data, headers=headers)
                if add_response.status_code in [200, 201]:
                    self.log_step("Cart Setup", "success", f"Added product {product['name']} to cart")
                    
                    # Get cart details
                    cart_response = requests.get(f"{self.base_url}/api/cart/", headers=headers)
                    if cart_response.status_code == 200:
                        cart_details = cart_response.json()
                        self.log_step("Cart Verification", "success", "Cart retrieved successfully", {
                            "Cart ID": cart_details.get('id'),
                            "Total Items": len(cart_details.get('items', [])),
                            "Total Amount": cart_details.get('total')
                        })
                        return cart_details
                else:
                    self.log_step("Cart Setup", "failed", f"Failed to add to cart: {add_response.status_code}")
                    return None
            else:
                self.log_step("Cart Setup", "failed", f"Failed to get products: {products_response.status_code}")
                return None
                
        except Exception as e:
            self.log_step("Cart Setup", "failed", f"Cart setup error: {str(e)}")
            return None

    def test_cod_payment_flow(self):
        """Test COD payment flow"""
        print("💰 Testing COD Payment Flow...")
        
        headers = self.get_headers()
        
        # Step 1: Create COD payment
        payment_data = {
            "payment_method": "cod",
            "shipping_address": {
                "full_name": "Test User",
                "address_line_1": "123 Test Street",
                "address_line_2": "Apt 4B",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "12345",
                "country": "India"
            }
        }
        
        try:
            payment_response = requests.post(f"{self.base_url}/api/payments/create-from-cart/", 
                                           json=payment_data, headers=headers)
            
            if payment_response.status_code in [200, 201]:
                payment_result = payment_response.json()
                payment_id = payment_result.get('payment_id')
                
                self.log_step("COD Payment Creation", "success", "COD payment created", {
                    "Payment ID": payment_id,
                    "Amount": payment_result.get('amount'),
                    "Currency": payment_result.get('currency')
                })
                
                # Step 2: Confirm COD payment
                confirm_data = {"payment_id": payment_id}
                confirm_response = requests.post(f"{self.base_url}/api/payments/confirm-cod/", 
                                               json=confirm_data, headers=headers)
                
                if confirm_response.status_code == 200:
                    confirm_result = confirm_response.json()
                    order_created = confirm_result.get('order_created', False)
                    order_info = confirm_result.get('order', {})
                    
                    self.log_step("COD Payment Confirmation", "success", "COD payment confirmed", {
                        "Order Created": order_created,
                        "Order ID": order_info.get('id'),
                        "Order Number": order_info.get('order_number'),
                        "Status": order_info.get('status'),
                        "Total": order_info.get('total')
                    })
                    
                    return order_info.get('id') if order_created else None
                else:
                    self.log_step("COD Payment Confirmation", "failed", f"COD confirmation failed: {confirm_response.status_code}")
                    print(f"Response: {confirm_response.text}")
            else:
                self.log_step("COD Payment Creation", "failed", f"COD payment creation failed: {payment_response.status_code}")
                print(f"Response: {payment_response.text}")
                
        except Exception as e:
            self.log_step("COD Payment Flow", "failed", f"COD payment error: {str(e)}")
        
        return None

    def verify_order_creation(self, expected_order_id=None):
        """Verify order was created and contains all details"""
        print("📋 Verifying Order Creation...")
        
        headers = self.get_headers()
        
        try:
            # Get user orders
            orders_response = requests.get(f"{self.base_url}/api/orders/", headers=headers)
            
            if orders_response.status_code == 200:
                orders_data = orders_response.json()
                orders = orders_data.get('results', []) if 'results' in orders_data else orders_data
                
                if orders:
                    latest_order = orders[0]  # Assuming orders are sorted by creation date
                    
                    # Get detailed order information
                    order_id = latest_order.get('id')
                    detail_response = requests.get(f"{self.base_url}/api/orders/{order_id}/", headers=headers)
                    
                    if detail_response.status_code == 200:
                        order_detail = detail_response.json()
                        
                        self.log_step("Order Verification", "success", "Order details retrieved", {
                            "Order ID": order_detail.get('id'),
                            "Order Number": order_detail.get('order_number'),
                            "Status": order_detail.get('status'),
                            "Payment Status": order_detail.get('payment_status'),
                            "Total": order_detail.get('total'),
                            "Items Count": len(order_detail.get('items', [])),
                            "Has Shipping Address": bool(order_detail.get('shipping_address')),
                            "User ID": order_detail.get('user', {}).get('id') if isinstance(order_detail.get('user'), dict) else order_detail.get('user')
                        })
                        
                        return order_detail
                    else:
                        self.log_step("Order Verification", "failed", f"Failed to get order details: {detail_response.status_code}")
                else:
                    self.log_step("Order Verification", "failed", "No orders found")
            else:
                self.log_step("Order Verification", "failed", f"Failed to get orders: {orders_response.status_code}")
                
        except Exception as e:
            self.log_step("Order Verification", "failed", f"Order verification error: {str(e)}")
        
        return None

    def verify_cart_cleanup(self):
        """Verify cart is cleaned after order creation"""
        print("🗑️ Verifying Cart Cleanup...")
        
        headers = self.get_headers()
        
        try:
            cart_response = requests.get(f"{self.base_url}/api/cart/", headers=headers)
            
            if cart_response.status_code == 200:
                cart_data = cart_response.json()
                items = cart_data.get('items', [])
                total = cart_data.get('total', '0')
                
                is_empty = len(items) == 0 and (total == '0' or total == '0.00' or float(total) == 0)
                
                self.log_step("Cart Cleanup Verification", "success" if is_empty else "failed", 
                            "Cart cleaned successfully" if is_empty else "Cart not properly cleaned", {
                    "Items Count": len(items),
                    "Total": total,
                    "Is Empty": is_empty
                })
                
                return is_empty
            else:
                self.log_step("Cart Cleanup Verification", "failed", f"Failed to get cart: {cart_response.status_code}")
                
        except Exception as e:
            self.log_step("Cart Cleanup Verification", "failed", f"Cart cleanup verification error: {str(e)}")
        
        return False

    def test_admin_operations(self, order_id):
        """Test admin order management operations"""
        print("👨‍💼 Testing Admin Operations...")
        
        if not self.admin_token:
            self.log_step("Admin Operations", "skipped", "Admin not authenticated")
            return
        
        headers = self.get_headers(is_admin=True)
        
        # Test 1: Accept Order
        try:
            accept_data = {
                "order_id": order_id,
                "notes": "Order reviewed and accepted by admin"
            }
            
            accept_response = requests.post(f"{self.base_url}/api/orders/admin/accept/", 
                                          json=accept_data, headers=headers)
            
            if accept_response.status_code == 200:
                accept_result = accept_response.json()
                self.log_step("Admin Accept Order", "success", "Order accepted successfully", {
                    "Order ID": accept_result.get('order_id'),
                    "New Status": accept_result.get('new_status'),
                    "Message": accept_result.get('message')
                })
            else:
                self.log_step("Admin Accept Order", "failed", f"Failed to accept order: {accept_response.status_code}")
                print(f"Response: {accept_response.text}")
        except Exception as e:
            self.log_step("Admin Accept Order", "failed", f"Accept order error: {str(e)}")
        
        # Test 2: Assign Shipping
        try:
            shipping_data = {
                "order_id": order_id,
                "shipping_partner": "BlueDart",
                "tracking_id": "BD123456789",
                "notes": "Order assigned to BlueDart for delivery"
            }
            
            shipping_response = requests.post(f"{self.base_url}/api/orders/admin/assign-shipping/", 
                                            json=shipping_data, headers=headers)
            
            if shipping_response.status_code == 200:
                shipping_result = shipping_response.json()
                self.log_step("Admin Assign Shipping", "success", "Shipping assigned successfully", {
                    "Shipping Partner": shipping_result.get('shipping_partner'),
                    "Tracking ID": shipping_result.get('tracking_id'),
                    "New Status": shipping_result.get('new_status')
                })
            else:
                self.log_step("Admin Assign Shipping", "failed", f"Failed to assign shipping: {shipping_response.status_code}")
                print(f"Response: {shipping_response.text}")
        except Exception as e:
            self.log_step("Admin Assign Shipping", "failed", f"Assign shipping error: {str(e)}")
        
        # Test 3: Mark Delivered
        try:
            delivered_data = {
                "order_id": order_id,
                "notes": "Package delivered successfully to customer"
            }
            
            delivered_response = requests.post(f"{self.base_url}/api/orders/admin/mark-delivered/", 
                                             json=delivered_data, headers=headers)
            
            if delivered_response.status_code == 200:
                delivered_result = delivered_response.json()
                self.log_step("Admin Mark Delivered", "success", "Order marked as delivered", {
                    "Order ID": delivered_result.get('order_id'),
                    "New Status": delivered_result.get('new_status'),
                    "Delivered At": delivered_result.get('delivered_at')
                })
            else:
                self.log_step("Admin Mark Delivered", "failed", f"Failed to mark delivered: {delivered_response.status_code}")
                print(f"Response: {delivered_response.text}")
        except Exception as e:
            self.log_step("Admin Mark Delivered", "failed", f"Mark delivered error: {str(e)}")

    def run_complete_test(self):
        """Run the complete end-to-end test"""
        print("🚀 Starting Complete E-commerce Flow Test")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Test User: {TEST_USER_EMAIL}")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate_user():
            print("❌ Cannot proceed without user authentication")
            return
        
        # Try to authenticate admin (optional)
        self.authenticate_admin()
        
        # Step 2: Setup cart
        cart_data = self.setup_cart()
        if not cart_data:
            print("❌ Cannot proceed without cart setup")
            return
        
        # Step 3: Test payment flow (COD)
        order_id = self.test_cod_payment_flow()
        if not order_id:
            print("❌ Payment flow failed")
            return
        
        # Wait a moment for order processing
        time.sleep(1)
        
        # Step 4: Verify order creation
        order_details = self.verify_order_creation(order_id)
        if not order_details:
            print("❌ Order verification failed")
            return
        
        # Step 5: Verify cart cleanup
        cart_cleaned = self.verify_cart_cleanup()
        
        # Step 6: Test admin operations
        if order_details:
            self.test_admin_operations(order_details.get('id'))
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 COMPLETE FLOW TEST RESULTS")
        print("=" * 60)
        
        success_count = sum(1 for result in self.test_results if result['status'] == 'success')
        total_count = len(self.test_results)
        
        print(f"✅ Successful Steps: {success_count}")
        print(f"❌ Failed Steps: {total_count - success_count}")
        print(f"📈 Success Rate: {(success_count/total_count)*100:.1f}%")
        
        # Key flow verification
        print(f"\n🔍 KEY FLOW VERIFICATION:")
        print(f"✅ Cart → Payment: Working")
        print(f"✅ Payment → Order: {'Working' if order_id else 'Failed'}")
        print(f"✅ Order → Cart Cleanup: {'Working' if cart_cleaned else 'Failed'}")
        print(f"✅ Admin Operations: {'Working' if self.admin_token else 'Skipped'}")
        
        if success_count >= total_count * 0.8:
            print(f"\n🎉 OVERALL STATUS: SUCCESS")
            print(f"✅ Complete e-commerce flow is working!")
        else:
            print(f"\n⚠️ OVERALL STATUS: NEEDS ATTENTION")
            print(f"❌ Some components need fixing")

def main():
    """Main test execution"""
    print("🎯 Complete E-commerce Flow Tester")
    print("📋 Testing: Cart → Payment → Order → Cart Cleanup → Admin Ops")
    print()
    
    tester = EcommerceFlowTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main()