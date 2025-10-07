#!/usr/bin/env python3
"""
Comprehensive Product API Test Suite - Direct Django Testing
Tests all product-related endpoints using Django's test client
"""

import os
import sys
import json
from decimal import Decimal
from datetime import datetime, timedelta
from io import BytesIO
import base64

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
import django
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import (
    Product, ProductCategory, Brand, ProductVariant, 
    MedicineDetails, EquipmentDetails, PathologyDetails,
    ProductAttribute, ProductAttributeValue, ProductImage,
    SupplierProductPrice, ProductReview
)

User = get_user_model()

class ComprehensiveProductAPITest:
    def __init__(self):
        self.client = APIClient()
        self.admin_user = None
        self.supplier_user = None
        self.regular_user = None
        self.test_results = []
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

    def log_result(self, test_name, success, details, response_data=None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()

    def setup_test_users(self):
        """Create test users with different roles"""
        try:
            # Create admin user
            self.admin_user, created = User.objects.get_or_create(
                email='admin@medixmall.com',
                defaults={
                    'full_name': 'Admin User',
                    'contact': '9876543210',
                    'role': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                    'email_verified': True
                }
            )
            if created:
                self.admin_user.set_password('admin123')
                self.admin_user.save()

            # Create supplier user
            self.supplier_user, created = User.objects.get_or_create(
                email='supplier@medixmall.com',
                defaults={
                    'full_name': 'Supplier User',
                    'contact': '9876543211',
                    'role': 'supplier',
                    'email_verified': True
                }
            )
            if created:
                self.supplier_user.set_password('supplier123')
                self.supplier_user.save()

            # Create regular user
            self.regular_user, created = User.objects.get_or_create(
                email='user@medixmall.com',
                defaults={
                    'full_name': 'Regular User',
                    'contact': '9876543212',
                    'role': 'user',
                    'email_verified': True
                }
            )
            if created:
                self.regular_user.set_password('user123')
                self.regular_user.save()

            self.log_result("Setup Test Users", True, "Test users created successfully")
            return True
        except Exception as e:
            self.log_result("Setup Test Users", False, f"Failed to setup users: {str(e)}")
            return False

    def authenticate_user(self, user):
        """Authenticate user and set client credentials"""
        try:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            return True
        except Exception as e:
            return False

    def test_create_product_categories(self):
        """Test creating product categories with admin user"""
        self.authenticate_user(self.admin_user)
        
        categories_data = [
            {
                'name': 'Medicines',
                'icon': 'https://via.placeholder.com/50x50/blue/white?text=Med',
                'parent': None,
                'is_publish': True,
                'status': 'published'
            },
            {
                'name': 'Medical Equipment',
                'icon': 'https://via.placeholder.com/50x50/green/white?text=Eq',
                'parent': None,
                'is_publish': True,
                'status': 'published'
            },
            {
                'name': 'Pathology',
                'icon': 'https://via.placeholder.com/50x50/red/white?text=Path',
                'parent': None,
                'is_publish': True,
                'status': 'published'
            }
        ]

        for category_data in categories_data:
            try:
                response = self.client.post('/api/products/categories/', category_data, format='json')
                
                if response.status_code == 201:
                    created_category = response.json()
                    self.created_entities['categories'].append(created_category)
                    self.log_result(
                        f"Create Category: {category_data['name']}", 
                        True, 
                        f"Category created with ID: {created_category['id']}"
                    )
                else:
                    self.log_result(
                        f"Create Category: {category_data['name']}", 
                        False, 
                        f"Failed to create category - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(
                    f"Create Category: {category_data['name']}", 
                    False, 
                    f"Exception: {str(e)}"
                )

    def test_create_brands(self):
        """Test creating brands with admin user"""
        self.authenticate_user(self.admin_user)
        
        brands_data = [
            {
                'name': 'Pfizer',
                'image': 'https://via.placeholder.com/100x100/blue/white?text=Pfizer'
            },
            {
                'name': 'Johnson & Johnson',
                'image': 'https://via.placeholder.com/100x100/red/white?text=J&J'
            },
            {
                'name': 'Roche',
                'image': 'https://via.placeholder.com/100x100/green/white?text=Roche'
            }
        ]

        for brand_data in brands_data:
            try:
                response = self.client.post('/api/products/brands/', brand_data, format='json')
                
                if response.status_code == 201:
                    created_brand = response.json()
                    self.created_entities['brands'].append(created_brand)
                    self.log_result(
                        f"Create Brand: {brand_data['name']}", 
                        True, 
                        f"Brand created with ID: {created_brand['id']}"
                    )
                else:
                    self.log_result(
                        f"Create Brand: {brand_data['name']}", 
                        False, 
                        f"Failed to create brand - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(
                    f"Create Brand: {brand_data['name']}", 
                    False, 
                    f"Exception: {str(e)}"
                )

    def test_create_product_attributes(self):
        """Test creating product attributes"""
        self.authenticate_user(self.admin_user)
        
        attributes_data = [
            {'name': 'Size'},
            {'name': 'Color'},
            {'name': 'Dosage'},
            {'name': 'Pack Size'},
            {'name': 'Strength'}
        ]

        for attr_data in attributes_data:
            try:
                response = self.client.post('/api/products/attributes/', attr_data, format='json')
                
                if response.status_code == 201:
                    created_attr = response.json()
                    self.created_entities['attributes'].append(created_attr)
                    self.log_result(
                        f"Create Attribute: {attr_data['name']}", 
                        True, 
                        f"Attribute created with ID: {created_attr['id']}"
                    )
                else:
                    self.log_result(
                        f"Create Attribute: {attr_data['name']}", 
                        False, 
                        f"Failed to create attribute - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(
                    f"Create Attribute: {attr_data['name']}", 
                    False, 
                    f"Exception: {str(e)}"
                )

    def test_create_attribute_values(self):
        """Test creating attribute values"""
        if not self.created_entities['attributes']:
            self.log_result("Create Attribute Values", False, "No attributes available")
            return

        self.authenticate_user(self.admin_user)
        
        attribute_values = {
            'Size': ['Small', 'Medium', 'Large'],
            'Color': ['Red', 'Blue', 'Green'],
            'Dosage': ['5mg', '10mg', '20mg'],
            'Pack Size': ['10 tablets', '30 tablets', '100 tablets'],
            'Strength': ['Low', 'Medium', 'High']
        }

        for attr in self.created_entities['attributes']:
            attr_name = attr['name']
            if attr_name in attribute_values:
                for value in attribute_values[attr_name]:
                    try:
                        response = self.client.post('/api/products/attribute-values/', {
                            'attribute': attr['id'],
                            'value': value
                        }, format='json')
                        
                        if response.status_code == 201:
                            created_value = response.json()
                            self.created_entities['attribute_values'].append(created_value)
                            self.log_result(
                                f"Create Attribute Value: {attr_name} - {value}", 
                                True, 
                                f"Value created with ID: {created_value['id']}"
                            )
                        else:
                            self.log_result(
                                f"Create Attribute Value: {attr_name} - {value}", 
                                False, 
                                f"Failed to create value - Status: {response.status_code}",
                                response.json() if hasattr(response, 'json') else response.data
                            )
                    except Exception as e:
                        self.log_result(
                            f"Create Attribute Value: {attr_name} - {value}", 
                            False, 
                            f"Exception: {str(e)}"
                        )

    def test_create_medicine_product(self, user_type='admin'):
        """Test creating medicine type product"""
        if not self.created_entities['categories'] or not self.created_entities['brands']:
            self.log_result(f"Create Medicine Product ({user_type})", False, "Categories or brands not available")
            return

        user = self.admin_user if user_type == 'admin' else self.supplier_user
        self.authenticate_user(user)
        
        medicine_data = {
            'name': f'Paracetamol 500mg ({user_type})',
            'product_type': 'medicine',
            'category': self.created_entities['categories'][0]['id'],
            'brand': self.created_entities['brands'][0]['id'],
            'description': 'Pain relief medication',
            'price': '15.50',
            'stock': 100,
            'image': 'https://via.placeholder.com/200x200/blue/white?text=Med',
            'specifications': {
                'active_ingredient': 'Paracetamol',
                'strength': '500mg'
            },
            'medicine_details': {
                'composition': 'Paracetamol 500mg',
                'quantity': '10 tablets',
                'manufacturer': 'Test Pharma Ltd',
                'batch_number': f'BTH{datetime.now().strftime("%Y%m%d")}',
                'prescription_required': False,
                'form': 'Tablet',
                'pack_size': '10 tablets'
            }
        }

        try:
            response = self.client.post('/api/products/products/', medicine_data, format='json')
            
            if response.status_code == 201:
                created_product = response.json()
                self.created_entities['products'].append(created_product)
                self.log_result(
                    f"Create Medicine Product ({user_type})", 
                    True, 
                    f"Medicine product created with ID: {created_product['id']}"
                )
            else:
                self.log_result(
                    f"Create Medicine Product ({user_type})", 
                    False, 
                    f"Failed to create medicine product - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result(
                f"Create Medicine Product ({user_type})", 
                False, 
                f"Exception: {str(e)}"
            )

    def test_create_equipment_product(self, user_type='admin'):
        """Test creating equipment type product"""
        if not self.created_entities['categories'] or not self.created_entities['brands']:
            self.log_result(f"Create Equipment Product ({user_type})", False, "Categories or brands not available")
            return

        user = self.admin_user if user_type == 'admin' else self.supplier_user
        self.authenticate_user(user)
        
        equipment_data = {
            'name': f'Digital Thermometer ({user_type})',
            'product_type': 'equipment',
            'category': self.created_entities['categories'][1]['id'] if len(self.created_entities['categories']) > 1 else self.created_entities['categories'][0]['id'],
            'brand': self.created_entities['brands'][1]['id'] if len(self.created_entities['brands']) > 1 else self.created_entities['brands'][0]['id'],
            'description': 'Digital medical thermometer with LCD display',
            'price': '25.99',
            'stock': 50,
            'image': 'https://via.placeholder.com/200x200/green/white?text=Eq',
            'specifications': {
                'measurement_range': '32-42°C',
                'accuracy': '±0.1°C'
            },
            'equipment_details': {
                'model_number': 'DT-2024',
                'warranty_period': '2 years',
                'usage_type': 'Personal/Clinical',
                'technical_specifications': 'LCD display, Auto shut-off, Memory function',
                'power_requirement': '1.5V AAA battery',
                'equipment_type': 'Diagnostic Equipment'
            }
        }

        try:
            response = self.client.post('/api/products/products/', equipment_data, format='json')
            
            if response.status_code == 201:
                created_product = response.json()
                self.created_entities['products'].append(created_product)
                self.log_result(
                    f"Create Equipment Product ({user_type})", 
                    True, 
                    f"Equipment product created with ID: {created_product['id']}"
                )
            else:
                self.log_result(
                    f"Create Equipment Product ({user_type})", 
                    False, 
                    f"Failed to create equipment product - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result(
                f"Create Equipment Product ({user_type})", 
                False, 
                f"Exception: {str(e)}"
            )

    def test_create_pathology_product(self, user_type='admin'):
        """Test creating pathology type product"""
        if not self.created_entities['categories'] or not self.created_entities['brands']:
            self.log_result(f"Create Pathology Product ({user_type})", False, "Categories or brands not available")
            return

        user = self.admin_user if user_type == 'admin' else self.supplier_user
        self.authenticate_user(user)
        
        pathology_data = {
            'name': f'Blood Glucose Test Strips ({user_type})',
            'product_type': 'pathology',
            'category': self.created_entities['categories'][2]['id'] if len(self.created_entities['categories']) > 2 else self.created_entities['categories'][0]['id'],
            'brand': self.created_entities['brands'][2]['id'] if len(self.created_entities['brands']) > 2 else self.created_entities['brands'][0]['id'],
            'description': 'High accuracy blood glucose test strips',
            'price': '35.75',
            'stock': 75,
            'image': 'https://via.placeholder.com/200x200/red/white?text=Path',
            'specifications': {
                'test_type': 'Blood Glucose',
                'sample_size': '0.5 μL'
            },
            'pathology_details': {
                'compatible_tests': 'Blood glucose, HbA1c',
                'chemical_composition': 'Glucose oxidase enzyme strips',
                'storage_condition': 'Store at 2-30°C, dry place'
            }
        }

        try:
            response = self.client.post('/api/products/products/', pathology_data, format='json')
            
            if response.status_code == 201:
                created_product = response.json()
                self.created_entities['products'].append(created_product)
                self.log_result(
                    f"Create Pathology Product ({user_type})", 
                    True, 
                    f"Pathology product created with ID: {created_product['id']}"
                )
            else:
                self.log_result(
                    f"Create Pathology Product ({user_type})", 
                    False, 
                    f"Failed to create pathology product - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result(
                f"Create Pathology Product ({user_type})", 
                False, 
                f"Exception: {str(e)}"
            )

    def test_create_product_variants(self):
        """Test creating product variants"""
        if not self.created_entities['products'] or not self.created_entities['attribute_values']:
            self.log_result("Create Product Variants", False, "Products or attribute values not available")
            return

        self.authenticate_user(self.admin_user)
        
        product = self.created_entities['products'][0]
        
        # Get attribute values for variants
        dosage_values = [av for av in self.created_entities['attribute_values'] 
                        if any(attr['name'] == 'Dosage' and attr['id'] == av['attribute'] 
                               for attr in self.created_entities['attributes'])]

        variants_data = [
            {
                'product': product['id'],
                'attributes': [dosage_values[0]['id']] if dosage_values else [],
                'price': '12.50',
                'additional_price': '0.00',
                'stock': 150,
                'is_active': True
            },
            {
                'product': product['id'],
                'attributes': [dosage_values[1]['id']] if len(dosage_values) > 1 else [],
                'price': '15.50',
                'additional_price': '0.00',
                'stock': 100,
                'is_active': True
            }
        ]

        for i, variant_data in enumerate(variants_data):
            try:
                response = self.client.post('/api/products/variants/', variant_data, format='json')
                
                if response.status_code == 201:
                    created_variant = response.json()
                    self.created_entities['variants'].append(created_variant)
                    self.log_result(
                        f"Create Product Variant {i+1}", 
                        True, 
                        f"Variant created with ID: {created_variant['id']}"
                    )
                else:
                    self.log_result(
                        f"Create Product Variant {i+1}", 
                        False, 
                        f"Failed to create variant - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(
                    f"Create Product Variant {i+1}", 
                    False, 
                    f"Exception: {str(e)}"
                )

    def test_create_product_images(self):
        """Test creating product images"""
        if not self.created_entities['products']:
            self.log_result("Create Product Images", False, "No products available")
            return

        self.authenticate_user(self.admin_user)
        
        product = self.created_entities['products'][0]
        
        images_data = [
            {
                'product': product['id'],
                'variant': None,
                'image': 'https://via.placeholder.com/400x400/blue/white?text=Main',
                'alt_text': 'Main product image',
                'order': 1
            },
            {
                'product': product['id'],
                'variant': None,
                'image': 'https://via.placeholder.com/400x400/green/white?text=Side',
                'alt_text': 'Side view',
                'order': 2
            }
        ]

        # Add variant-specific image if variants exist
        if self.created_entities['variants']:
            variant = self.created_entities['variants'][0]
            images_data.append({
                'product': product['id'],
                'variant': variant['id'],
                'image': 'https://via.placeholder.com/400x400/red/white?text=Variant',
                'alt_text': 'Variant specific image',
                'order': 1
            })

        for i, image_data in enumerate(images_data):
            try:
                response = self.client.post('/api/products/images/', image_data, format='json')
                
                if response.status_code == 201:
                    created_image = response.json()
                    self.created_entities['images'].append(created_image)
                    self.log_result(
                        f"Create Product Image {i+1}", 
                        True, 
                        f"Image created with ID: {created_image['id']}"
                    )
                else:
                    self.log_result(
                        f"Create Product Image {i+1}", 
                        False, 
                        f"Failed to create image - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(
                    f"Create Product Image {i+1}", 
                    False, 
                    f"Exception: {str(e)}"
                )

    def test_create_supplier_prices(self):
        """Test creating supplier prices"""
        if not self.created_entities['variants']:
            self.log_result("Create Supplier Prices", False, "No variants available")
            return

        self.authenticate_user(self.supplier_user)
        
        variant = self.created_entities['variants'][0]
        
        supplier_prices_data = [
            {
                'product_variant': variant['id'],
                'price': '10.50',
                'pincode': '110001',
                'district': 'Central Delhi'
            },
            {
                'product_variant': variant['id'],
                'price': '11.00',
                'pincode': '400001',
                'district': 'Mumbai City'
            }
        ]

        for i, price_data in enumerate(supplier_prices_data):
            try:
                response = self.client.post('/api/products/supplier-prices/', price_data, format='json')
                
                if response.status_code == 201:
                    created_price = response.json()
                    self.created_entities['supplier_prices'].append(created_price)
                    self.log_result(
                        f"Create Supplier Price {i+1}", 
                        True, 
                        f"Price created with ID: {created_price['id']}"
                    )
                else:
                    self.log_result(
                        f"Create Supplier Price {i+1}", 
                        False, 
                        f"Failed to create price - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(
                    f"Create Supplier Price {i+1}", 
                    False, 
                    f"Exception: {str(e)}"
                )

    def test_create_product_reviews(self):
        """Test creating product reviews"""
        if not self.created_entities['products']:
            self.log_result("Create Product Reviews", False, "No products available")
            return

        self.authenticate_user(self.regular_user)
        
        product = self.created_entities['products'][0]
        
        reviews_data = [
            {
                'product': product['id'],
                'rating': 5,
                'comment': 'Excellent product, works as expected'
            },
            {
                'product': product['id'],
                'rating': 4,
                'comment': 'Good quality, fast delivery'
            }
        ]

        for i, review_data in enumerate(reviews_data):
            try:
                response = self.client.post('/api/products/reviews/', review_data, format='json')
                
                if response.status_code == 201:
                    created_review = response.json()
                    self.created_entities['reviews'].append(created_review)
                    self.log_result(
                        f"Create Product Review {i+1}", 
                        True, 
                        f"Review created with ID: {created_review['id']}"
                    )
                else:
                    self.log_result(
                        f"Create Product Review {i+1}", 
                        False, 
                        f"Failed to create review - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(
                    f"Create Product Review {i+1}", 
                    False, 
                    f"Exception: {str(e)}"
                )

    def test_unauthorized_access(self):
        """Test unauthorized access scenarios"""
        # Test creating category without admin permissions
        self.authenticate_user(self.regular_user)
        
        try:
            response = self.client.post('/api/products/categories/', {
                'name': 'Unauthorized Category'
            }, format='json')
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Unauthorized Category Creation", 
                    True, 
                    "Correctly blocked unauthorized access"
                )
            else:
                self.log_result(
                    "Unauthorized Category Creation", 
                    False, 
                    f"Should have blocked unauthorized access - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result(
                "Unauthorized Category Creation", 
                False, 
                f"Exception: {str(e)}"
            )

        # Test creating product without authentication
        self.client.credentials()  # Clear authentication
        
        try:
            response = self.client.post('/api/products/products/', {
                'name': 'Unauthorized Product'
            }, format='json')
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Unauthenticated Product Creation", 
                    True, 
                    "Correctly blocked unauthenticated access"
                )
            else:
                self.log_result(
                    "Unauthenticated Product Creation", 
                    False, 
                    f"Should have blocked unauthenticated access - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result(
                "Unauthenticated Product Creation", 
                False, 
                f"Exception: {str(e)}"
            )

    def run_all_post_tests(self):
        """Run all POST endpoint tests"""
        print("🚀 Starting Comprehensive Product API POST Tests (Direct Django)")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_users():
            return False

        # Test all POST endpoints
        print("\n📝 Testing Category Creation...")
        self.test_create_product_categories()
        
        print("\n🏷️ Testing Brand Creation...")
        self.test_create_brands()
        
        print("\n🔧 Testing Attribute Creation...")
        self.test_create_product_attributes()
        
        print("\n📊 Testing Attribute Values Creation...")
        self.test_create_attribute_values()
        
        print("\n💊 Testing Medicine Product Creation (Admin)...")
        self.test_create_medicine_product('admin')
        
        print("\n💊 Testing Medicine Product Creation (Supplier)...")
        self.test_create_medicine_product('supplier')
        
        print("\n🏥 Testing Equipment Product Creation (Admin)...")
        self.test_create_equipment_product('admin')
        
        print("\n🏥 Testing Equipment Product Creation (Supplier)...")
        self.test_create_equipment_product('supplier')
        
        print("\n🧪 Testing Pathology Product Creation (Admin)...")
        self.test_create_pathology_product('admin')
        
        print("\n🧪 Testing Pathology Product Creation (Supplier)...")
        self.test_create_pathology_product('supplier')
        
        print("\n🎯 Testing Product Variants Creation...")
        self.test_create_product_variants()
        
        print("\n🖼️ Testing Product Images Creation...")
        self.test_create_product_images()
        
        print("\n💰 Testing Supplier Prices Creation...")
        self.test_create_supplier_prices()
        
        print("\n⭐ Testing Product Reviews Creation...")
        self.test_create_product_reviews()
        
        print("\n🚫 Testing Unauthorized Access...")
        self.test_unauthorized_access()
        
        return True

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE POST ENDPOINTS TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 Created Entities Summary:")
        for entity_type, entities in self.created_entities.items():
            print(f"   {entity_type.title()}: {len(entities)}")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test_name']}: {result['details']}")
        
        print(f"\n✅ Test completed successfully!")
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'created_entities': self.created_entities,
            'detailed_results': self.test_results
        }


def main():
    """Main function to run the tests"""
    tester = ComprehensiveProductAPITest()
    
    try:
        success = tester.run_all_post_tests()
        report = tester.generate_test_report()
        
        # Save detailed results to JSON file
        with open('product_post_test_results_direct.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: product_post_test_results_direct.json")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)