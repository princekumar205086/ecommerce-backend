#!/usr/bin/env python
"""
Comprehensive Product API POST Endpoints Testing Suite
Tests all product types (medicine, equipment, pathology) and variants
From both Admin and Supplier perspectives
"""

import os
import sys
import json
import django
from datetime import datetime, date
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

class ComprehensiveProductPOSTTest:
    def __init__(self):
        self.client = Client()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
        self.created_entities = {
            'categories': [],
            'brands': [],
            'products': [],
            'variants': [],
            'attributes': [],
            'attribute_values': [],
            'images': [],
            'supplier_prices': [],
            'reviews': []
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
            
    def setup_test_users(self):
        """Create test users for admin and supplier roles"""
        try:
            # Create admin user
            admin_user, created = User.objects.get_or_create(
                email='admin_test@medixmall.com',
                defaults={
                    'full_name': 'Admin Test User',
                    'contact': '+91-9999999999',
                    'role': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                    'email_verified': True
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
            
            # Create supplier user
            supplier_user, created = User.objects.get_or_create(
                email='supplier_test@medixmall.com',
                defaults={
                    'full_name': 'Supplier Test User',
                    'contact': '+91-8888888888',
                    'role': 'supplier',
                    'email_verified': True
                }
            )
            if created:
                supplier_user.set_password('supplier123')
                supplier_user.save()
                
            # Create regular user for reviews
            regular_user, created = User.objects.get_or_create(
                email='user_test@medixmall.com',
                defaults={
                    'full_name': 'Regular Test User',
                    'contact': '+91-7777777777',
                    'role': 'user',
                    'email_verified': True
                }
            )
            if created:
                regular_user.set_password('user123')
                regular_user.save()
            
            self.users = {
                'admin': admin_user,
                'supplier': supplier_user,
                'regular': regular_user
            }
            
            self.log_test("Setup Test Users", "PASS", "Test users created successfully")
            return True
            
        except Exception as e:
            self.log_test("Setup Test Users", "FAIL", f"Error: {str(e)}")
            return False
            
    def get_auth_headers(self, user):
        """Get authentication headers for a user"""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
        
    def test_category_creation(self):
        """Test product category creation"""
        print("\n📝 Testing Category Creation...")
        
        categories_data = [
            {
                'name': 'Medicines',
                'is_publish': True,
                'status': 'published'
            },
            {
                'name': 'Medical Equipment',
                'is_publish': True,
                'status': 'published'
            },
            {
                'name': 'Pathology',
                'is_publish': True,
                'status': 'published'
            }
        ]
        
        headers = self.get_auth_headers(self.users['admin'])
        
        for category_data in categories_data:
            response = self.client.post('/api/products/categories/', 
                                      data=json.dumps(category_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code in [200, 201]:
                created_category = response.json()
                self.created_entities['categories'].append(created_category)
                self.log_test(f"Create Category: {category_data['name']}", "PASS", 
                             f"Category created with ID: {created_category.get('id')}")
            else:
                self.log_test(f"Create Category: {category_data['name']}", "FAIL", 
                             f"Failed to create category - Status: {response.status_code}, Response: {response.json()}")
                             
    def test_brand_creation(self):
        """Test brand creation"""
        print("\n🏷️ Testing Brand Creation...")
        
        brands_data = [
            {'name': 'Pfizer'},
            {'name': 'Johnson & Johnson'},
            {'name': 'Roche'},
            {'name': 'Siemens Healthineers'}
        ]
        
        headers = self.get_auth_headers(self.users['admin'])
        
        for brand_data in brands_data:
            response = self.client.post('/api/products/brands/',
                                      data=json.dumps(brand_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code in [200, 201]:
                created_brand = response.json()
                self.created_entities['brands'].append(created_brand)
                self.log_test(f"Create Brand: {brand_data['name']}", "PASS", 
                             f"Brand created with ID: {created_brand.get('id')}")
            else:
                self.log_test(f"Create Brand: {brand_data['name']}", "FAIL", 
                             f"Failed to create brand - Status: {response.status_code}, Response: {response.json()}")
                             
    def test_attribute_creation(self):
        """Test product attribute creation"""
        print("\n🔧 Testing Attribute Creation...")
        
        attributes_data = [
            {'name': 'Size'},
            {'name': 'Color'},
            {'name': 'Dosage'},
            {'name': 'Pack Size'},
            {'name': 'Strength'}
        ]
        
        headers = self.get_auth_headers(self.users['admin'])
        
        for attribute_data in attributes_data:
            response = self.client.post('/api/products/attributes/',
                                      data=json.dumps(attribute_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code in [200, 201]:
                created_attribute = response.json()
                self.created_entities['attributes'].append(created_attribute)
                self.log_test(f"Create Attribute: {attribute_data['name']}", "PASS", 
                             f"Attribute created with ID: {created_attribute.get('id')}")
            else:
                self.log_test(f"Create Attribute: {attribute_data['name']}", "FAIL", 
                             f"Failed to create attribute - Status: {response.status_code}, Response: {response.json()}")
                             
    def test_attribute_values_creation(self):
        """Test attribute values creation"""
        print("\n📊 Testing Attribute Values Creation...")
        
        if not self.created_entities['attributes']:
            self.log_test("Create Attribute Values", "FAIL", "No attributes available")
            return
            
        headers = self.get_auth_headers(self.users['admin'])
        
        # Create values for each attribute
        attribute_values_data = [
            # Size values
            {'attribute': self.created_entities['attributes'][0]['id'], 'value': 'Small'},
            {'attribute': self.created_entities['attributes'][0]['id'], 'value': 'Medium'},
            {'attribute': self.created_entities['attributes'][0]['id'], 'value': 'Large'},
            # Dosage values  
            {'attribute': self.created_entities['attributes'][2]['id'], 'value': '250mg'},
            {'attribute': self.created_entities['attributes'][2]['id'], 'value': '500mg'},
            {'attribute': self.created_entities['attributes'][2]['id'], 'value': '1000mg'},
        ]
        
        for value_data in attribute_values_data:
            response = self.client.post('/api/products/attribute-values/',
                                      data=json.dumps(value_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code in [200, 201]:
                created_value = response.json()
                self.created_entities['attribute_values'].append(created_value)
                self.log_test(f"Create Attribute Value: {value_data['value']}", "PASS", 
                             f"Value created with ID: {created_value.get('id')}")
            else:
                self.log_test(f"Create Attribute Value: {value_data['value']}", "FAIL", 
                             f"Failed to create value - Status: {response.status_code}, Response: {response.json()}")
                             
    def test_medicine_product_creation(self, user_type='admin'):
        """Test medicine product creation"""
        print(f"\n💊 Testing Medicine Product Creation ({user_type})...")
        
        if not self.created_entities['categories'] or not self.created_entities['brands']:
            self.log_test(f"Create Medicine Product ({user_type})", "FAIL", "Categories or brands not available")
            return
            
        headers = self.get_auth_headers(self.users[user_type])
        
        medicine_data = {
            'name': f'Paracetamol 500mg ({user_type})',
            'description': 'Pain relief and fever reducer medication',
            'category': self.created_entities['categories'][0]['id'],  # Medicines category
            'brand': self.created_entities['brands'][0]['id'],  # Pfizer
            'product_type': 'medicine',
            'price': '25.99',
            'stock': 100,
            'is_publish': True,
            'status': 'published',
            'medicine_details': {
                'composition': 'Paracetamol 500mg',
                'quantity': '10 tablets',
                'manufacturer': 'Pfizer Ltd',
                'batch_number': f'BATCH-{datetime.now().strftime("%Y%m%d")}-001',
                'prescription_required': False,
                'form': 'tablet',
                'pack_size': '10 tablets'
            }
        }
        
        response = self.client.post('/api/products/products/',
                                  data=json.dumps(medicine_data),
                                  content_type='application/json',
                                  **headers)
        
        if response.status_code in [200, 201]:
            created_product = response.json()
            self.created_entities['products'].append(created_product)
            self.log_test(f"Create Medicine Product ({user_type})", "PASS", 
                         f"Medicine created with ID: {created_product.get('id')}")
        else:
            self.log_test(f"Create Medicine Product ({user_type})", "FAIL", 
                         f"Failed to create medicine - Status: {response.status_code}, Response: {response.json()}")
                         
    def test_equipment_product_creation(self, user_type='admin'):
        """Test equipment product creation"""
        print(f"\n🏥 Testing Equipment Product Creation ({user_type})...")
        
        if not self.created_entities['categories'] or not self.created_entities['brands']:
            self.log_test(f"Create Equipment Product ({user_type})", "FAIL", "Categories or brands not available")
            return
            
        headers = self.get_auth_headers(self.users[user_type])
        
        equipment_data = {
            'name': f'Digital Thermometer ({user_type})',
            'description': 'High precision digital thermometer for medical use',
            'category': self.created_entities['categories'][1]['id'],  # Medical Equipment category
            'brand': self.created_entities['brands'][1]['id'],  # Johnson & Johnson
            'product_type': 'equipment',
            'price': '299.99',
            'stock': 50,
            'is_publish': True,
            'status': 'published',
            'equipment_details': {
                'model_number': f'DT-{datetime.now().strftime("%Y%m%d")}-001',
                'warranty_period': '2 years',
                'usage_type': 'Medical diagnosis',
                'technical_specifications': 'Digital display, memory function, fever alarm',
                'power_requirement': '1.5V AAA battery',
                'equipment_type': 'Diagnostic equipment'
            }
        }
        
        response = self.client.post('/api/products/products/',
                                  data=json.dumps(equipment_data),
                                  content_type='application/json',
                                  **headers)
        
        if response.status_code in [200, 201]:
            created_product = response.json()
            self.created_entities['products'].append(created_product)
            self.log_test(f"Create Equipment Product ({user_type})", "PASS", 
                         f"Equipment created with ID: {created_product.get('id')}")
        else:
            self.log_test(f"Create Equipment Product ({user_type})", "FAIL", 
                         f"Failed to create equipment - Status: {response.status_code}, Response: {response.json()}")
                         
    def test_pathology_product_creation(self, user_type='admin'):
        """Test pathology product creation"""
        print(f"\n🧪 Testing Pathology Product Creation ({user_type})...")
        
        if not self.created_entities['categories'] or not self.created_entities['brands']:
            self.log_test(f"Create Pathology Product ({user_type})", "FAIL", "Categories or brands not available")
            return
            
        headers = self.get_auth_headers(self.users[user_type])
        
        pathology_data = {
            'name': f'Blood Glucose Test Kit ({user_type})',
            'description': 'Complete kit for blood glucose testing',
            'category': self.created_entities['categories'][2]['id'],  # Pathology category
            'brand': self.created_entities['brands'][2]['id'],  # Roche
            'product_type': 'pathology',
            'price': '149.99',
            'stock': 75,
            'is_publish': True,
            'status': 'published',
            'pathology_details': {
                'compatible_tests': 'Blood glucose, HbA1c',
                'chemical_composition': 'Glucose oxidase enzyme strips',
                'storage_condition': 'Store at room temperature, avoid moisture'
            }
        }
        
        response = self.client.post('/api/products/products/',
                                  data=json.dumps(pathology_data),
                                  content_type='application/json',
                                  **headers)
        
        if response.status_code in [200, 201]:
            created_product = response.json()
            self.created_entities['products'].append(created_product)
            self.log_test(f"Create Pathology Product ({user_type})", "PASS", 
                         f"Pathology product created with ID: {created_product.get('id')}")
        else:
            self.log_test(f"Create Pathology Product ({user_type})", "FAIL", 
                         f"Failed to create pathology product - Status: {response.status_code}, Response: {response.json()}")
                         
    def test_product_variants_creation(self):
        """Test product variant creation"""
        print("\n🎯 Testing Product Variants Creation...")
        
        if not self.created_entities['products'] or not self.created_entities['attribute_values']:
            self.log_test("Create Product Variants", "FAIL", "Products or attribute values not available")
            return
            
        headers = self.get_auth_headers(self.users['admin'])
        
        # Create variants for the first product (medicine)
        product = self.created_entities['products'][0]
        
        variants_data = [
            {
                'product': product['id'],
                'attributes': [self.created_entities['attribute_values'][3]['id']],  # 250mg dosage
                'price': '20.99',
                'additional_price': '0.00',
                'stock': 50,
                'is_active': True
            },
            {
                'product': product['id'],
                'attributes': [self.created_entities['attribute_values'][4]['id']],  # 500mg dosage
                'price': '25.99',
                'additional_price': '0.00',
                'stock': 75,
                'is_active': True
            }
        ]
        
        for variant_data in variants_data:
            response = self.client.post('/api/products/variants/',
                                      data=json.dumps(variant_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code in [200, 201]:
                created_variant = response.json()
                self.created_entities['variants'].append(created_variant)
                self.log_test(f"Create Product Variant", "PASS", 
                             f"Variant created with ID: {created_variant.get('id')}")
            else:
                self.log_test(f"Create Product Variant", "FAIL", 
                             f"Failed to create variant - Status: {response.status_code}, Response: {response.json()}")
                             
    def test_product_images_creation(self):
        """Test product image creation"""
        print("\n🖼️ Testing Product Images Creation...")
        
        if not self.created_entities['products']:
            self.log_test("Create Product Images", "FAIL", "No products available")
            return
            
        headers = self.get_auth_headers(self.users['admin'])
        
        # Create images for products
        for product in self.created_entities['products'][:2]:  # First 2 products
            image_data = {
                'product': product['id'],
                'image': 'https://via.placeholder.com/400x400/0066cc/ffffff?text=Product+Image',
                'alt_text': f'Image for {product["name"]}',
                'order': 1
            }
            
            response = self.client.post('/api/products/images/',
                                      data=json.dumps(image_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code in [200, 201]:
                created_image = response.json()
                self.created_entities['images'].append(created_image)
                self.log_test(f"Create Product Image", "PASS", 
                             f"Image created with ID: {created_image.get('id')}")
            else:
                self.log_test(f"Create Product Image", "FAIL", 
                             f"Failed to create image - Status: {response.status_code}, Response: {response.json()}")
                             
    def test_supplier_prices_creation(self):
        """Test supplier price creation"""
        print("\n💰 Testing Supplier Prices Creation...")
        
        if not self.created_entities['variants']:
            self.log_test("Create Supplier Prices", "FAIL", "No variants available")
            return
            
        headers = self.get_auth_headers(self.users['supplier'])
        
        # Create supplier prices for variants
        for variant in self.created_entities['variants']:
            price_data = {
                'product_variant': variant['id'],
                'price': str(float(variant['price']) * 0.9),  # 10% discount from retail
                'pincode': '110001',
                'district': 'New Delhi'
            }
            
            response = self.client.post('/api/products/supplier-prices/',
                                      data=json.dumps(price_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code in [200, 201]:
                created_price = response.json()
                self.created_entities['supplier_prices'].append(created_price)
                self.log_test(f"Create Supplier Price", "PASS", 
                             f"Price created with ID: {created_price.get('id')}")
            else:
                self.log_test(f"Create Supplier Price", "FAIL", 
                             f"Failed to create price - Status: {response.status_code}, Response: {response.json()}")
                             
    def test_product_reviews_creation(self):
        """Test product review creation"""
        print("\n⭐ Testing Product Reviews Creation...")
        
        if not self.created_entities['products']:
            self.log_test("Create Product Reviews", "FAIL", "No products available")
            return
            
        headers = self.get_auth_headers(self.users['regular'])
        
        # Create reviews for products
        for product in self.created_entities['products'][:2]:  # First 2 products
            review_data = {
                'product': product['id'],
                'rating': 5,
                'comment': f'Excellent product! {product["name"]} works perfectly and arrived quickly.'
            }
            
            response = self.client.post('/api/products/reviews/',
                                      data=json.dumps(review_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code in [200, 201]:
                created_review = response.json()
                self.created_entities['reviews'].append(created_review)
                self.log_test(f"Create Product Review", "PASS", 
                             f"Review created with ID: {created_review.get('id')}")
            else:
                self.log_test(f"Create Product Review", "FAIL", 
                             f"Failed to create review - Status: {response.status_code}, Response: {response.json()}")
                             
    def test_unauthorized_access(self):
        """Test unauthorized access scenarios"""
        print("\n🚫 Testing Unauthorized Access...")
        
        # Test without authentication
        unauthorized_data = {
            'name': 'Unauthorized Category',
            'is_publish': True
        }
        
        response = self.client.post('/api/products/categories/',
                                  data=json.dumps(unauthorized_data),
                                  content_type='application/json')
        
        if response.status_code in [401, 403]:
            self.log_test("Unauthorized Category Creation", "PASS", 
                         "Correctly blocked unauthorized access")
        else:
            self.log_test("Unauthorized Category Creation", "FAIL", 
                         f"Expected 401/403, got: {response.status_code}")
        
        # Test regular user trying to create product
        headers = self.get_auth_headers(self.users['regular'])
        
        response = self.client.post('/api/products/products/',
                                  data=json.dumps({'name': 'User Product'}),
                                  content_type='application/json',
                                  **headers)
        
        if response.status_code == 403:
            self.log_test("Unauthenticated Product Creation", "PASS", 
                         "Correctly blocked unauthenticated access")
        else:
            self.log_test("Unauthenticated Product Creation", "FAIL", 
                         f"Expected 403, got: {response.status_code}")
                         
    def generate_summary_report(self):
        """Generate comprehensive test summary"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE POST ENDPOINTS TEST REPORT")
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
        print(f"\n📋 Created Entities Summary:")
        for entity_type, entities in self.created_entities.items():
            print(f"   {entity_type.title()}: {len(entities)}")
            
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
            'entity_counts': {k: len(v) for k, v in self.created_entities.items()}
        }
        
        print(f"\n✅ Test completed successfully!")
        
        # Save detailed results
        with open('comprehensive_post_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        print(f"💾 Detailed results saved to: comprehensive_post_test_results.json")
        
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Product API POST Tests")
        print("="*60)
        
        if not self.setup_test_users():
            return
            
        # Basic entity creation
        self.test_category_creation()
        self.test_brand_creation()
        self.test_attribute_creation()
        self.test_attribute_values_creation()
        
        # Product creation - Admin perspective
        self.test_medicine_product_creation('admin')
        self.test_equipment_product_creation('admin')
        self.test_pathology_product_creation('admin')
        
        # Product creation - Supplier perspective
        self.test_medicine_product_creation('supplier')
        self.test_equipment_product_creation('supplier')
        self.test_pathology_product_creation('supplier')
        
        # Variants and related entities
        self.test_product_variants_creation()
        self.test_product_images_creation()
        self.test_supplier_prices_creation()
        self.test_product_reviews_creation()
        
        # Security testing
        self.test_unauthorized_access()
        
        # Generate final report
        self.generate_summary_report()

if __name__ == '__main__':
    test_suite = ComprehensiveProductPOSTTest()
    test_suite.run_all_tests()