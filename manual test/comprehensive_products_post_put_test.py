#!/usr/bin/env python3
"""
COMPREHENSIVE PRODUCTS POST/PUT TEST SUITE
==========================================

This script tests all POST and PUT endpoints for:
1. Brands (Admin vs Supplier)
2. Categories (Admin vs Supplier) 
3. Products - All 3 types with specifications:
   - Medicine Products (with MedicineDetails)
   - Equipment Products (with EquipmentDetails) 
   - Pathology Products (with PathologyDetails)
4. Product Variants with attributes
5. Admin approval workflow

Tests both Admin and Supplier workflows with complete validation.
"""

import os
import sys
import django
import json
import jwt
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from products.models import (
    Brand, ProductCategory, Product, ProductVariant,
    MedicineDetails, EquipmentDetails, PathologyDetails,
    ProductAttribute, ProductAttributeValue
)

User = get_user_model()

class ComprehensiveProductTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.admin_token = None
        self.supplier_token = None
        self.test_results = []
        self.created_items = {
            'brands': [],
            'categories': [],
            'products': [],
            'variants': [],
            'attributes': [],
            'attribute_values': []
        }

    def log_result(self, test_name, success, details, response_data=None):
        """Log test results with details"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")

    def setup_users_and_tokens(self):
        """Setup admin and supplier users with JWT tokens"""
        print("\n🔧 Setting up test users and tokens...")
        
        try:
            # Get or create admin user
            admin_user, created = User.objects.get_or_create(
                email='admin@test.com',
                defaults={
                    'full_name': 'Test Admin',
                    'role': 'admin',
                    'is_verified': True,
                    'is_active': True
                }
            )
            if created:
                admin_user.set_password('testpass123')
                admin_user.save()

            # Get or create supplier user
            supplier_user, created = User.objects.get_or_create(
                email='supplier@test.com',
                defaults={
                    'full_name': 'Test Supplier',
                    'role': 'supplier',
                    'is_verified': True,
                    'is_active': True
                }
            )
            if created:
                supplier_user.set_password('testpass123')
                supplier_user.save()

            # Generate JWT tokens manually
            payload_admin = {
                'user_id': admin_user.id,
                'email': admin_user.email,
                'role': admin_user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            
            payload_supplier = {
                'user_id': supplier_user.id,
                'email': supplier_user.email,
                'role': supplier_user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }

            self.admin_token = jwt.encode(payload_admin, settings.SECRET_KEY, algorithm='HS256')
            self.supplier_token = jwt.encode(payload_supplier, settings.SECRET_KEY, algorithm='HS256')
            
            print(f"✅ Admin user: {admin_user.email} (ID: {admin_user.id})")
            print(f"✅ Supplier user: {supplier_user.email} (ID: {supplier_user.id})")
            print(f"✅ Tokens generated successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up users: {str(e)}")
            return False

    def setup_attributes(self):
        """Setup product attributes for variant testing"""
        print("\n🔧 Setting up product attributes...")
        
        try:
            # Create attributes
            size_attr, _ = ProductAttribute.objects.get_or_create(name='Size')
            color_attr, _ = ProductAttribute.objects.get_or_create(name='Color')
            weight_attr, _ = ProductAttribute.objects.get_or_create(name='Weight')
            
            # Create attribute values
            size_values = ['Small', 'Medium', 'Large', 'XL']
            color_values = ['Red', 'Blue', 'Green', 'Black', 'White']
            weight_values = ['100g', '250g', '500g', '1kg']
            
            for value in size_values:
                obj, _ = ProductAttributeValue.objects.get_or_create(
                    attribute=size_attr, value=value
                )
                self.created_items['attribute_values'].append(obj.id)
            
            for value in color_values:
                obj, _ = ProductAttributeValue.objects.get_or_create(
                    attribute=color_attr, value=value
                )
                self.created_items['attribute_values'].append(obj.id)
                
            for value in weight_values:
                obj, _ = ProductAttributeValue.objects.get_or_create(
                    attribute=weight_attr, value=value
                )
                self.created_items['attribute_values'].append(obj.id)
            
            self.created_items['attributes'].extend([size_attr.id, color_attr.id, weight_attr.id])
            
            print(f"✅ Created attributes: Size, Color, Weight")
            print(f"✅ Created {len(self.created_items['attribute_values'])} attribute values")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up attributes: {str(e)}")
            return False

    def make_request(self, method, endpoint, data=None, token=None, files=None):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if files:
            # Remove Content-Type for multipart
            headers.pop('Content-Type', None)
            
        try:
            if method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                if files:
                    response = requests.put(url, data=data, files=files, headers=headers)
                else:
                    response = requests.put(url, json=data, headers=headers)
            else:
                response = requests.get(url, headers=headers)
                
            return response
            
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
            return None

    def test_brand_creation(self):
        """Test brand creation for admin and supplier"""
        print("\n🧪 Testing Brand Creation...")
        
        # Test 1: Admin creates brand (should be published immediately)
        brand_data = {
            'name': 'Admin Test Brand',
            'image': 'https://example.com/admin-brand.jpg'
        }
        
        response = self.make_request('POST', '/api/products/brands/', brand_data, self.admin_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['brands'].append(data['id'])
            
            # Verify admin brand is published
            if data.get('status') == 'published' and data.get('is_publish') == True:
                self.log_result(
                    "Admin Brand Creation",
                    True,
                    f"Admin brand created and published immediately (ID: {data['id']})",
                    data
                )
            else:
                self.log_result(
                    "Admin Brand Creation",
                    False,
                    f"Admin brand not published immediately. Status: {data.get('status')}, Published: {data.get('is_publish')}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Admin Brand Creation",
                False,
                f"Failed to create admin brand. Status: {response.status_code if response else 'No response'}",
                error_data
            )

        # Test 2: Supplier creates brand (should be pending approval)
        brand_data = {
            'name': 'Supplier Test Brand',
            'image': 'https://example.com/supplier-brand.jpg'
        }
        
        response = self.make_request('POST', '/api/products/brands/', brand_data, self.supplier_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['brands'].append(data['id'])
            
            # Verify supplier brand is pending
            if data.get('status') == 'pending' and data.get('is_publish') == False:
                self.log_result(
                    "Supplier Brand Creation",
                    True,
                    f"Supplier brand created and pending approval (ID: {data['id']})",
                    data
                )
            else:
                self.log_result(
                    "Supplier Brand Creation",
                    False,
                    f"Supplier brand should be pending. Status: {data.get('status')}, Published: {data.get('is_publish')}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Supplier Brand Creation",
                False,
                f"Failed to create supplier brand. Status: {response.status_code if response else 'No response'}",
                error_data
            )

    def test_brand_updates(self):
        """Test brand PUT operations"""
        print("\n🧪 Testing Brand Updates...")
        
        if not self.created_items['brands']:
            self.log_result("Brand Updates", False, "No brands available for testing updates")
            return
        
        brand_id = self.created_items['brands'][0]
        
        # Test admin update
        update_data = {
            'name': 'Updated Admin Brand Name',
            'image': 'https://example.com/updated-admin-brand.jpg'
        }
        
        response = self.make_request('PUT', f'/api/products/brands/{brand_id}/', update_data, self.admin_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('name') == update_data['name']:
                self.log_result(
                    "Admin Brand Update",
                    True,
                    f"Admin successfully updated brand (ID: {brand_id})",
                    data
                )
            else:
                self.log_result(
                    "Admin Brand Update",
                    False,
                    f"Brand name not updated correctly. Expected: {update_data['name']}, Got: {data.get('name')}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Admin Brand Update",
                False,
                f"Failed to update brand. Status: {response.status_code if response else 'No response'}",
                error_data
            )

    def test_category_creation(self):
        """Test category creation for admin and supplier"""
        print("\n🧪 Testing Category Creation...")
        
        # Test 1: Admin creates parent category
        category_data = {
            'name': 'Admin Parent Category',
            'icon': 'https://example.com/admin-category.jpg'
        }
        
        response = self.make_request('POST', '/api/products/categories/', category_data, self.admin_token)
        
        parent_category_id = None
        if response and response.status_code == 201:
            data = response.json()
            parent_category_id = data['id']
            self.created_items['categories'].append(data['id'])
            
            if data.get('status') == 'published' and data.get('is_publish') == True:
                self.log_result(
                    "Admin Parent Category Creation",
                    True,
                    f"Admin parent category created and published (ID: {data['id']})",
                    data
                )
            else:
                self.log_result(
                    "Admin Parent Category Creation",
                    False,
                    f"Admin category not published. Status: {data.get('status')}, Published: {data.get('is_publish')}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Admin Parent Category Creation",
                False,
                f"Failed to create admin parent category. Status: {response.status_code if response else 'No response'}",
                error_data
            )

        # Test 2: Admin creates child category
        if parent_category_id:
            child_category_data = {
                'name': 'Admin Child Category',
                'parent': parent_category_id,
                'icon': 'https://example.com/admin-child-category.jpg'
            }
            
            response = self.make_request('POST', '/api/products/categories/', child_category_data, self.admin_token)
            
            if response and response.status_code == 201:
                data = response.json()
                self.created_items['categories'].append(data['id'])
                
                if data.get('parent') == parent_category_id:
                    self.log_result(
                        "Admin Child Category Creation",
                        True,
                        f"Admin child category created with parent {parent_category_id} (ID: {data['id']})",
                        data
                    )
                else:
                    self.log_result(
                        "Admin Child Category Creation",
                        False,
                        f"Child category parent not set correctly. Expected: {parent_category_id}, Got: {data.get('parent')}",
                        data
                    )

        # Test 3: Supplier creates category (should be pending)
        supplier_category_data = {
            'name': 'Supplier Test Category',
            'icon': 'https://example.com/supplier-category.jpg'
        }
        
        response = self.make_request('POST', '/api/products/categories/', supplier_category_data, self.supplier_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['categories'].append(data['id'])
            
            if data.get('status') == 'pending' and data.get('is_publish') == False:
                self.log_result(
                    "Supplier Category Creation",
                    True,
                    f"Supplier category created and pending approval (ID: {data['id']})",
                    data
                )
            else:
                self.log_result(
                    "Supplier Category Creation",
                    False,
                    f"Supplier category should be pending. Status: {data.get('status')}, Published: {data.get('is_publish')}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Supplier Category Creation",
                False,
                f"Failed to create supplier category. Status: {response.status_code if response else 'No response'}",
                error_data
            )

    def test_category_updates(self):
        """Test category PUT operations"""
        print("\n🧪 Testing Category Updates...")
        
        if not self.created_items['categories']:
            self.log_result("Category Updates", False, "No categories available for testing updates")
            return
        
        category_id = self.created_items['categories'][0]
        
        update_data = {
            'name': 'Updated Admin Category Name',
            'icon': 'https://example.com/updated-admin-category.jpg'
        }
        
        response = self.make_request('PUT', f'/api/products/categories/{category_id}/', update_data, self.admin_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('name') == update_data['name']:
                self.log_result(
                    "Admin Category Update",
                    True,
                    f"Admin successfully updated category (ID: {category_id})",
                    data
                )
            else:
                self.log_result(
                    "Admin Category Update",
                    False,
                    f"Category name not updated correctly. Expected: {update_data['name']}, Got: {data.get('name')}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Admin Category Update",
                False,
                f"Failed to update category. Status: {response.status_code if response else 'No response'}",
                error_data
            )

    def test_medicine_product_creation(self):
        """Test medicine product creation with MedicineDetails"""
        print("\n🧪 Testing Medicine Product Creation...")
        
        if not self.created_items['categories'] or not self.created_items['brands']:
            self.log_result("Medicine Product Creation", False, "Missing categories or brands for testing")
            return
        
        # Test 1: Admin creates medicine product
        medicine_data = {
            'name': 'Admin Medicine Product',
            'description': 'Test medicine product created by admin',
            'category': self.created_items['categories'][0],
            'brand': self.created_items['brands'][0],
            'product_type': 'medicine',
            'price': '99.99',
            'stock': 100,
            'image': 'https://example.com/medicine.jpg',
            'specifications': {
                'storage': 'Store in cool, dry place',
                'dosage': 'As directed by physician'
            },
            'medicine_details': {
                'composition': 'Paracetamol 500mg, Caffeine 30mg',
                'quantity': '10 tablets',
                'manufacturer': 'Test Pharma Ltd',
                'expiry_date': '2025-12-31',
                'batch_number': 'MED001',
                'prescription_required': True,
                'form': 'Tablet',
                'pack_size': '1x10 tablets'
            }
        }
        
        response = self.make_request('POST', '/api/products/products/', medicine_data, self.admin_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['products'].append(data['id'])
            
            # Verify medicine details are created
            success_checks = []
            success_checks.append(data.get('product_type') == 'medicine')
            success_checks.append(data.get('medicine_details') is not None)
            success_checks.append(data.get('medicine_details', {}).get('composition') == medicine_data['medicine_details']['composition'])
            success_checks.append(data.get('medicine_details', {}).get('prescription_required') == True)
            
            if all(success_checks):
                self.log_result(
                    "Admin Medicine Product Creation",
                    True,
                    f"Admin medicine product created with details (ID: {data['id']})",
                    data
                )
            else:
                self.log_result(
                    "Admin Medicine Product Creation",
                    False,
                    f"Medicine product created but details incomplete. Checks: {success_checks}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Admin Medicine Product Creation",
                False,
                f"Failed to create medicine product. Status: {response.status_code if response else 'No response'}",
                error_data
            )

        # Test 2: Supplier creates medicine product
        supplier_medicine_data = {
            'name': 'Supplier Medicine Product',
            'description': 'Test medicine product created by supplier',
            'category': self.created_items['categories'][0],
            'brand': self.created_items['brands'][0],
            'product_type': 'medicine',
            'price': '79.99',
            'stock': 50,
            'image': 'https://example.com/supplier-medicine.jpg',
            'medicine_details': {
                'composition': 'Ibuprofen 400mg',
                'quantity': '20 tablets',
                'manufacturer': 'Supplier Pharma',
                'expiry_date': '2025-06-30',
                'batch_number': 'SUP001',
                'prescription_required': False,
                'form': 'Tablet',
                'pack_size': '2x10 tablets'
            }
        }
        
        response = self.make_request('POST', '/api/products/products/', supplier_medicine_data, self.supplier_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['products'].append(data['id'])
            
            # Verify supplier product is pending
            success_checks = []
            success_checks.append(data.get('status') == 'pending')
            success_checks.append(data.get('is_publish') == False)
            success_checks.append(data.get('medicine_details') is not None)
            
            if all(success_checks):
                self.log_result(
                    "Supplier Medicine Product Creation",
                    True,
                    f"Supplier medicine product created and pending (ID: {data['id']})",
                    data
                )
            else:
                self.log_result(
                    "Supplier Medicine Product Creation",
                    False,
                    f"Supplier medicine product issues. Checks: {success_checks}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Supplier Medicine Product Creation",
                False,
                f"Failed to create supplier medicine product. Status: {response.status_code if response else 'No response'}",
                error_data
            )

    def test_equipment_product_creation(self):
        """Test equipment product creation with EquipmentDetails"""
        print("\n🧪 Testing Equipment Product Creation...")
        
        if not self.created_items['categories'] or not self.created_items['brands']:
            self.log_result("Equipment Product Creation", False, "Missing categories or brands for testing")
            return
        
        # Admin creates equipment product
        equipment_data = {
            'name': 'Medical Stethoscope',
            'description': 'Professional grade stethoscope for medical diagnosis',
            'category': self.created_items['categories'][0],
            'brand': self.created_items['brands'][0],
            'product_type': 'equipment',
            'price': '299.99',
            'stock': 25,
            'image': 'https://example.com/stethoscope.jpg',
            'specifications': {
                'material': 'Stainless Steel',
                'weight': '200g'
            },
            'equipment_details': {
                'model_number': 'STET-PRO-2024',
                'warranty_period': '2 years',
                'usage_type': 'Professional Medical',
                'technical_specifications': 'Frequency range: 20Hz-2000Hz, Tube length: 28 inches',
                'power_requirement': 'N/A - Manual device',
                'equipment_type': 'Diagnostic Tool'
            }
        }
        
        response = self.make_request('POST', '/api/products/products/', equipment_data, self.admin_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['products'].append(data['id'])
            
            success_checks = []
            success_checks.append(data.get('product_type') == 'equipment')
            success_checks.append(data.get('equipment_details') is not None)
            success_checks.append(data.get('equipment_details', {}).get('model_number') == equipment_data['equipment_details']['model_number'])
            success_checks.append(data.get('equipment_details', {}).get('warranty_period') == '2 years')
            
            if all(success_checks):
                self.log_result(
                    "Admin Equipment Product Creation",
                    True,
                    f"Admin equipment product created with details (ID: {data['id']})",
                    data
                )
            else:
                self.log_result(
                    "Admin Equipment Product Creation",
                    False,
                    f"Equipment product created but details incomplete. Checks: {success_checks}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Admin Equipment Product Creation",
                False,
                f"Failed to create equipment product. Status: {response.status_code if response else 'No response'}",
                error_data
            )

        # Supplier creates equipment product
        supplier_equipment_data = {
            'name': 'Digital Thermometer',
            'description': 'Accurate digital thermometer for temperature measurement',
            'category': self.created_items['categories'][0],
            'brand': self.created_items['brands'][0],
            'product_type': 'equipment',
            'price': '49.99',
            'stock': 100,
            'equipment_details': {
                'model_number': 'THERM-DIG-001',
                'warranty_period': '1 year',
                'usage_type': 'Home/Clinical use',
                'technical_specifications': 'Range: 32-42°C, Accuracy: ±0.1°C',
                'power_requirement': '1.5V LR44 battery',
                'equipment_type': 'Temperature Measurement'
            }
        }
        
        response = self.make_request('POST', '/api/products/products/', supplier_equipment_data, self.supplier_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['products'].append(data['id'])
            
            success_checks = []
            success_checks.append(data.get('status') == 'pending')
            success_checks.append(data.get('equipment_details') is not None)
            success_checks.append(data.get('equipment_details', {}).get('model_number') == supplier_equipment_data['equipment_details']['model_number'])
            
            if all(success_checks):
                self.log_result(
                    "Supplier Equipment Product Creation",
                    True,
                    f"Supplier equipment product created and pending (ID: {data['id']})",
                    data
                )
            else:
                self.log_result(
                    "Supplier Equipment Product Creation",
                    False,
                    f"Supplier equipment product issues. Checks: {success_checks}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Supplier Equipment Product Creation",
                False,
                f"Failed to create supplier equipment product. Status: {response.status_code if response else 'No response'}",
                error_data
            )

    def test_pathology_product_creation(self):
        """Test pathology product creation with PathologyDetails"""
        print("\n🧪 Testing Pathology Product Creation...")
        
        if not self.created_items['categories'] or not self.created_items['brands']:
            self.log_result("Pathology Product Creation", False, "Missing categories or brands for testing")
            return
        
        # Admin creates pathology product
        pathology_data = {
            'name': 'Blood Glucose Test Strips',
            'description': 'High accuracy glucose test strips for diabetes monitoring',
            'category': self.created_items['categories'][0],
            'brand': self.created_items['brands'][0],
            'product_type': 'pathology',
            'price': '45.99',
            'stock': 200,
            'image': 'https://example.com/glucose-strips.jpg',
            'specifications': {
                'pack_size': '50 strips',
                'shelf_life': '24 months'
            },
            'pathology_details': {
                'compatible_tests': 'Blood Glucose Level, HbA1c estimation',
                'chemical_composition': 'Glucose oxidase enzyme, Potassium ferricyanide',
                'storage_condition': 'Store at 2-30°C in dry place, avoid direct sunlight'
            }
        }
        
        response = self.make_request('POST', '/api/products/products/', pathology_data, self.admin_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['products'].append(data['id'])
            
            success_checks = []
            success_checks.append(data.get('product_type') == 'pathology')
            success_checks.append(data.get('pathology_details') is not None)
            success_checks.append('glucose' in data.get('pathology_details', {}).get('compatible_tests', '').lower())
            success_checks.append('enzyme' in data.get('pathology_details', {}).get('chemical_composition', '').lower())
            
            if all(success_checks):
                self.log_result(
                    "Admin Pathology Product Creation",
                    True,
                    f"Admin pathology product created with details (ID: {data['id']})",
                    data
                )
            else:
                self.log_result(
                    "Admin Pathology Product Creation",
                    False,
                    f"Pathology product created but details incomplete. Checks: {success_checks}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Admin Pathology Product Creation",
                False,
                f"Failed to create pathology product. Status: {response.status_code if response else 'No response'}",
                error_data
            )

        # Supplier creates pathology product
        supplier_pathology_data = {
            'name': 'Urine Test Strips',
            'description': 'Multi-parameter urine analysis strips',
            'category': self.created_items['categories'][0],
            'brand': self.created_items['brands'][0],
            'product_type': 'pathology',
            'price': '29.99',
            'stock': 150,
            'pathology_details': {
                'compatible_tests': 'Protein, Glucose, Ketones, pH, Specific Gravity',
                'chemical_composition': 'Chromogenic reagents, pH indicators',
                'storage_condition': 'Store below 30°C, keep container tightly closed'
            }
        }
        
        response = self.make_request('POST', '/api/products/products/', supplier_pathology_data, self.supplier_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['products'].append(data['id'])
            
            success_checks = []
            success_checks.append(data.get('status') == 'pending')
            success_checks.append(data.get('pathology_details') is not None)
            success_checks.append('protein' in data.get('pathology_details', {}).get('compatible_tests', '').lower())
            
            if all(success_checks):
                self.log_result(
                    "Supplier Pathology Product Creation",
                    True,
                    f"Supplier pathology product created and pending (ID: {data['id']})",
                    data
                )
            else:
                self.log_result(
                    "Supplier Pathology Product Creation",
                    False,
                    f"Supplier pathology product issues. Checks: {success_checks}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Supplier Pathology Product Creation",
                False,
                f"Failed to create supplier pathology product. Status: {response.status_code if response else 'No response'}",
                error_data
            )

    def test_product_updates(self):
        """Test product PUT operations"""
        print("\n🧪 Testing Product Updates...")
        
        if not self.created_items['products']:
            self.log_result("Product Updates", False, "No products available for testing updates")
            return
        
        product_id = self.created_items['products'][0]
        
        # Test updating medicine product
        update_data = {
            'name': 'Updated Medicine Product Name',
            'description': 'Updated description for medicine product',
            'price': '149.99',
            'stock': 75,
            'medicine_details': {
                'composition': 'Updated Paracetamol 650mg, Caffeine 40mg',
                'quantity': '15 tablets',
                'manufacturer': 'Updated Pharma Ltd',
                'batch_number': 'UPD001',
                'prescription_required': False
            }
        }
        
        response = self.make_request('PUT', f'/api/products/products/{product_id}/', update_data, self.admin_token)
        
        if response and response.status_code == 200:
            data = response.json()
            
            success_checks = []
            success_checks.append(data.get('name') == update_data['name'])
            success_checks.append(float(data.get('price', 0)) == float(update_data['price']))
            success_checks.append(data.get('medicine_details', {}).get('composition') == update_data['medicine_details']['composition'])
            
            if all(success_checks):
                self.log_result(
                    "Admin Product Update",
                    True,
                    f"Admin successfully updated product (ID: {product_id})",
                    data
                )
            else:
                self.log_result(
                    "Admin Product Update",
                    False,
                    f"Product update incomplete. Checks: {success_checks}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Admin Product Update",
                False,
                f"Failed to update product. Status: {response.status_code if response else 'No response'}",
                error_data
            )

    def test_variant_creation(self):
        """Test product variant creation with attributes"""
        print("\n🧪 Testing Product Variant Creation...")
        
        if not self.created_items['products'] or not self.created_items['attribute_values']:
            self.log_result("Variant Creation", False, "Missing products or attribute values for testing")
            return
        
        product_id = self.created_items['products'][0]
        
        # Test creating variant with attributes
        variant_data = {
            'product': product_id,
            'price': '109.99',
            'additional_price': '10.00',
            'stock': 30,
            'is_active': True,
            'attribute_ids': self.created_items['attribute_values'][:3]  # Use first 3 attribute values
        }
        
        response = self.make_request('POST', '/api/products/variants/', variant_data, self.admin_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['variants'].append(data['id'])
            
            success_checks = []
            success_checks.append(data.get('product') == product_id)
            success_checks.append(float(data.get('price', 0)) == float(variant_data['price']))
            success_checks.append(data.get('sku') is not None)  # SKU should be auto-generated
            success_checks.append(len(data.get('attributes', [])) > 0)  # Should have attributes
            
            if all(success_checks):
                self.log_result(
                    "Admin Variant Creation",
                    True,
                    f"Admin variant created with attributes (ID: {data['id']}, SKU: {data.get('sku')})",
                    data
                )
            else:
                self.log_result(
                    "Admin Variant Creation",
                    False,
                    f"Variant creation incomplete. Checks: {success_checks}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Admin Variant Creation",
                False,
                f"Failed to create variant. Status: {response.status_code if response else 'No response'}",
                error_data
            )

        # Test supplier variant creation (should be pending)
        supplier_variant_data = {
            'product': self.created_items['products'][-1] if len(self.created_items['products']) > 1 else product_id,
            'price': '89.99',
            'stock': 20,
            'is_active': True,
            'attribute_ids': self.created_items['attribute_values'][3:6] if len(self.created_items['attribute_values']) > 3 else []
        }
        
        response = self.make_request('POST', '/api/products/variants/', supplier_variant_data, self.supplier_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.created_items['variants'].append(data['id'])
            
            success_checks = []
            success_checks.append(data.get('product') == supplier_variant_data['product'])
            success_checks.append(data.get('sku') is not None)
            
            if all(success_checks):
                self.log_result(
                    "Supplier Variant Creation",
                    True,
                    f"Supplier variant created (ID: {data['id']}, SKU: {data.get('sku')})",
                    data
                )
            else:
                self.log_result(
                    "Supplier Variant Creation",
                    False,
                    f"Supplier variant creation incomplete. Checks: {success_checks}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Supplier Variant Creation",
                False,
                f"Failed to create supplier variant. Status: {response.status_code if response else 'No response'}",
                error_data
            )

    def test_variant_updates(self):
        """Test variant PUT operations"""
        print("\n🧪 Testing Variant Updates...")
        
        if not self.created_items['variants']:
            self.log_result("Variant Updates", False, "No variants available for testing updates")
            return
        
        variant_id = self.created_items['variants'][0]
        
        update_data = {
            'price': '119.99',
            'stock': 45,
            'is_active': True,
            'attribute_ids': self.created_items['attribute_values'][-2:] if len(self.created_items['attribute_values']) >= 2 else []
        }
        
        response = self.make_request('PUT', f'/api/products/variants/{variant_id}/', update_data, self.admin_token)
        
        if response and response.status_code == 200:
            data = response.json()
            
            success_checks = []
            success_checks.append(float(data.get('price', 0)) == float(update_data['price']))
            success_checks.append(data.get('stock') == update_data['stock'])
            
            if all(success_checks):
                self.log_result(
                    "Admin Variant Update",
                    True,
                    f"Admin successfully updated variant (ID: {variant_id})",
                    data
                )
            else:
                self.log_result(
                    "Admin Variant Update",
                    False,
                    f"Variant update incomplete. Checks: {success_checks}",
                    data
                )
        else:
            error_data = response.json() if response else {}
            self.log_result(
                "Admin Variant Update",
                False,
                f"Failed to update variant. Status: {response.status_code if response else 'No response'}",
                error_data
            )

    def test_admin_approval_workflow(self):
        """Test admin approval/rejection of supplier content"""
        print("\n🧪 Testing Admin Approval Workflow...")
        
        # Find pending items created by suppliers
        pending_brands = [bid for bid in self.created_items['brands']]
        pending_categories = [cid for cid in self.created_items['categories']]
        pending_products = [pid for pid in self.created_items['products']]
        
        # Test brand approval
        if pending_brands:
            brand_id = pending_brands[-1]  # Get last created brand (likely supplier's)
            
            response = self.make_request('POST', f'/api/products/admin/brands/{brand_id}/approve/', {}, self.admin_token)
            
            if response and response.status_code == 200:
                data = response.json()
                if 'approved' in data.get('message', '').lower():
                    self.log_result(
                        "Admin Brand Approval",
                        True,
                        f"Admin successfully approved brand {brand_id}",
                        data
                    )
                else:
                    self.log_result(
                        "Admin Brand Approval",
                        False,
                        f"Brand approval message unclear: {data.get('message')}",
                        data
                    )
            else:
                error_data = response.json() if response else {}
                self.log_result(
                    "Admin Brand Approval",
                    False,
                    f"Failed to approve brand. Status: {response.status_code if response else 'No response'}",
                    error_data
                )

        # Test category rejection
        if len(pending_categories) > 1:
            category_id = pending_categories[-1]  # Get last created category
            
            rejection_data = {
                'reason': 'Category name too generic, please be more specific'
            }
            
            response = self.make_request('POST', f'/api/products/admin/categories/{category_id}/reject/', rejection_data, self.admin_token)
            
            if response and response.status_code == 200:
                data = response.json()
                if 'rejected' in data.get('message', '').lower():
                    self.log_result(
                        "Admin Category Rejection",
                        True,
                        f"Admin successfully rejected category {category_id}",
                        data
                    )
                else:
                    self.log_result(
                        "Admin Category Rejection",
                        False,
                        f"Category rejection message unclear: {data.get('message')}",
                        data
                    )
            else:
                error_data = response.json() if response else {}
                self.log_result(
                    "Admin Category Rejection",
                    False,
                    f"Failed to reject category. Status: {response.status_code if response else 'No response'}",
                    error_data
                )

        # Test product approval
        if pending_products:
            product_id = pending_products[-1]  # Get last created product
            
            response = self.make_request('POST', f'/api/products/admin/products/{product_id}/approve/', {}, self.admin_token)
            
            if response and response.status_code == 200:
                data = response.json()
                if 'approved' in data.get('message', '').lower():
                    self.log_result(
                        "Admin Product Approval",
                        True,
                        f"Admin successfully approved product {product_id}",
                        data
                    )
                else:
                    self.log_result(
                        "Admin Product Approval",
                        False,
                        f"Product approval message unclear: {data.get('message')}",
                        data
                    )
            else:
                error_data = response.json() if response else {}
                self.log_result(
                    "Admin Product Approval",
                    False,
                    f"Failed to approve product. Status: {response.status_code if response else 'No response'}",
                    error_data
                )

        # Test bulk approval
        bulk_data = {
            'brand_ids': pending_brands[:1] if pending_brands else [],
            'category_ids': pending_categories[:1] if pending_categories else [],
            'product_ids': pending_products[:1] if pending_products else []
        }
        
        if any(bulk_data.values()):
            response = self.make_request('POST', '/api/products/admin/bulk-approve/', bulk_data, self.admin_token)
            
            if response and response.status_code == 200:
                data = response.json()
                if 'completed' in data.get('message', '').lower():
                    self.log_result(
                        "Admin Bulk Approval",
                        True,
                        f"Admin successfully completed bulk approval",
                        data
                    )
                else:
                    self.log_result(
                        "Admin Bulk Approval",
                        False,
                        f"Bulk approval message unclear: {data.get('message')}",
                        data
                    )
            else:
                error_data = response.json() if response else {}
                self.log_result(
                    "Admin Bulk Approval",
                    False,
                    f"Failed bulk approval. Status: {response.status_code if response else 'No response'}",
                    error_data
                )

    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE PRODUCTS POST/PUT TEST REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📈 CREATED ITEMS")
        for item_type, items in self.created_items.items():
            print(f"{item_type.capitalize()}: {len(items)} items")
        
        print(f"\n📋 DETAILED TEST RESULTS")
        print("-" * 80)
        
        categories = {
            'Brand Tests': [],
            'Category Tests': [],
            'Product Tests': [],
            'Variant Tests': [],
            'Admin Workflow Tests': []
        }
        
        for result in self.test_results:
            test_name = result['test']
            if 'Brand' in test_name:
                categories['Brand Tests'].append(result)
            elif 'Category' in test_name:
                categories['Category Tests'].append(result)
            elif 'Product' in test_name:
                categories['Product Tests'].append(result)
            elif 'Variant' in test_name:
                categories['Variant Tests'].append(result)
            elif 'Admin' in test_name or 'Approval' in test_name:
                categories['Admin Workflow Tests'].append(result)
        
        for category, tests in categories.items():
            if tests:
                print(f"\n🔸 {category}")
                for test in tests:
                    status = "✅" if test['success'] else "❌"
                    print(f"  {status} {test['test']}: {test['details']}")
        
        print(f"\n" + "="*80)
        
        if success_rate == 100:
            print("🎉 ALL TESTS PASSED! 100% SUCCESS RATE")
        elif success_rate >= 90:
            print(f"🎯 EXCELLENT! {success_rate:.1f}% success rate")
        elif success_rate >= 75:
            print(f"👍 GOOD! {success_rate:.1f}% success rate")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% success rate")
        
        print("="*80)
        
        # Save detailed report to file
        report_filename = f"comprehensive_products_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        detailed_report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': success_rate,
                'timestamp': datetime.now().isoformat()
            },
            'created_items': self.created_items,
            'test_results': self.test_results
        }
        
        try:
            with open(report_filename, 'w') as f:
                json.dump(detailed_report, f, indent=2, default=str)
            print(f"📄 Detailed report saved: {report_filename}")
        except Exception as e:
            print(f"❌ Failed to save report: {str(e)}")

    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Comprehensive Products POST/PUT Test Suite...")
        print("="*80)
        
        # Setup
        if not self.setup_users_and_tokens():
            print("❌ Failed to setup users and tokens. Aborting tests.")
            return False
        
        if not self.setup_attributes():
            print("❌ Failed to setup attributes. Aborting tests.")
            return False
        
        # Run all tests in order
        self.test_brand_creation()
        self.test_brand_updates()
        self.test_category_creation()
        self.test_category_updates()
        self.test_medicine_product_creation()
        self.test_equipment_product_creation()
        self.test_pathology_product_creation()
        self.test_product_updates()
        self.test_variant_creation()
        self.test_variant_updates()
        self.test_admin_approval_workflow()
        
        # Generate final report
        self.generate_comprehensive_report()
        
        return True


def main():
    """Main execution function"""
    test_suite = ComprehensiveProductTestSuite()
    
    try:
        success = test_suite.run_all_tests()
        
        if success:
            print("\n✅ Test suite completed successfully!")
            return 0
        else:
            print("\n❌ Test suite failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Test suite interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test suite crashed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)