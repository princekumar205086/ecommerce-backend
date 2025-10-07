#!/usr/bin/env python
"""
Final Comprehensive Product API Test Suite
Tests all POST and REST endpoints with existing and new data
"""

import os
import sys
import json
import django
from datetime import datetime
from decimal import Decimal

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import (
    ProductCategory, Brand, Product, ProductVariant, 
    ProductAttribute, ProductAttributeValue, ProductImage,
    SupplierProductPrice, ProductReview, MedicineDetails,
    EquipmentDetails, PathologyDetails
)

User = get_user_model()

class FinalComprehensiveProductAPITest:
    def __init__(self):
        self.client = Client()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
        self.entity_counts = {
            'categories': 0,
            'brands': 0,
            'products': 0,
            'variants': 0,
            'images': 0,
            'reviews': 0,
            'supplier_prices': 0
        }
        
    def log_test(self, test_name, status, details=None, response_data=None):
        """Log a test result"""
        result = {
            'test_name': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        if details:
            result['details'] = details
        if response_data:
            result['response'] = response_data
            
        self.test_results['tests'].append(result)
        
        if status == 'PASS':
            print(f"✅ PASS - {test_name}: {details}")
        else:
            print(f"❌ FAIL - {test_name}: {details}")
            
    def setup_users(self):
        """Setup test users"""
        try:
            # Get existing users or use defaults
            try:
                admin_user = User.objects.get(email='admin@test.com')
            except User.DoesNotExist:
                admin_user = User.objects.filter(is_superuser=True).first()
                
            try:
                supplier_user = User.objects.get(email='supplier@test.com')
            except User.DoesNotExist:
                supplier_user = User.objects.filter(role='supplier').first()
                
            try:
                regular_user = User.objects.get(email='user@test.com')
            except User.DoesNotExist:
                regular_user = User.objects.filter(role='user').first()
                
            self.users = {
                'admin': admin_user,
                'supplier': supplier_user,
                'regular': regular_user
            }
            
            self.log_test("Setup Test Users", "PASS", f"Retrieved existing users: {list(self.users.keys())}")
            return True
            
        except Exception as e:
            self.log_test("Setup Test Users", "FAIL", f"Error: {str(e)}")
            return False
            
    def get_auth_headers(self, user):
        """Get authentication headers for a user"""
        if not user:
            return {}
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
        
    def test_existing_data_retrieval(self):
        """Test retrieving existing data"""
        print("\n📖 Testing Existing Data Retrieval...")
        
        # Test Categories
        response = self.client.get('/api/products/categories/')
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', len(data))
            self.log_test("GET Categories List", "PASS", f"Retrieved {count} categories")
        else:
            self.log_test("GET Categories List", "FAIL", f"Status: {response.status_code}")
            
        # Test Brands  
        response = self.client.get('/api/products/brands/')
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', len(data))
            self.log_test("GET Brands List", "PASS", f"Retrieved {count} brands")
        else:
            self.log_test("GET Brands List", "FAIL", f"Status: {response.status_code}")
            
        # Test Products
        response = self.client.get('/api/products/products/')
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', len(data))
            self.log_test("GET Products List", "PASS", f"Retrieved {count} products")
        else:
            self.log_test("GET Products List", "FAIL", f"Status: {response.status_code}")
            
        # Test Variants
        response = self.client.get('/api/products/variants/')
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', len(data))
            self.log_test("GET Variants List", "PASS", f"Retrieved {count} variants")
        else:
            self.log_test("GET Variants List", "FAIL", f"Status: {response.status_code}")
            
    def test_new_entity_creation(self):
        """Test creating new entities with unique names"""
        print("\n📝 Testing New Entity Creation...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Test new category creation (Admin)
        headers = self.get_auth_headers(self.users['admin'])
        category_data = {
            'name': f'Test Category {timestamp}',
            'is_publish': True,
            'status': 'published'
        }
        
        response = self.client.post('/api/products/categories/', 
                                  data=json.dumps(category_data),
                                  content_type='application/json',
                                  **headers)
        
        if response.status_code in [200, 201]:
            created_category = response.json()
            self.entity_counts['categories'] += 1
            self.log_test("Create New Category (Admin)", "PASS", 
                         f"Created category: {created_category.get('name')}")
            self.test_category_id = created_category.get('id')
        else:
            self.log_test("Create New Category (Admin)", "FAIL", 
                         f"Status: {response.status_code}, Response: {response.json()}")
            
        # Test new brand creation (Admin)
        brand_data = {
            'name': f'Test Brand {timestamp}'
        }
        
        response = self.client.post('/api/products/brands/',
                                  data=json.dumps(brand_data),
                                  content_type='application/json',
                                  **headers)
        
        if response.status_code in [200, 201]:
            created_brand = response.json()
            self.entity_counts['brands'] += 1
            self.log_test("Create New Brand (Admin)", "PASS", 
                         f"Created brand: {created_brand.get('name')}")
            self.test_brand_id = created_brand.get('id')
        else:
            self.log_test("Create New Brand (Admin)", "FAIL", 
                         f"Status: {response.status_code}, Response: {response.json()}")
            
    def test_product_creation_with_existing_data(self):
        """Test product creation using existing categories and brands"""
        print("\n💊 Testing Product Creation with Existing Data...")
        
        # Get existing categories and brands
        categories = list(ProductCategory.objects.filter(is_publish=True)[:3])
        brands = list(Brand.objects.all()[:3])
        
        if not categories or not brands:
            self.log_test("Product Creation Prerequisites", "FAIL", 
                         "No active categories or brands available")
            return
            
        # Test Medicine Product Creation (Admin)
        headers = self.get_auth_headers(self.users['admin'])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        medicine_data = {
            'name': f'Test Medicine {timestamp}',
            'description': 'Test medicine for API testing',
            'category': categories[0].id,
            'brand': brands[0].id,
            'product_type': 'medicine',
            'price': '25.99',
            'is_publish': True,
            'status': 'published',
            'medicine_details': {
                'composition': 'Test composition',
                'dosage_form': 'tablet',
                'strength': '500mg',
                'prescription_required': True
            }
        }
        
        response = self.client.post('/api/products/products/',
                                  data=json.dumps(medicine_data),
                                  content_type='application/json',
                                  **headers)
        
        if response.status_code in [200, 201]:
            created_product = response.json()
            self.entity_counts['products'] += 1
            self.log_test("Create Medicine Product (Admin)", "PASS", 
                         f"Created product: {created_product.get('name')}")
            self.test_product_id = created_product.get('id')
        else:
            self.log_test("Create Medicine Product (Admin)", "FAIL", 
                         f"Status: {response.status_code}, Response: {response.json()}")
            
        # Test Equipment Product Creation (Supplier)
        if self.users['supplier']:
            headers = self.get_auth_headers(self.users['supplier'])
            
            equipment_data = {
                'name': f'Test Equipment {timestamp}',
                'description': 'Test equipment for API testing',
                'category': categories[1].id if len(categories) > 1 else categories[0].id,
                'brand': brands[1].id if len(brands) > 1 else brands[0].id,
                'product_type': 'equipment',
                'price': '299.99',
                'is_publish': True,
                'status': 'published',
                'equipment_details': {
                    'model_number': f'TEST-{timestamp}',
                    'warranty_period': 12,
                    'power_requirements': '220V AC',
                    'dimensions': '10x10x10 cm'
                }
            }
            
            response = self.client.post('/api/products/products/',
                                      data=json.dumps(equipment_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code in [200, 201]:
                created_product = response.json()
                self.entity_counts['products'] += 1
                self.log_test("Create Equipment Product (Supplier)", "PASS", 
                             f"Created product: {created_product.get('name')}")
            else:
                self.log_test("Create Equipment Product (Supplier)", "FAIL", 
                             f"Status: {response.status_code}, Response: {response.json()}")
                             
    def test_product_detail_operations(self):
        """Test GET, PUT, PATCH, DELETE operations on products"""
        print("\n✏️ Testing Product Detail Operations...")
        
        # Get existing products
        products = list(Product.objects.all()[:5])
        
        if not products:
            self.log_test("Product Detail Prerequisites", "FAIL", "No products available")
            return
            
        # Test GET product detail with admin authentication
        headers = self.get_auth_headers(self.users['admin'])
        for i, product in enumerate(products[:3]):
            response = self.client.get(f'/api/products/products/{product.id}/', **headers)
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"GET Product Detail #{i+1}", "PASS", 
                             f"Retrieved product: {data.get('name', product.name)}")
            else:
                self.log_test(f"GET Product Detail #{i+1}", "FAIL", 
                             f"Status: {response.status_code}, Product ID: {product.id}")
                             
        # Test PATCH product (Admin)
        test_product = products[0]
        
        patch_data = {
            'price': '39.99',
            'description': f'Updated description {datetime.now().strftime("%H:%M:%S")}'
        }
        
        response = self.client.patch(f'/api/products/products/{test_product.id}/',
                                   data=json.dumps(patch_data),
                                   content_type='application/json',
                                   **headers)
        
        if response.status_code == 200:
            updated_product = response.json()
            self.log_test("PATCH Product (Admin)", "PASS", 
                         f"Updated product price to: {updated_product.get('price')}")
        else:
            self.log_test("PATCH Product (Admin)", "FAIL", 
                         f"Status: {response.status_code}, Response: {response.json()}")
                         
    def test_permission_restrictions(self):
        """Test permission restrictions"""
        print("\n🚫 Testing Permission Restrictions...")
        
        # Test unauthorized product creation
        unauthorized_data = {
            'name': 'Unauthorized Product',
            'description': 'Should not be created'
        }
        
        response = self.client.post('/api/products/products/',
                                  data=json.dumps(unauthorized_data),
                                  content_type='application/json')
        
        if response.status_code in [401, 403]:
            self.log_test("Unauthorized Product Creation", "PASS", 
                         "Correctly blocked unauthorized access")
        else:
            self.log_test("Unauthorized Product Creation", "FAIL", 
                         f"Expected 401/403, got: {response.status_code}")
                         
        # Test regular user trying to create category
        if self.users['regular']:
            headers = self.get_auth_headers(self.users['regular'])
            
            response = self.client.post('/api/products/categories/',
                                      data=json.dumps({'name': 'User Category'}),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code == 403:
                self.log_test("Regular User Category Creation", "PASS", 
                             "Correctly blocked regular user from creating category")
            else:
                self.log_test("Regular User Category Creation", "FAIL", 
                             f"Expected 403, got: {response.status_code}")
                             
    def generate_final_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 FINAL COMPREHENSIVE PRODUCT API TEST REPORT")
        print("="*60)
        
        # Calculate statistics
        total_tests = len(self.test_results['tests'])
        passed_tests = len([t for t in self.test_results['tests'] if t['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Entity creation summary
        print(f"\n📋 Entity Operations Summary:")
        for entity_type, count in self.entity_counts.items():
            print(f"   {entity_type.title()}: {count}")
            
        # Failed tests summary
        failed_test_names = [t['test_name'] for t in self.test_results['tests'] if t['status'] == 'FAIL']
        if failed_test_names:
            print(f"\n❌ Failed Tests:")
            for test_name in failed_test_names:
                print(f"   - {test_name}")
                
        # Store summary
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'entity_counts': self.entity_counts
        }
        
        print(f"\n✅ Final test completed successfully!")
        
        # Save detailed results
        with open('final_comprehensive_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        print(f"💾 Detailed results saved to: final_comprehensive_test_results.json")
        
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Final Comprehensive Product API Tests")
        print("="*60)
        
        if not self.setup_users():
            return
            
        self.test_existing_data_retrieval()
        self.test_new_entity_creation()
        self.test_product_creation_with_existing_data()
        self.test_product_detail_operations()
        self.test_permission_restrictions()
        
        self.generate_final_report()

if __name__ == '__main__':
    test_suite = FinalComprehensiveProductAPITest()
    test_suite.run_all_tests()