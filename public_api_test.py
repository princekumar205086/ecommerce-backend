#!/usr/bin/env python3
"""
Comprehensive Public API Test Script
Tests all public endpoints for products, categories, brands, CMS content, etc.
"""

import requests
import json
import time
from datetime import datetime


class PublicAPITester:
    def __init__(self, base_url='http://127.0.0.1:8000'):
        self.base_url = base_url
        self.admin_token = None
        self.supplier_token = None
        self.results = {
            'passed': 0,
            'failed': 0,
            'total': 0,
            'details': []
        }

    def log_result(self, test_name, status, details=""):
        """Log test result"""
        self.results['total'] += 1
        if status == 'PASS':
            self.results['passed'] += 1
            print(f"✅ {test_name}")
        else:
            self.results['failed'] += 1
            print(f"❌ {test_name}: {details}")
        
        self.results['details'].append({
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def get_auth_token(self, email, password, role="admin"):
        """Get authentication token"""
        try:
            response = requests.post(f"{self.base_url}/api/token/", json={
                'email': email,
                'password': password
            })
            if response.status_code == 200:
                token = response.json()['access']
                self.log_result(f"Auth Token for {role}", "PASS")
                return token
            else:
                self.log_result(f"Auth Token for {role}", "FAIL", f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_result(f"Auth Token for {role}", "FAIL", str(e))
            return None

    def setup_test_data(self):
        """Setup test data using authenticated endpoints"""
        if not self.admin_token:
            return False

        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create test category
        try:
            category_data = {
                'name': f'Test Category {int(time.time())}',
                'description': 'Test category for public API testing'
            }
            response = requests.post(f"{self.base_url}/api/products/categories/", 
                                   json=category_data, headers=headers)
            if response.status_code in [200, 201]:
                category = response.json()
                # Approve the category
                approve_data = {'status': 'published', 'is_publish': True}
                requests.patch(f"{self.base_url}/api/products/categories/{category['id']}/", 
                             json=approve_data, headers=headers)
                self.test_category_id = category['id']
                self.log_result("Setup Test Category", "PASS")
            else:
                self.log_result("Setup Test Category", "FAIL", response.text)
                return False
        except Exception as e:
            self.log_result("Setup Test Category", "FAIL", str(e))
            return False

        # Create test brand
        try:
            brand_data = {
                'name': f'Test Brand {int(time.time())}',
                'description': 'Test brand for public API testing'
            }
            response = requests.post(f"{self.base_url}/api/products/brands/", 
                                   json=brand_data, headers=headers)
            if response.status_code in [200, 201]:
                brand = response.json()
                # Approve the brand (brands don't have status/is_publish fields)
                # approve_data = {'status': 'approved', 'is_publish': True}
                # requests.patch(f"{self.base_url}/api/products/brands/{brand['id']}/", 
                #              json=approve_data, headers=headers)
                self.test_brand_id = brand['id']
                self.log_result("Setup Test Brand", "PASS")
            else:
                self.log_result("Setup Test Brand", "FAIL", response.text)
                return False
        except Exception as e:
            self.log_result("Setup Test Brand", "FAIL", str(e))
            return False

        # Create test product
        try:
            product_data = {
                'name': f'Test Product {int(time.time())}',
                'description': 'Test product for public API testing',
                'price': 99.99,
                'stock': 10,
                'product_type': 'medicine',
                'category': self.test_category_id,
                'brand': self.test_brand_id
            }
            response = requests.post(f"{self.base_url}/api/products/products/", 
                                   json=product_data, headers=headers)
            if response.status_code in [200, 201]:
                product = response.json()
                # Approve the product
                approve_data = {'status': 'published', 'is_publish': True}
                requests.patch(f"{self.base_url}/api/products/products/{product['id']}/", 
                             json=approve_data, headers=headers)
                self.test_product_id = product['id']
                self.log_result("Setup Test Product", "PASS")
                return True
            else:
                self.log_result("Setup Test Product", "FAIL", response.text)
                return False
        except Exception as e:
            self.log_result("Setup Test Product", "FAIL", str(e))
            return False

    def test_public_endpoint(self, endpoint, expected_fields=None, params=None):
        """Test a public endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if expected fields are present
                if expected_fields and isinstance(data, dict):
                    missing_fields = []
                    for field in expected_fields:
                        if field not in data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        self.log_result(f"GET {endpoint}", "FAIL", 
                                      f"Missing fields: {missing_fields}")
                    else:
                        self.log_result(f"GET {endpoint}", "PASS")
                else:
                    self.log_result(f"GET {endpoint}", "PASS")
                
                return data
            else:
                self.log_result(f"GET {endpoint}", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            self.log_result(f"GET {endpoint}", "FAIL", str(e))
            return None

    def test_public_products_api(self):
        """Test all public product endpoints"""
        print("\n🔍 Testing Public Product APIs...")
        
        # Test public categories
        self.test_public_endpoint("/api/public/products/categories/")
        
        # Test public brands
        self.test_public_endpoint("/api/public/products/brands/")
        
        # Test public products list
        products_data = self.test_public_endpoint("/api/public/products/products/")
        
        # Test public product detail (if we have products)
        if products_data and isinstance(products_data, list) and len(products_data) > 0:
            product_id = products_data[0]['id']
            self.test_public_endpoint(f"/api/public/products/products/{product_id}/")
            
            # Test product reviews
            self.test_public_endpoint(f"/api/public/products/products/{product_id}/reviews/")
        
        # Test search endpoint
        search_data = self.test_public_endpoint("/api/public/products/search/", 
                                               expected_fields=['results', 'pagination', 'filters'])
        
        # Test featured products
        self.test_public_endpoint("/api/public/products/featured/")
        
        # Test products by category (if we have categories)
        if hasattr(self, 'test_category_id'):
            self.test_public_endpoint(f"/api/public/products/categories/{self.test_category_id}/products/")
        
        # Test products by brand (if we have brands)
        if hasattr(self, 'test_brand_id'):
            self.test_public_endpoint(f"/api/public/products/brands/{self.test_brand_id}/products/")

    def test_cms_api(self):
        """Test CMS public endpoints"""
        print("\n📄 Testing CMS APIs...")
        
        # Test pages
        self.test_public_endpoint("/api/cms/pages/")
        
        # Test banners
        self.test_public_endpoint("/api/cms/banners/")
        
        # Test blog posts
        self.test_public_endpoint("/api/cms/blog/")
        
        # Test blog categories
        self.test_public_endpoint("/api/cms/blog/categories/")
        
        # Test blog tags
        self.test_public_endpoint("/api/cms/blog/tags/")
        
        # Test FAQs
        self.test_public_endpoint("/api/cms/faqs/")
        
        # Test testimonials
        self.test_public_endpoint("/api/cms/testimonials/")

    def test_other_public_apis(self):
        """Test other public APIs"""
        print("\n🔧 Testing Other Public APIs...")
        
        # Test analytics tracking (public endpoint)
        try:
            response = requests.post(f"{self.base_url}/api/analytics/track/", json={
                'event_type': 'page_view',
                'path': '/test',
                'data': {'test': True}
            })
            if response.status_code in [200, 201]:
                self.log_result("POST /api/analytics/track/", "PASS")
            else:
                self.log_result("POST /api/analytics/track/", "FAIL", 
                              f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("POST /api/analytics/track/", "FAIL", str(e))

    def test_swagger_documentation(self):
        """Test Swagger documentation endpoint"""
        print("\n📚 Testing API Documentation...")
        
        # Test Swagger UI
        try:
            response = requests.get(f"{self.base_url}/swagger/")
            if response.status_code == 200:
                self.log_result("Swagger UI", "PASS")
            else:
                self.log_result("Swagger UI", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Swagger UI", "FAIL", str(e))
        
        # Test ReDoc
        try:
            response = requests.get(f"{self.base_url}/redoc/")
            if response.status_code == 200:
                self.log_result("ReDoc UI", "PASS")
            else:
                self.log_result("ReDoc UI", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("ReDoc UI", "FAIL", str(e))
        
        # Test Swagger JSON
        try:
            response = requests.get(f"{self.base_url}/swagger.json")
            if response.status_code == 200:
                self.log_result("Swagger JSON", "PASS")
            else:
                self.log_result("Swagger JSON", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Swagger JSON", "FAIL", str(e))

    def run_all_tests(self):
        """Run all public API tests"""
        print("🚀 Starting Comprehensive Public API Testing...")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Get authentication tokens for setup
        self.admin_token = self.get_auth_token('admin@example.com', 'adminpass123', 'admin')
        
        # Setup test data if possible
        if self.admin_token:
            self.setup_test_data()
        
        # Run all tests
        self.test_public_products_api()
        self.test_cms_api()
        self.test_other_public_apis()
        self.test_swagger_documentation()
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📋 Total:  {self.results['total']}")
        print(f"🎯 Success Rate: {(self.results['passed']/self.results['total']*100):.1f}%")
        
        if self.results['failed'] > 0:
            print("\n❌ FAILED TESTS:")
            for detail in self.results['details']:
                if detail['status'] == 'FAIL':
                    print(f"   • {detail['test']}: {detail['details']}")
        
        return self.results


def main():
    """Main function"""
    tester = PublicAPITester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open('public_api_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: public_api_test_results.json")


if __name__ == "__main__":
    main()