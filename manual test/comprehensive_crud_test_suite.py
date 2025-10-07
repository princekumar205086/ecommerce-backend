#!/usr/bin/env python
"""
Comprehensive CRUD Endpoints Test Suite
Tests all GET, PUT, PATCH, DELETE endpoints for products app
"""
import os
import sys
import json
import random
from datetime import datetime, date
from decimal import Decimal

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import (
    ProductCategory, Brand, Product, ProductVariant, 
    ProductAttribute, ProductAttributeValue, ProductImage,
    SupplierProductPrice, ProductReview
)

User = get_user_model()

class ComprehensiveCRUDTestSuite:
    def __init__(self):
        self.client = Client()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {},
            'crud_coverage': {}
        }
        self.users = {}
        self.test_entities = {}
        
    def log_test(self, test_name, status, details=None, error=None):
        """Log a test result"""
        result = {
            'test_name': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'error': str(error) if error else None
        }
        self.test_results['tests'].append(result)
        
        if status == 'PASS':
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}: {error or details}")
            
    def setup_test_users(self):
        """Setup test users"""
        try:
            # Get existing test users
            self.users['admin'] = User.objects.get(email='admin@example.com')
            self.users['supplier'] = User.objects.get(email='supplier@example.com')
            self.users['user'] = User.objects.get(email='user@example.com')
            
            self.log_test("Setup CRUD Test Users", "PASS")
            
        except Exception as e:
            self.log_test("Setup CRUD Test Users", "FAIL", error=e)
            
    def get_auth_headers(self, user):
        """Get authentication headers for a user"""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
        
    def fetch_existing_entities(self):
        """Fetch existing entities for testing"""
        try:
            admin_headers = self.get_auth_headers(self.users['admin'])
            
            # Get categories
            categories_response = self.client.get('/api/products/categories/', **admin_headers)
            if categories_response.status_code == 200:
                categories = categories_response.json().get('results', [])
                self.test_entities['categories'] = categories[:5]  # Take first 5
                
            # Get brands
            brands_response = self.client.get('/api/products/brands/', **admin_headers)
            if brands_response.status_code == 200:
                brands = brands_response.json().get('results', [])
                self.test_entities['brands'] = brands[:5]  # Take first 5
                
            # Get products
            products_response = self.client.get('/api/products/products/', **admin_headers)
            if products_response.status_code == 200:
                products = products_response.json().get('results', [])
                self.test_entities['products'] = products[:5]  # Take first 5
                
            # Get variants
            variants_response = self.client.get('/api/products/variants/', **admin_headers)
            if variants_response.status_code == 200:
                variants = variants_response.json().get('results', [])
                self.test_entities['variants'] = variants[:5]  # Take first 5
                
            # Get attributes
            attributes_response = self.client.get('/api/products/attributes/', **admin_headers)
            if attributes_response.status_code == 200:
                attributes = attributes_response.json().get('results', [])
                self.test_entities['attributes'] = attributes[:3]  # Take first 3
                
            self.log_test("Fetch Existing Entities", "PASS", {
                "categories": len(self.test_entities.get('categories', [])),
                "brands": len(self.test_entities.get('brands', [])),
                "products": len(self.test_entities.get('products', [])),
                "variants": len(self.test_entities.get('variants', [])),
                "attributes": len(self.test_entities.get('attributes', []))
            })
            
        except Exception as e:
            self.log_test("Fetch Existing Entities", "FAIL", error=e)
            
    def test_get_endpoints(self):
        """Test all GET endpoints"""
        print("\n📖 Testing GET Endpoints...")
        
        endpoints = [
            '/api/products/categories/',
            '/api/products/brands/',
            '/api/products/products/',
            '/api/products/variants/',
            '/api/products/attributes/',
            '/api/products/attribute-values/',
            '/api/products/images/',
            '/api/products/supplier-prices/',
            '/api/products/reviews/'
        ]
        
        # Test with different user roles
        user_types = ['admin', 'supplier', 'user', 'anonymous']
        
        for endpoint in endpoints:
            for user_type in user_types:
                try:
                    if user_type == 'anonymous':
                        response = self.client.get(endpoint)
                        headers = {}
                    else:
                        headers = self.get_auth_headers(self.users[user_type])
                        response = self.client.get(endpoint, **headers)
                    
                    endpoint_name = endpoint.split('/')[-2]  # Get endpoint name
                    
                    if response.status_code in [200, 401, 403]:  # Expected status codes
                        self.log_test(f"GET {endpoint_name} ({user_type})", "PASS", {
                            "status_code": response.status_code,
                            "has_data": 'results' in response.json() if response.status_code == 200 else False
                        })
                    else:
                        self.log_test(f"GET {endpoint_name} ({user_type})", "FAIL", {
                            "status_code": response.status_code,
                            "response": response.json() if response.content else "No content"
                        })
                        
                except Exception as e:
                    self.log_test(f"GET {endpoint_name} ({user_type})", "FAIL", error=e)
                    
    def test_detail_get_endpoints(self):
        """Test GET detail endpoints"""
        print("\n🔍 Testing GET Detail Endpoints...")
        
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        # Test category detail
        if self.test_entities.get('categories'):
            category_id = self.test_entities['categories'][0]['id']
            try:
                response = self.client.get(f'/api/products/categories/{category_id}/', **admin_headers)
                if response.status_code == 200:
                    self.log_test("GET Category Detail", "PASS", {"category_id": category_id})
                else:
                    self.log_test("GET Category Detail", "FAIL", {"status_code": response.status_code})
            except Exception as e:
                self.log_test("GET Category Detail", "FAIL", error=e)
        
        # Test brand detail
        if self.test_entities.get('brands'):
            brand_id = self.test_entities['brands'][0]['id']
            try:
                response = self.client.get(f'/api/products/brands/{brand_id}/', **admin_headers)
                if response.status_code == 200:
                    self.log_test("GET Brand Detail", "PASS", {"brand_id": brand_id})
                else:
                    self.log_test("GET Brand Detail", "FAIL", {"status_code": response.status_code})
            except Exception as e:
                self.log_test("GET Brand Detail", "FAIL", error=e)
                
        # Test product detail
        if self.test_entities.get('products'):
            product_id = self.test_entities['products'][0]['id']
            try:
                response = self.client.get(f'/api/products/products/{product_id}/', **admin_headers)
                if response.status_code == 200:
                    product_data = response.json()
                    self.log_test("GET Product Detail", "PASS", {
                        "product_id": product_id,
                        "product_type": product_data.get('product_type'),
                        "has_variants": bool(product_data.get('variants'))
                    })
                else:
                    self.log_test("GET Product Detail", "FAIL", {"status_code": response.status_code})
            except Exception as e:
                self.log_test("GET Product Detail", "FAIL", error=e)
                
    def test_put_endpoints(self):
        """Test PUT endpoints (full update)"""
        print("\n✏️ Testing PUT Endpoints...")
        
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        # Test category PUT
        if self.test_entities.get('categories'):
            category = self.test_entities['categories'][0]
            category_id = category['id']
            
            updated_data = {
                'name': f"Updated {category['name']}",
                'icon': category.get('icon', ''),
                'is_publish': True
            }
            
            try:
                response = self.client.put(f'/api/products/categories/{category_id}/', 
                                         data=json.dumps(updated_data),
                                         content_type='application/json',
                                         **admin_headers)
                
                if response.status_code == 200:
                    self.log_test("PUT Category Update", "PASS", {"category_id": category_id})
                else:
                    self.log_test("PUT Category Update", "FAIL", {
                        "status_code": response.status_code,
                        "response": response.json() if response.content else "No content"
                    })
            except Exception as e:
                self.log_test("PUT Category Update", "FAIL", error=e)
                
        # Test brand PUT
        if self.test_entities.get('brands'):
            brand = self.test_entities['brands'][0]
            brand_id = brand['id']
            
            updated_data = {
                'name': f"Updated {brand['name']}",
                'image': brand.get('image', '')[:190]  # Limit to 190 characters to be safe
            }
            
            try:
                response = self.client.put(f'/api/products/brands/{brand_id}/', 
                                         data=json.dumps(updated_data),
                                         content_type='application/json',
                                         **admin_headers)
                
                if response.status_code == 200:
                    self.log_test("PUT Brand Update", "PASS", {"brand_id": brand_id})
                else:
                    self.log_test("PUT Brand Update", "FAIL", {
                        "status_code": response.status_code,
                        "response": response.json() if response.content else "No content"
                    })
            except Exception as e:
                self.log_test("PUT Brand Update", "FAIL", error=e)
                
    def test_patch_endpoints(self):
        """Test PATCH endpoints (partial update)"""
        print("\n🔧 Testing PATCH Endpoints...")
        
        admin_headers = self.get_auth_headers(self.users['admin'])
        supplier_headers = self.get_auth_headers(self.users['supplier'])
        
        # Test product PATCH
        if self.test_entities.get('products'):
            product = self.test_entities['products'][0]
            product_id = product['id']
            
            # Test admin PATCH
            patch_data = {
                'description': f"Updated description for {product['name']} at {datetime.now()}",
                'price': '99.99'
            }
            
            try:
                response = self.client.patch(f'/api/products/products/{product_id}/', 
                                           data=json.dumps(patch_data),
                                           content_type='application/json',
                                           **admin_headers)
                
                if response.status_code == 200:
                    self.log_test("PATCH Product (Admin)", "PASS", {"product_id": product_id})
                else:
                    self.log_test("PATCH Product (Admin)", "FAIL", {
                        "status_code": response.status_code,
                        "response": response.json() if response.content else "No content"
                    })
            except Exception as e:
                self.log_test("PATCH Product (Admin)", "FAIL", error=e)
                
            # Test supplier PATCH (should be limited)
            try:
                response = self.client.patch(f'/api/products/products/{product_id}/', 
                                           data=json.dumps(patch_data),
                                           content_type='application/json',
                                           **supplier_headers)
                
                if response.status_code in [200, 403]:  # Success or forbidden
                    self.log_test("PATCH Product (Supplier)", "PASS", {
                        "product_id": product_id,
                        "status_code": response.status_code,
                        "access_level": "forbidden" if response.status_code == 403 else "allowed"
                    })
                else:
                    self.log_test("PATCH Product (Supplier)", "FAIL", {
                        "status_code": response.status_code
                    })
            except Exception as e:
                self.log_test("PATCH Product (Supplier)", "FAIL", error=e)
                
        # Test variant PATCH
        if self.test_entities.get('variants'):
            variant = self.test_entities['variants'][0]
            variant_id = variant['id']
            
            patch_data = {
                'stock': random.randint(10, 100),
                'price': f'{random.uniform(10, 200):.2f}'
            }
            
            try:
                response = self.client.patch(f'/api/products/variants/{variant_id}/', 
                                           data=json.dumps(patch_data),
                                           content_type='application/json',
                                           **admin_headers)
                
                if response.status_code == 200:
                    self.log_test("PATCH Variant", "PASS", {"variant_id": variant_id})
                else:
                    self.log_test("PATCH Variant", "FAIL", {
                        "status_code": response.status_code,
                        "response": response.json() if response.content else "No content"
                    })
            except Exception as e:
                self.log_test("PATCH Variant", "FAIL", error=e)
                
    def test_delete_endpoints(self):
        """Test DELETE endpoints"""
        print("\n🗑️ Testing DELETE Endpoints...")
        
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        # Create a test category to delete
        try:
            test_category_data = {
                'name': f'Test Delete Category {random.randint(1000, 9999)}',
                'icon': 'http://127.0.0.1:8000/media/images/medical-pattern.svg'
            }
            
            create_response = self.client.post('/api/products/categories/', 
                                             data=json.dumps(test_category_data),
                                             content_type='application/json',
                                             **admin_headers)
            
            if create_response.status_code == 201:
                category_id = create_response.json()['id']
                
                # Now delete it
                delete_response = self.client.delete(f'/api/products/categories/{category_id}/', 
                                                   **admin_headers)
                
                if delete_response.status_code == 204:
                    self.log_test("DELETE Category", "PASS", {"category_id": category_id})
                else:
                    self.log_test("DELETE Category", "FAIL", {
                        "status_code": delete_response.status_code
                    })
            else:
                self.log_test("DELETE Category", "SKIP", {"reason": "Could not create test category"})
                
        except Exception as e:
            self.log_test("DELETE Category", "FAIL", error=e)
            
        # Create a test brand to delete
        try:
            test_brand_data = {
                'name': f'Test Delete Brand {random.randint(1000, 9999)}',
                'image': 'http://127.0.0.1:8000/media/images/medical-pattern.svg'
            }
            
            create_response = self.client.post('/api/products/brands/', 
                                             data=json.dumps(test_brand_data),
                                             content_type='application/json',
                                             **admin_headers)
            
            if create_response.status_code == 201:
                brand_id = create_response.json()['id']
                
                # Now delete it
                delete_response = self.client.delete(f'/api/products/brands/{brand_id}/', 
                                                   **admin_headers)
                
                if delete_response.status_code == 204:
                    self.log_test("DELETE Brand", "PASS", {"brand_id": brand_id})
                else:
                    self.log_test("DELETE Brand", "FAIL", {
                        "status_code": delete_response.status_code
                    })
            else:
                self.log_test("DELETE Brand", "SKIP", {"reason": "Could not create test brand"})
                
        except Exception as e:
            self.log_test("DELETE Brand", "FAIL", error=e)
            
    def test_filtering_and_search(self):
        """Test filtering and search functionality"""
        print("\n🔍 Testing Filtering and Search...")
        
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        # Test category search
        try:
            response = self.client.get('/api/products/categories/?search=medicine', **admin_headers)
            if response.status_code == 200:
                results = response.json().get('results', [])
                self.log_test("Search Categories", "PASS", {"results_count": len(results)})
            else:
                self.log_test("Search Categories", "FAIL", {"status_code": response.status_code})
        except Exception as e:
            self.log_test("Search Categories", "FAIL", error=e)
            
        # Test product filtering by type
        try:
            response = self.client.get('/api/products/products/?product_type=medicine', **admin_headers)
            if response.status_code == 200:
                results = response.json().get('results', [])
                self.log_test("Filter Products by Type", "PASS", {"results_count": len(results)})
            else:
                self.log_test("Filter Products by Type", "FAIL", {"status_code": response.status_code})
        except Exception as e:
            self.log_test("Filter Products by Type", "FAIL", error=e)
            
        # Test product search
        try:
            response = self.client.get('/api/products/products/?search=medicine', **admin_headers)
            if response.status_code == 200:
                results = response.json().get('results', [])
                self.log_test("Search Products", "PASS", {"results_count": len(results)})
            else:
                self.log_test("Search Products", "FAIL", {"status_code": response.status_code})
        except Exception as e:
            self.log_test("Search Products", "FAIL", error=e)
            
        # Test ordering
        try:
            response = self.client.get('/api/products/products/?ordering=-created_at', **admin_headers)
            if response.status_code == 200:
                results = response.json().get('results', [])
                self.log_test("Order Products by Date", "PASS", {"results_count": len(results)})
            else:
                self.log_test("Order Products by Date", "FAIL", {"status_code": response.status_code})
        except Exception as e:
            self.log_test("Order Products by Date", "FAIL", error=e)
            
    def test_permission_restrictions(self):
        """Test permission restrictions across different user roles"""
        print("\n🔒 Testing Permission Restrictions...")
        
        user_headers = self.get_auth_headers(self.users['user'])
        
        # Test user trying to create category (should fail)
        try:
            test_data = {'name': 'User Created Category'}
            response = self.client.post('/api/products/categories/', 
                                      data=json.dumps(test_data),
                                      content_type='application/json',
                                      **user_headers)
            
            if response.status_code == 403:
                self.log_test("User Category Creation (Restricted)", "PASS", {
                    "expected_403": True,
                    "status_code": response.status_code
                })
            else:
                self.log_test("User Category Creation (Restricted)", "FAIL", {
                    "expected_403_got": response.status_code
                })
        except Exception as e:
            self.log_test("User Category Creation (Restricted)", "FAIL", error=e)
            
        # Test user trying to delete product (should fail)
        if self.test_entities.get('products'):
            product_id = self.test_entities['products'][0]['id']
            try:
                response = self.client.delete(f'/api/products/products/{product_id}/', **user_headers)
                
                if response.status_code == 403:
                    self.log_test("User Product Deletion (Restricted)", "PASS", {
                        "expected_403": True,
                        "status_code": response.status_code
                    })
                else:
                    self.log_test("User Product Deletion (Restricted)", "FAIL", {
                        "expected_403_got": response.status_code
                    })
            except Exception as e:
                self.log_test("User Product Deletion (Restricted)", "FAIL", error=e)
                
    def generate_crud_summary(self):
        """Generate CRUD test summary"""
        total_tests = len(self.test_results['tests'])
        passed_tests = len([t for t in self.test_results['tests'] if t['status'] == 'PASS'])
        failed_tests = len([t for t in self.test_results['tests'] if t['status'] == 'FAIL'])
        skipped_tests = len([t for t in self.test_results['tests'] if t['status'] == 'SKIP'])
        
        # Categorize tests by CRUD operation
        crud_operations = {'CREATE': 0, 'READ': 0, 'UPDATE': 0, 'DELETE': 0}
        for test in self.test_results['tests']:
            name = test['test_name'].upper()
            if 'POST' in name or 'CREATE' in name:
                crud_operations['CREATE'] += 1
            elif 'GET' in name or 'FETCH' in name or 'SEARCH' in name or 'FILTER' in name:
                crud_operations['READ'] += 1
            elif 'PUT' in name or 'PATCH' in name or 'UPDATE' in name:
                crud_operations['UPDATE'] += 1
            elif 'DELETE' in name:
                crud_operations['DELETE'] += 1
                
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': skipped_tests,
            'success_rate': f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            'crud_coverage': crud_operations
        }
        
        # Save results
        with open('comprehensive_crud_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📊 COMPREHENSIVE CRUD TEST SUMMARY")
        print(f"=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"📈 Success Rate: {self.test_results['summary']['success_rate']}")
        print(f"\n🔄 CRUD Operation Coverage:")
        for operation, count in crud_operations.items():
            print(f"  {operation}: {count} tests")
        print(f"\n📄 Detailed results saved to: comprehensive_crud_test_results.json")
        
    def run_crud_tests(self):
        """Run all CRUD tests"""
        print("🔄 Starting Comprehensive CRUD Endpoints Test Suite")
        print("=" * 60)
        
        try:
            self.setup_test_users()
            self.fetch_existing_entities()
            self.test_get_endpoints()
            self.test_detail_get_endpoints()
            self.test_put_endpoints()
            self.test_patch_endpoints()
            self.test_delete_endpoints()
            self.test_filtering_and_search()
            self.test_permission_restrictions()
            self.generate_crud_summary()
            
        except Exception as e:
            print(f"❌ Critical error in CRUD test suite: {e}")
            self.log_test("CRUD Test Suite Execution", "FAIL", error=e)


if __name__ == '__main__':
    test_suite = ComprehensiveCRUDTestSuite()
    test_suite.run_crud_tests()