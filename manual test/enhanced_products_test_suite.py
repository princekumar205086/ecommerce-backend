#!/usr/bin/env python
"""
Enhanced Comprehensive Product API Testing Suite
Tests all product types (medicine, equipment, pathology) and variants
From both Admin and Supplier perspectives with proper permission checking
Enhanced with new variant image field testing and enterprise optimizations
"""
import os
import sys
import json
import random
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

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
    SupplierProductPrice, ProductReview, MedicineDetails,
    EquipmentDetails, PathologyDetails
)

User = get_user_model()

class EnhancedProductsTestSuite:
    def __init__(self):
        self.client = Client()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {},
            'created_entities': {},
            'issues_found': [],
            'suggestions': []
        }
        self.users = {}
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
        self.base_media_url = "http://127.0.0.1:8000/media/images/"
        
    def log_test(self, test_name, status, details=None, response_data=None, error=None):
        """Log a test result with detailed information"""
        result = {
            'test_name': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'response_data': response_data,
            'error': str(error) if error else None
        }
        self.test_results['tests'].append(result)
        
        # Print real-time feedback
        if status == 'PASS':
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}: {error or details}")
            if error:
                self.test_results['issues_found'].append({
                    'test': test_name,
                    'error': str(error),
                    'details': details
                })
            
    def setup_test_users(self):
        """Create or get test users for different roles"""
        try:
            print("\n🔧 Setting up test users...")
            
            # Admin user
            admin_user, created = User.objects.get_or_create(
                email='admin@example.com',
                defaults={
                    'full_name': 'Admin User',
                    'contact': '1234567890',
                    'role': 'admin',
                    'is_staff': True,
                    'is_active': True,
                    'email_verified': True
                }
            )
            if created:
                admin_user.set_password('Admin@123')
                admin_user.save()
            self.users['admin'] = admin_user
            
            # Supplier user  
            supplier_user, created = User.objects.get_or_create(
                email='supplier@example.com',
                defaults={
                    'full_name': 'Supplier User',
                    'contact': '0987654321',
                    'role': 'supplier',
                    'is_active': True,
                    'email_verified': True
                }
            )
            if created:
                supplier_user.set_password('Supplier@123')
                supplier_user.save()
            self.users['supplier'] = supplier_user
            
            # Additional supplier for price comparison testing
            supplier2_user, created = User.objects.get_or_create(
                email='supplier2@example.com',
                defaults={
                    'full_name': 'Supplier Two',
                    'contact': '1122334455',
                    'role': 'supplier',
                    'is_active': True,
                    'email_verified': True
                }
            )
            if created:
                supplier2_user.set_password('Supplier2@123')
                supplier2_user.save()
            self.users['supplier2'] = supplier2_user
            
            # Regular user
            regular_user, created = User.objects.get_or_create(
                email='user@example.com',
                defaults={
                    'full_name': 'Regular User',
                    'contact': '5566778899',
                    'role': 'user',
                    'is_active': True,
                    'email_verified': True
                }
            )
            if created:
                regular_user.set_password('User@123')
                regular_user.save()
            self.users['user'] = regular_user
            
            print(f"✅ Test users setup complete. Users: {list(self.users.keys())}")
            self.log_test("Setup Test Users", "PASS", {"users_created": list(self.users.keys())})
            
        except Exception as e:
            self.log_test("Setup Test Users", "FAIL", error=e)
            raise e
            
    def get_auth_headers(self, user):
        """Get authentication headers for a user"""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
        
    def test_category_creation(self):
        """Test product category creation for admin and supplier"""
        print("\n📁 Testing Category Creation...")
        
        categories_data = [
            {
                'name': 'Advanced Medicine',
                'icon': f'{self.base_media_url}medicine.png',
                'is_publish': True
            },
            {
                'name': 'Medical Equipment Pro',
                'icon': f'{self.base_media_url}doctor-equipment.png',
                'is_publish': True
            },
            {
                'name': 'Pathology Supplies Plus',
                'icon': f'{self.base_media_url}pathology-supplies.png',
                'is_publish': True
            }
        ]
        
        # Test admin category creation
        admin_headers = self.get_auth_headers(self.users['admin'])
        for i, category_data in enumerate(categories_data):
            try:
                response = self.client.post('/api/products/categories/', 
                                          data=json.dumps(category_data),
                                          content_type='application/json',
                                          **admin_headers)
                
                if response.status_code == 201:
                    category_id = response.json()['id']
                    self.created_entities['categories'].append(category_id)
                    self.log_test(f"Create Category (Admin) - {category_data['name']}", "PASS", 
                                {"category_id": category_id, "status_code": response.status_code})
                else:
                    self.log_test(f"Create Category (Admin) - {category_data['name']}", "FAIL", 
                                {"status_code": response.status_code, "response": response.json()})
                    
            except Exception as e:
                self.log_test(f"Create Category (Admin) - {category_data['name']}", "FAIL", error=e)
        
        # Test supplier category creation (should work but require approval)
        supplier_headers = self.get_auth_headers(self.users['supplier'])
        supplier_category_data = {
            'name': 'Supplier Category Test',
            'icon': f'{self.base_media_url}medical-pattern.svg',
            'is_publish': False
        }
        
        try:
            response = self.client.post('/api/products/categories/', 
                                      data=json.dumps(supplier_category_data),
                                      content_type='application/json',
                                      **supplier_headers)
            
            if response.status_code == 201:
                category_id = response.json()['id']
                self.created_entities['categories'].append(category_id)
                self.log_test("Create Category (Supplier)", "PASS", 
                            {"category_id": category_id, "needs_approval": True})
            else:
                self.log_test("Create Category (Supplier)", "FAIL", 
                            {"status_code": response.status_code, "response": response.json()})
                
        except Exception as e:
            self.log_test("Create Category (Supplier)", "FAIL", error=e)
            
        # Test unauthorized category creation
        try:
            response = self.client.post('/api/products/categories/', 
                                      data=json.dumps(supplier_category_data),
                                      content_type='application/json')
            
            if response.status_code == 401:
                self.log_test("Unauthorized Category Creation", "PASS", 
                            {"expected_401": True, "status_code": response.status_code})
            else:
                self.log_test("Unauthorized Category Creation", "FAIL", 
                            {"expected_401_got": response.status_code})
                
        except Exception as e:
            self.log_test("Unauthorized Category Creation", "FAIL", error=e)
                             
    def test_brand_creation(self):
        """Test brand creation for admin and supplier"""
        print("\n🏷️ Testing Brand Creation...")
        
        brands_data = [
            {'name': 'Pfizer Premium', 'image': f'{self.base_media_url}medixmall.jpg'},
            {'name': 'Johnson & Johnson Pro', 'image': f'{self.base_media_url}medicine.png'},
            {'name': 'Siemens Healthineers Advanced', 'image': f'{self.base_media_url}doctor-equipment.png'},
            {'name': 'Roche Diagnostics Plus', 'image': f'{self.base_media_url}pathology-supplies.png'}
        ]
        
        # Test admin brand creation
        admin_headers = self.get_auth_headers(self.users['admin'])
        for brand_data in brands_data:
            try:
                response = self.client.post('/api/products/brands/', 
                                          data=json.dumps(brand_data),
                                          content_type='application/json',
                                          **admin_headers)
                
                if response.status_code == 201:
                    brand_id = response.json()['id']
                    self.created_entities['brands'].append(brand_id)
                    self.log_test(f"Create Brand (Admin) - {brand_data['name']}", "PASS", 
                                {"brand_id": brand_id})
                else:
                    self.log_test(f"Create Brand (Admin) - {brand_data['name']}", "FAIL", 
                                {"status_code": response.status_code, "response": response.json()})
                    
            except Exception as e:
                self.log_test(f"Create Brand (Admin) - {brand_data['name']}", "FAIL", error=e)
        
        # Test supplier brand creation
        supplier_headers = self.get_auth_headers(self.users['supplier'])
        supplier_brand_data = {
            'name': 'Supplier Brand Test',
            'image': f'{self.base_media_url}medical-pattern.svg'
        }
        
        try:
            response = self.client.post('/api/products/brands/', 
                                      data=json.dumps(supplier_brand_data),
                                      content_type='application/json',
                                      **supplier_headers)
            
            if response.status_code == 201:
                brand_id = response.json()['id']
                self.created_entities['brands'].append(brand_id)
                self.log_test("Create Brand (Supplier)", "PASS", 
                            {"brand_id": brand_id, "needs_approval": True})
            else:
                self.log_test("Create Brand (Supplier)", "FAIL", 
                            {"status_code": response.status_code, "response": response.json()})
                
        except Exception as e:
            self.log_test("Create Brand (Supplier)", "FAIL", error=e)
                             
    def test_attribute_creation(self):
        """Test product attribute creation"""
        print("\n🔧 Testing Attribute Creation...")
        
        attributes_data = [
            {'name': 'Size'},
            {'name': 'Color'},
            {'name': 'Dosage'},
            {'name': 'Pack Size'},
            {'name': 'Strength'},
            {'name': 'Brand Variant'},
            {'name': 'Model Type'}
        ]
        
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        for attribute_data in attributes_data:
            try:
                # Check if attribute already exists
                existing_check = self.client.get('/api/products/attributes/', **admin_headers)
                if existing_check.status_code == 200:
                    existing_attrs = existing_check.json().get('results', [])
                    existing_names = [attr['name'] for attr in existing_attrs]
                    
                    if attribute_data['name'] in existing_names:
                        # Find existing attribute and add to our list
                        for attr in existing_attrs:
                            if attr['name'] == attribute_data['name']:
                                self.created_entities['attributes'].append(attr['id'])
                                break
                        self.log_test(f"Attribute Already Exists - {attribute_data['name']}", "PASS", 
                                    {"attribute_found": True, "reused": True})
                        continue
                
                response = self.client.post('/api/products/attributes/', 
                                          data=json.dumps(attribute_data),
                                          content_type='application/json',
                                          **admin_headers)
                
                if response.status_code == 201:
                    attribute_id = response.json()['id']
                    self.created_entities['attributes'].append(attribute_id)
                    self.log_test(f"Create Attribute - {attribute_data['name']}", "PASS", 
                                {"attribute_id": attribute_id})
                else:
                    self.log_test(f"Create Attribute - {attribute_data['name']}", "FAIL", 
                                {"status_code": response.status_code, "response": response.json()})
                    
            except Exception as e:
                self.log_test(f"Create Attribute - {attribute_data['name']}", "FAIL", error=e)
                             
    def test_attribute_values_creation(self):
        """Test attribute values creation"""
        print("\n📊 Testing Attribute Values Creation...")
        
        if not self.created_entities['attributes']:
            self.log_test("Create Attribute Values", "SKIP", {"reason": "No attributes created"})
            return
            
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        # Create values for each attribute
        attribute_values_map = {
            'Size': ['Small', 'Medium', 'Large', 'Extra Large'],
            'Color': ['Red', 'Blue', 'White', 'Black', 'Green'],
            'Dosage': ['10mg', '25mg', '50mg', '100mg'],
            'Pack Size': ['10 pieces', '50 pieces', '100 pieces'],
            'Strength': ['Regular', 'Extra Strong', 'Mild'],
            'Brand Variant': ['Pro', 'Premium', 'Standard'],
            'Model Type': ['Basic', 'Advanced', 'Professional']
        }
        
        # Get attribute names and IDs
        for attr_id in self.created_entities['attributes']:
            try:
                # Get attribute details
                response = self.client.get(f'/api/products/attributes/{attr_id}/', **admin_headers)
                if response.status_code == 200:
                    attr_name = response.json()['name']
                    values = attribute_values_map.get(attr_name, ['Default Value'])
                    
                    for value in values:
                        value_data = {
                            'attribute': attr_id,
                            'value': value
                        }
                        
                        response = self.client.post('/api/products/attribute-values/', 
                                                  data=json.dumps(value_data),
                                                  content_type='application/json',
                                                  **admin_headers)
                        
                        if response.status_code == 201:
                            value_id = response.json()['id']
                            self.created_entities['attribute_values'].append(value_id)
                            self.log_test(f"Create Attribute Value - {attr_name}: {value}", "PASS", 
                                        {"value_id": value_id})
                        else:
                            self.log_test(f"Create Attribute Value - {attr_name}: {value}", "FAIL", 
                                        {"status_code": response.status_code, "response": response.json()})
                            
            except Exception as e:
                self.log_test(f"Create Attribute Values for ID {attr_id}", "FAIL", error=e)
                         
    def test_medicine_product_creation(self, user_type='admin'):
        """Test medicine product creation"""
        print(f"\n💊 Testing Medicine Product Creation ({user_type})...")
        
        if not self.created_entities['categories'] or not self.created_entities['brands']:
            self.log_test(f"Create Medicine Product ({user_type})", "SKIP", 
                        {"reason": "Required categories or brands not available"})
            return
            
        headers = self.get_auth_headers(self.users[user_type])
        
        medicine_data = {
            'name': f'Advanced Pain Relief Medicine ({user_type})',
            'description': 'High-quality pain relief medication with fast action',
            'brand': self.created_entities['brands'][0],
            'category': self.created_entities['categories'][0],
            'product_type': 'medicine',
            'price': '45.99',
            'stock': 100,
            'image': f'{self.base_media_url}medicine.png',
            'specifications': {
                'active_ingredient': 'Ibuprofen',
                'strength': '200mg',
                'form': 'Tablet'
            },
            'medicine_details': {
                'composition': 'Ibuprofen 200mg, Excipients',
                'quantity': '30 tablets',
                'manufacturer': 'PharmaCorp Ltd',
                'prescription_required': False,
                'form': 'Tablet',
                'pack_size': '30 tablets'
            }
        }
        
        try:
            response = self.client.post('/api/products/products/', 
                                      data=json.dumps(medicine_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code == 201:
                product_id = response.json()['id']
                self.created_entities['products'].append(product_id)
                self.log_test(f"Create Medicine Product ({user_type})", "PASS", 
                            {"product_id": product_id, "needs_approval": user_type == 'supplier'})
            else:
                self.log_test(f"Create Medicine Product ({user_type})", "FAIL", 
                            {"status_code": response.status_code, "response": response.json()})
                
        except Exception as e:
            self.log_test(f"Create Medicine Product ({user_type})", "FAIL", error=e)
                         
    def test_equipment_product_creation(self, user_type='admin'):
        """Test equipment product creation"""
        print(f"\n🔬 Testing Equipment Product Creation ({user_type})...")
        
        if not self.created_entities['categories'] or not self.created_entities['brands']:
            self.log_test(f"Create Equipment Product ({user_type})", "SKIP", 
                        {"reason": "Required categories or brands not available"})
            return
            
        headers = self.get_auth_headers(self.users[user_type])
        
        equipment_data = {
            'name': f'Professional Digital Stethoscope ({user_type})',
            'description': 'High-precision digital stethoscope with noise cancellation',
            'brand': self.created_entities['brands'][1] if len(self.created_entities['brands']) > 1 else self.created_entities['brands'][0],
            'category': self.created_entities['categories'][1] if len(self.created_entities['categories']) > 1 else self.created_entities['categories'][0],
            'product_type': 'equipment',
            'price': '299.99',
            'stock': 25,
            'image': f'{self.base_media_url}Professional%20Stethoscope.jpg',  # URL encoded
            'specifications': {
                'type': 'Digital',
                'frequency_range': '20Hz-20kHz',
                'amplification': '5x-100x'
            },
            'equipment_details': {
                'model_number': 'DS-3000-PRO',
                'warranty_period': '2 years',
                'usage_type': 'Professional Medical',
                'technical_specifications': 'Digital signal processing, Bluetooth connectivity, 40-hour battery life',
                'power_requirement': 'Rechargeable Li-ion battery',
                'equipment_type': 'Diagnostic Equipment'
            }
        }
        
        try:
            response = self.client.post('/api/products/products/', 
                                      data=json.dumps(equipment_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code == 201:
                product_id = response.json()['id']
                self.created_entities['products'].append(product_id)
                self.log_test(f"Create Equipment Product ({user_type})", "PASS", 
                            {"product_id": product_id, "needs_approval": user_type == 'supplier'})
            else:
                self.log_test(f"Create Equipment Product ({user_type})", "FAIL", 
                            {"status_code": response.status_code, "response": response.json()})
                
        except Exception as e:
            self.log_test(f"Create Equipment Product ({user_type})", "FAIL", error=e)
                         
    def test_pathology_product_creation(self, user_type='admin'):
        """Test pathology product creation"""
        print(f"\n🧪 Testing Pathology Product Creation ({user_type})...")
        
        if not self.created_entities['categories'] or not self.created_entities['brands']:
            self.log_test(f"Create Pathology Product ({user_type})", "SKIP", 
                        {"reason": "Required categories or brands not available"})
            return
            
        headers = self.get_auth_headers(self.users[user_type])
        
        pathology_data = {
            'name': f'Blood Test Kit Professional ({user_type})',
            'description': 'Comprehensive blood testing kit for medical professionals',
            'brand': self.created_entities['brands'][-1],
            'category': self.created_entities['categories'][-1],
            'product_type': 'pathology',
            'price': '89.99',
            'stock': 50,
            'image': f'{self.base_media_url}pathology-supplies.png',
            'specifications': {
                'test_types': 'CBC, Blood Sugar, Cholesterol',
                'sample_size': '5ml',
                'accuracy': '99.5%'
            },
            'pathology_details': {
                'compatible_tests': 'Complete Blood Count, Glucose levels, Lipid profile, Liver function',
                'chemical_composition': 'EDTA tubes, Serum separators, Reagents',
                'storage_condition': 'Store at 2-8°C, protect from light'
            }
        }
        
        try:
            response = self.client.post('/api/products/products/', 
                                      data=json.dumps(pathology_data),
                                      content_type='application/json',
                                      **headers)
            
            if response.status_code == 201:
                product_id = response.json()['id']
                self.created_entities['products'].append(product_id)
                self.log_test(f"Create Pathology Product ({user_type})", "PASS", 
                            {"product_id": product_id, "needs_approval": user_type == 'supplier'})
            else:
                self.log_test(f"Create Pathology Product ({user_type})", "FAIL", 
                            {"status_code": response.status_code, "response": response.json()})
                
        except Exception as e:
            self.log_test(f"Create Pathology Product ({user_type})", "FAIL", error=e)
                         
    def test_product_variants_creation(self):
        """Test product variants creation with the new image field"""
        print("\n🎭 Testing Product Variants Creation with Images...")
        
        if not self.created_entities['products'] or not self.created_entities['attribute_values']:
            self.log_test("Create Product Variants", "SKIP", 
                        {"reason": "No products or attribute values available"})
            return
            
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        # Create variants for each product
        variant_images = [
            f'{self.base_media_url}medicine.png',
            f'{self.base_media_url}Professional Stethoscope.jpg',
            f'{self.base_media_url}pathology-supplies.png',
            f'{self.base_media_url}N95 Respirator Masks.jpg',
            f'{self.base_media_url}glucose.webp'
        ]
        
        for i, product_id in enumerate(self.created_entities['products'][:3]):  # Test first 3 products
            try:
                # Create multiple variants per product
                for j in range(2):  # 2 variants per product
                    variant_data = {
                        'product': product_id,
                        'sku': f'VAR-{product_id}-{j+1}',
                        'price': f'{random.uniform(10, 199):.2f}',  # Fix decimal precision
                        'additional_price': '5.00',
                        'stock': random.randint(10, 100),
                        'image': variant_images[(i * 2 + j) % len(variant_images)],  # Use the new variant image field
                        'is_active': True,
                        'attributes': self.created_entities['attribute_values'][:2] if j == 0 else self.created_entities['attribute_values'][2:4]
                    }
                    
                    response = self.client.post('/api/products/variants/', 
                                              data=json.dumps(variant_data),
                                              content_type='application/json',
                                              **admin_headers)
                    
                    if response.status_code == 201:
                        variant_id = response.json()['id']
                        self.created_entities['variants'].append(variant_id)
                        self.log_test(f"Create Product Variant - Product {product_id} Variant {j+1}", "PASS", 
                                    {"variant_id": variant_id, "has_image": bool(variant_data['image'])})
                    else:
                        self.log_test(f"Create Product Variant - Product {product_id} Variant {j+1}", "FAIL", 
                                    {"status_code": response.status_code, "response": response.json()})
                        
            except Exception as e:
                self.log_test(f"Create Product Variant - Product {product_id}", "FAIL", error=e)
                             
    def test_product_images_creation(self):
        """Test product images creation for additional image management"""
        print("\n🖼️ Testing Product Images Creation...")
        
        if not self.created_entities['products']:
            self.log_test("Create Product Images", "SKIP", {"reason": "No products available"})
            return
            
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        additional_images = [
            f'{self.base_media_url}thermameter.jpg',
            f'{self.base_media_url}nebulizer.jpg',
            f'{self.base_media_url}oxymeter.webp',
            f'{self.base_media_url}BpMonitor.webp'
        ]
        
        for i, product_id in enumerate(self.created_entities['products'][:2]):  # First 2 products
            try:
                # Add 2 additional images per product
                for j in range(2):
                    image_data = {
                        'product': product_id,
                        'image': additional_images[(i * 2 + j) % len(additional_images)],
                        'alt_text': f'Additional image {j+1} for product {product_id}',
                        'order': j + 1
                    }
                    
                    response = self.client.post('/api/products/images/', 
                                              data=json.dumps(image_data),
                                              content_type='application/json',
                                              **admin_headers)
                    
                    if response.status_code == 201:
                        image_id = response.json()['id']
                        self.created_entities['images'].append(image_id)
                        self.log_test(f"Create Product Image - Product {product_id} Image {j+1}", "PASS", 
                                    {"image_id": image_id})
                    else:
                        self.log_test(f"Create Product Image - Product {product_id} Image {j+1}", "FAIL", 
                                    {"status_code": response.status_code, "response": response.json()})
                        
            except Exception as e:
                self.log_test(f"Create Product Image - Product {product_id}", "FAIL", error=e)
                             
    def test_supplier_prices_creation(self):
        """Test supplier prices creation for product variants"""
        print("\n💰 Testing Supplier Prices Creation...")
        
        if not self.created_entities['variants']:
            self.log_test("Create Supplier Prices", "SKIP", {"reason": "No variants available"})
            return
            
        # Test with both suppliers
        suppliers = ['supplier', 'supplier2']
        locations = [
            {'pincode': '110001', 'district': 'Delhi'},
            {'pincode': '400001', 'district': 'Mumbai'},
            {'pincode': '560001', 'district': 'Bangalore'},
            {'pincode': '600001', 'district': 'Chennai'}
        ]
        
        for supplier_role in suppliers:
            supplier_headers = self.get_auth_headers(self.users[supplier_role])
            
            for i, variant_id in enumerate(self.created_entities['variants'][:3]):  # First 3 variants
                try:
                    location = locations[i % len(locations)]
                    price_data = {
                        'product_variant': variant_id,
                        'price': f'{random.uniform(50, 299):.2f}',  # Fix decimal precision
                        'pincode': location['pincode'],
                        'district': location['district']
                    }
                    
                    response = self.client.post('/api/products/supplier-prices/', 
                                              data=json.dumps(price_data),
                                              content_type='application/json',
                                              **supplier_headers)
                    
                    if response.status_code == 201:
                        price_id = response.json()['id']
                        self.created_entities['supplier_prices'].append(price_id)
                        self.log_test(f"Create Supplier Price - {supplier_role} Variant {variant_id}", "PASS", 
                                    {"price_id": price_id, "location": location})
                    else:
                        self.log_test(f"Create Supplier Price - {supplier_role} Variant {variant_id}", "FAIL", 
                                    {"status_code": response.status_code, "response": response.json()})
                        
                except Exception as e:
                    self.log_test(f"Create Supplier Price - {supplier_role} Variant {variant_id}", "FAIL", error=e)
                             
    def test_product_reviews_creation(self):
        """Test product reviews creation from user perspective"""
        print("\n⭐ Testing Product Reviews Creation...")
        
        if not self.created_entities['products']:
            self.log_test("Create Product Reviews", "SKIP", {"reason": "No products available"})
            return
            
        user_headers = self.get_auth_headers(self.users['user'])
        
        reviews_data = [
            {
                'rating': 5,
                'comment': 'Excellent product! Highly recommend for professional use.'
            },
            {
                'rating': 4,
                'comment': 'Good quality but could be improved in packaging.'
            },
            {
                'rating': 3,
                'comment': 'Average product, meets basic requirements.'
            }
        ]
        
        for i, product_id in enumerate(self.created_entities['products'][:3]):
            try:
                review_data = reviews_data[i % len(reviews_data)]
                review_data['product'] = product_id
                
                response = self.client.post('/api/products/reviews/', 
                                          data=json.dumps(review_data),
                                          content_type='application/json',
                                          **user_headers)
                
                if response.status_code == 201:
                    review_id = response.json()['id']
                    self.created_entities['reviews'].append(review_id)
                    self.log_test(f"Create Product Review - Product {product_id}", "PASS", 
                                {"review_id": review_id, "rating": review_data['rating']})
                else:
                    self.log_test(f"Create Product Review - Product {product_id}", "FAIL", 
                                {"status_code": response.status_code, "response": response.json()})
                    
            except Exception as e:
                self.log_test(f"Create Product Review - Product {product_id}", "FAIL", error=e)
                             
    def test_unauthorized_access(self):
        """Test unauthorized access to various endpoints"""
        print("\n🔒 Testing Unauthorized Access...")
        
        # Test data for unauthorized attempts
        test_data = {
            'category': {'name': 'Unauthorized Category'},
            'brand': {'name': 'Unauthorized Brand'},
            'product': {
                'name': 'Unauthorized Product',
                'category': 1,
                'product_type': 'medicine',
                'price': '10.00'
            }
        }
        
        endpoints = [
            ('/api/products/categories/', test_data['category']),
            ('/api/products/brands/', test_data['brand']),
            ('/api/products/products/', test_data['product'])
        ]
        
        for endpoint, data in endpoints:
            try:
                response = self.client.post(endpoint, 
                                          data=json.dumps(data),
                                          content_type='application/json')
                
                if response.status_code == 401:
                    self.log_test(f"Unauthorized Access - {endpoint}", "PASS", 
                                {"expected_401": True, "status_code": response.status_code})
                else:
                    self.log_test(f"Unauthorized Access - {endpoint}", "FAIL", 
                                {"expected_401_got": response.status_code})
                    
            except Exception as e:
                self.log_test(f"Unauthorized Access - {endpoint}", "FAIL", error=e)
                         
    def analyze_enterprise_optimizations(self):
        """Analyze and suggest enterprise-level optimizations"""
        print("\n🏢 Analyzing Enterprise-Level Optimizations...")
        
        suggestions = []
        
        # Database optimization suggestions
        suggestions.append({
            'category': 'Database Optimization',
            'item': 'Add database indexes for frequently queried fields',
            'details': 'Consider adding indexes on product.category, product.brand, product.product_type, and variant.product for better query performance',
            'priority': 'High'
        })
        
        # Caching suggestions
        suggestions.append({
            'category': 'Caching Strategy',
            'item': 'Implement Redis caching for product listings',
            'details': 'Cache product listings, category hierarchies, and brand lists for improved response times',
            'priority': 'High'
        })
        
        # Image optimization
        suggestions.append({
            'category': 'Image Management',
            'item': 'Implement CDN for image delivery',
            'details': 'Use CloudFront or similar CDN for faster image loading and better user experience',
            'priority': 'Medium'
        })
        
        # Search optimization
        suggestions.append({
            'category': 'Search & Filtering',
            'item': 'Implement Elasticsearch for advanced search',
            'details': 'Add full-text search, faceted filtering, and autocomplete functionality',
            'priority': 'Medium'
        })
        
        # API optimization
        suggestions.append({
            'category': 'API Performance',
            'item': 'Implement API rate limiting and pagination',
            'details': 'Add rate limiting to prevent abuse and optimize pagination for large datasets',
            'priority': 'High'
        })
        
        # Security enhancements
        suggestions.append({
            'category': 'Security',
            'item': 'Implement field-level permissions',
            'details': 'Add granular permissions for different user roles and product approval workflows',
            'priority': 'High'
        })
        
        self.test_results['suggestions'] = suggestions
        
        for suggestion in suggestions:
            print(f"💡 {suggestion['category']}: {suggestion['item']} (Priority: {suggestion['priority']})")
            
        self.log_test("Enterprise Optimization Analysis", "PASS", 
                    {"suggestions_count": len(suggestions)})
                         
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        total_tests = len(self.test_results['tests'])
        passed_tests = len([t for t in self.test_results['tests'] if t['status'] == 'PASS'])
        failed_tests = len([t for t in self.test_results['tests'] if t['status'] == 'FAIL'])
        skipped_tests = len([t for t in self.test_results['tests'] if t['status'] == 'SKIP'])
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': skipped_tests,
            'success_rate': f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            'entities_created': {
                'categories': len(self.created_entities['categories']),
                'brands': len(self.created_entities['brands']),
                'products': len(self.created_entities['products']),
                'variants': len(self.created_entities['variants']),
                'attributes': len(self.created_entities['attributes']),
                'attribute_values': len(self.created_entities['attribute_values']),
                'images': len(self.created_entities['images']),
                'supplier_prices': len(self.created_entities['supplier_prices']),
                'reviews': len(self.created_entities['reviews'])
            },
            'issues_count': len(self.test_results['issues_found']),
            'optimization_suggestions': len(self.test_results.get('suggestions', []))
        }
        
        # Save detailed results to file
        with open('enhanced_products_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📊 COMPREHENSIVE TEST SUMMARY")
        print(f"=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"📈 Success Rate: {self.test_results['summary']['success_rate']}")
        print(f"\n📦 Entities Created:")
        for entity_type, count in self.test_results['summary']['entities_created'].items():
            print(f"  {entity_type.title()}: {count}")
        
        if self.test_results['issues_found']:
            print(f"\n🚨 Issues Found ({len(self.test_results['issues_found'])}):")
            for issue in self.test_results['issues_found'][:5]:  # Show first 5 issues
                print(f"  - {issue['test']}: {issue['error']}")
        
        print(f"\n📄 Detailed results saved to: enhanced_products_test_results.json")
        
    def run_all_post_tests(self):
        """Run all POST endpoint tests"""
        print("🚀 Starting Enhanced Products POST Endpoints Test Suite")
        print("=" * 70)
        
        try:
            # Setup phase
            self.setup_test_users()
            
            # Core entity creation tests
            self.test_category_creation()
            self.test_brand_creation()
            self.test_attribute_creation()
            self.test_attribute_values_creation()
            
            # Product creation tests for all types and both user roles
            self.test_medicine_product_creation('admin')
            self.test_medicine_product_creation('supplier')
            self.test_equipment_product_creation('admin')
            self.test_equipment_product_creation('supplier')
            self.test_pathology_product_creation('admin')
            self.test_pathology_product_creation('supplier')
            
            # Extended functionality tests
            self.test_product_variants_creation()
            self.test_product_images_creation()
            self.test_supplier_prices_creation()
            self.test_product_reviews_creation()
            
            # Security tests
            self.test_unauthorized_access()
            
            # Enterprise optimization analysis
            self.analyze_enterprise_optimizations()
            
            # Generate comprehensive report
            self.generate_summary_report()
            
        except Exception as e:
            print(f"❌ Critical error in test suite: {e}")
            self.log_test("Test Suite Execution", "FAIL", error=e)


if __name__ == '__main__':
    test_suite = EnhancedProductsTestSuite()
    test_suite.run_all_post_tests()