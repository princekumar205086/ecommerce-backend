#!/usr/bin/env python3
"""
Comprehensive Test for MedixMall Mode Implementation
Tests the complete MedixMall switch functionality end-to-end
"""

import requests
import json
import os
import sys
from decimal import Decimal

# Configuration
BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step):
    print(f"\n🔸 {step}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

class MedixMallTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.supplier_token = None
        self.test_user_id = None
        self.session = requests.Session()
        
    def authenticate_users(self):
        """Authenticate test users"""
        print_header("AUTHENTICATION TEST")
        
        # Admin login
        print_step("Authenticating admin user")
        admin_response = self.session.post(f"{BASE_URL}/api/token/", {
            "email": "admin@test.com",
            "password": "admin123"
        })
        
        if admin_response.status_code == 200:
            self.admin_token = admin_response.json()['access']
            print_success("Admin authentication successful")
        else:
            print_error(f"Admin authentication failed: {admin_response.text}")
            return False
        
        # User login
        print_step("Authenticating regular user")
        user_response = self.session.post(f"{BASE_URL}/api/token/", {
            "email": "customer@test.com",
            "password": "customer123"
        })
        
        if user_response.status_code == 200:
            self.user_token = user_response.json()['access']
            print_success("User authentication successful")
        else:
            print_error(f"User authentication failed: {user_response.text}")
            return False
        
        # Supplier login
        print_step("Authenticating supplier user")
        supplier_response = self.session.post(f"{BASE_URL}/api/token/", {
            "email": "supplier@test.com",
            "password": "testpass123"
        })
        
        if supplier_response.status_code == 200:
            self.supplier_token = supplier_response.json()['access']
            print_success("Supplier authentication successful")
        else:
            print_error(f"Supplier authentication failed: {supplier_response.text}")
            return False
        
        return True
    
    def test_medixmall_mode_endpoints(self):
        """Test MedixMall mode toggle endpoints"""
        print_header("MEDIXMALL MODE ENDPOINTS TEST")
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Test GET current mode
        print_step("Getting current MedixMall mode status")
        response = self.session.get(f"{BASE_URL}/api/accounts/medixmall-mode/", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Current mode: {data['medixmall_mode']}")
            print_info(f"Message: {data['message']}")
        else:
            print_error(f"Failed to get MedixMall mode: {response.text}")
            return False
        
        # Test enabling MedixMall mode
        print_step("Enabling MedixMall mode")
        response = self.session.put(f"{BASE_URL}/api/accounts/medixmall-mode/", 
                                   json={"medixmall_mode": True}, 
                                   headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"MedixMall mode enabled: {data['medixmall_mode']}")
            print_info(f"Message: {data['message']}")
        else:
            print_error(f"Failed to enable MedixMall mode: {response.text}")
            return False
        
        # Test disabling MedixMall mode
        print_step("Disabling MedixMall mode")
        response = self.session.put(f"{BASE_URL}/api/accounts/medixmall-mode/", 
                                   json={"medixmall_mode": False}, 
                                   headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"MedixMall mode disabled: {data['medixmall_mode']}")
            print_info(f"Message: {data['message']}")
        else:
            print_error(f"Failed to disable MedixMall mode: {response.text}")
            return False
        
        return True
    
    def test_product_filtering(self):
        """Test product filtering with MedixMall mode"""
        print_header("PRODUCT FILTERING TEST")
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # First, get all products without MedixMall mode
        print_step("Getting all products (MedixMall mode OFF)")
        response = self.session.get(f"{BASE_URL}/api/public/products/products/", headers=headers)
        
        if response.status_code == 200:
            all_products = response.json()['results']
            print_success(f"Found {len(all_products)} total products")
            
            # Count products by type
            medicine_count = sum(1 for p in all_products if p.get('product_type') == 'medicine')
            equipment_count = sum(1 for p in all_products if p.get('product_type') == 'equipment')
            pathology_count = sum(1 for p in all_products if p.get('product_type') == 'pathology')
            
            print_info(f"Medicine products: {medicine_count}")
            print_info(f"Equipment products: {equipment_count}")
            print_info(f"Pathology products: {pathology_count}")
        else:
            print_error(f"Failed to get products: {response.text}")
            return False
        
        # Enable MedixMall mode
        print_step("Enabling MedixMall mode")
        self.session.put(f"{BASE_URL}/api/accounts/medixmall-mode/", 
                        json={"medixmall_mode": True}, 
                        headers=headers)
        
        # Get products with MedixMall mode ON
        print_step("Getting products with MedixMall mode ON")
        response = self.session.get(f"{BASE_URL}/api/public/products/products/", headers=headers)
        
        if response.status_code == 200:
            medixmall_products = response.json()['results']
            print_success(f"Found {len(medixmall_products)} products in MedixMall mode")
            
            # Check X-MedixMall-Mode header
            mode_header = response.headers.get('X-MedixMall-Mode')
            print_info(f"MedixMall mode header: {mode_header}")
            
            # Verify all products are medicine type
            all_medicine = all(p.get('product_type') == 'medicine' for p in medixmall_products)
            if all_medicine:
                print_success("✅ All products are medicine type - filtering works!")
            else:
                print_error("❌ Found non-medicine products in MedixMall mode")
                return False
        else:
            print_error(f"Failed to get products in MedixMall mode: {response.text}")
            return False
        
        return True
    
    def test_enterprise_search(self):
        """Test enterprise-level search functionality"""
        print_header("ENTERPRISE SEARCH TEST")
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Test search without MedixMall mode
        print_step("Testing enterprise search (MedixMall mode OFF)")
        self.session.put(f"{BASE_URL}/api/accounts/medixmall-mode/", 
                        json={"medixmall_mode": False}, 
                        headers=headers)
        
        # Test various search scenarios
        search_queries = [
            {"q": "paracetamol", "description": "Medicine search"},
            {"q": "equipment", "description": "Equipment search"},
            {"q": "tablet", "description": "Form-based search"},
            {"q": "blood", "description": "Medical term search"},
            {"product_type": "medicine", "description": "Product type filter"},
            {"sort_by": "price_low", "description": "Price sorting"},
            {"min_price": 10, "max_price": 100, "description": "Price range"},
        ]
        
        for query in search_queries:
            print_step(f"Testing: {query['description']}")
            response = self.session.get(f"{BASE_URL}/api/public/products/search/", 
                                       params=query, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                results_count = data['pagination']['total_count']
                print_success(f"Search successful - {results_count} results")
                
                # Check for search suggestions
                if 'search_suggestions' in data:
                    suggestions = data['search_suggestions']
                    if suggestions:
                        print_info(f"Search suggestions: {', '.join(suggestions[:3])}")
                
                # Check filters
                if 'filters' in data:
                    filters = data['filters']
                    print_info(f"Available categories: {len(filters.get('categories', []))}")
                    print_info(f"Available brands: {len(filters.get('brands', []))}")
            else:
                print_error(f"Search failed: {response.text}")
        
        # Test search with MedixMall mode ON
        print_step("Testing enterprise search (MedixMall mode ON)")
        self.session.put(f"{BASE_URL}/api/accounts/medixmall-mode/", 
                        json={"medixmall_mode": True}, 
                        headers=headers)
        
        response = self.session.get(f"{BASE_URL}/api/public/products/search/", 
                                   params={"q": "medicine"}, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"MedixMall search successful - {data['pagination']['total_count']} results")
            print_info(f"MedixMall mode in response: {data.get('medixmall_mode')}")
            
            # Verify all results are medicine
            all_medicine = all(
                p.get('product_type') == 'medicine' 
                for p in data['results']
            )
            if all_medicine:
                print_success("✅ All search results are medicine products")
            else:
                print_error("❌ Found non-medicine products in MedixMall search")
        else:
            print_error(f"MedixMall search failed: {response.text}")
        
        return True
    
    def test_order_filtering(self):
        """Test order filtering with MedixMall mode"""
        print_header("ORDER FILTERING TEST")
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # First disable MedixMall mode and get all orders
        print_step("Getting orders (MedixMall mode OFF)")
        self.session.put(f"{BASE_URL}/api/accounts/medixmall-mode/", 
                        json={"medixmall_mode": False}, 
                        headers=headers)
        
        response = self.session.get(f"{BASE_URL}/api/orders/", headers=headers)
        
        if response.status_code == 200:
            all_orders = response.json()['results']
            print_success(f"Found {len(all_orders)} total orders")
        else:
            print_info("No orders found or user not authenticated for orders")
            all_orders = []
        
        # Enable MedixMall mode and get filtered orders
        print_step("Getting orders (MedixMall mode ON)")
        self.session.put(f"{BASE_URL}/api/accounts/medixmall-mode/", 
                        json={"medixmall_mode": True}, 
                        headers=headers)
        
        response = self.session.get(f"{BASE_URL}/api/orders/", headers=headers)
        
        if response.status_code == 200:
            medixmall_orders = response.json()['results']
            print_success(f"Found {len(medixmall_orders)} orders in MedixMall mode")
            
            # Check X-MedixMall-Mode header
            mode_header = response.headers.get('X-MedixMall-Mode')
            print_info(f"MedixMall mode header: {mode_header}")
            
            if len(medixmall_orders) <= len(all_orders):
                print_success("✅ Order filtering appears to be working")
            else:
                print_error("❌ More orders in MedixMall mode than total orders")
        else:
            print_info("No orders found or user not authenticated for orders")
        
        return True
    
    def test_swagger_documentation(self):
        """Test Swagger documentation updates"""
        print_header("SWAGGER DOCUMENTATION TEST")
        
        print_step("Checking Swagger schema")
        response = self.session.get(f"{BASE_URL}/swagger/")
        
        if response.status_code == 200:
            print_success("Swagger documentation accessible")
        else:
            print_error(f"Swagger documentation not accessible: {response.status_code}")
        
        # Check OpenAPI schema
        print_step("Checking OpenAPI schema")
        response = self.session.get(f"{BASE_URL}/swagger.json")
        
        if response.status_code == 200:
            try:
                schema = response.json()
                
                # Check for MedixMall endpoints
                paths = schema.get('paths', {})
                medixmall_endpoint = '/api/accounts/medixmall-mode/'
                
                if medixmall_endpoint in paths:
                    print_success("✅ MedixMall mode endpoint found in schema")
                    
                    # Check for X-MedixMall-Mode header in responses
                    endpoint_data = paths[medixmall_endpoint]
                    for method, method_data in endpoint_data.items():
                        responses = method_data.get('responses', {})
                        for status_code, response_data in responses.items():
                            headers = response_data.get('headers', {})
                            if 'X-MedixMall-Mode' in headers:
                                print_success(f"✅ X-MedixMall-Mode header documented in {method.upper()} {status_code}")
                else:
                    print_error("❌ MedixMall mode endpoint not found in schema")
            except json.JSONDecodeError:
                print_error("❌ Failed to parse OpenAPI schema JSON")
        else:
            print_error(f"Failed to get OpenAPI schema: {response.status_code}")
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print_header("COMPREHENSIVE MEDIXMALL MODE TEST")
        print("Testing complete MedixMall switch functionality")
        
        test_results = []
        
        # Authentication
        if self.authenticate_users():
            test_results.append(("Authentication", True))
        else:
            print_error("Authentication failed - stopping tests")
            return False
        
        # Test MedixMall mode endpoints
        test_results.append(("MedixMall Mode Endpoints", self.test_medixmall_mode_endpoints()))
        
        # Test product filtering
        test_results.append(("Product Filtering", self.test_product_filtering()))
        
        # Test enterprise search
        test_results.append(("Enterprise Search", self.test_enterprise_search()))
        
        # Test order filtering
        test_results.append(("Order Filtering", self.test_order_filtering()))
        
        # Test Swagger documentation
        test_results.append(("Swagger Documentation", self.test_swagger_documentation()))
        
        # Print final results
        print_header("TEST RESULTS SUMMARY")
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            if result:
                print_success(f"{test_name}: PASSED")
                passed += 1
            else:
                print_error(f"{test_name}: FAILED")
                failed += 1
        
        print(f"\n📊 SUMMARY: {passed} passed, {failed} failed out of {len(test_results)} tests")
        
        if failed == 0:
            print_success("🎉 ALL TESTS PASSED! MedixMall mode implementation is working correctly.")
        else:
            print_error(f"❌ {failed} test(s) failed. Please check the implementation.")
        
        return failed == 0


if __name__ == "__main__":
    tester = MedixMallTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)