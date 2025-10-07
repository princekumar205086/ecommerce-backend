#!/usr/bin/env python3
"""
Comprehensive Product API POST Endpoints Test Suite
Tests all product-related POST endpoints with different product types and variants
from both admin and supplier perspectives.
"""

import json
import requests
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import base64
from PIL import Image
from io import BytesIO

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from products.models import (
    Product, ProductCategory, Brand, ProductVariant, 
    MedicineDetails, EquipmentDetails, PathologyDetails,
    ProductAttribute, ProductAttributeValue, ProductImage,
    SupplierProductPrice, ProductReview
)

User = get_user_model()

class ProductPostAPITester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000/api"
        self.admin_token = None
        self.supplier_token = None
        self.user_token = None
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
        
    def log_result(self, test_name, success, details, response=None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'status_code': response.status_code if response else None,
            'response_data': response.json() if response and response.headers.get('content-type', '').startswith('application/json') else None
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        if response and not success:
            print(f"   Status: {response.status_code}")
            try:
                print(f"   Response: {response.json()}")
            except:
                print(f"   Response: {response.text}")
        print()

    def setup_test_users(self):
        """Create test users with different roles"""
        try:
            # Create admin user
            admin_user, created = User.objects.get_or_create(
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
                admin_user.set_password('admin123')
                admin_user.save()

            # Create supplier user
            supplier_user, created = User.objects.get_or_create(
                email='supplier@medixmall.com',
                defaults={
                    'full_name': 'Supplier User',
                    'contact': '9876543211',
                    'role': 'supplier',
                    'email_verified': True
                }
            )
            if created:
                supplier_user.set_password('supplier123')
                supplier_user.save()

            # Create regular user
            regular_user, created = User.objects.get_or_create(
                email='user@medixmall.com',
                defaults={
                    'full_name': 'Regular User',
                    'contact': '9876543212',
                    'role': 'user',
                    'email_verified': True
                }
            )
            if created:
                regular_user.set_password('user123')
                regular_user.save()

            self.log_result("Setup Test Users", True, "Test users created successfully")
            return True
        except Exception as e:
            self.log_result("Setup Test Users", False, f"Failed to setup users: {str(e)}")
            return False

    def authenticate_users(self):
        """Authenticate all test users and get tokens"""
        users = [
            ('admin@medixmall.com', 'admin123', 'admin'),
            ('supplier@medixmall.com', 'supplier123', 'supplier'),
            ('user@medixmall.com', 'user123', 'user')
        ]
        
        for email, password, role in users:
            try:
                response = requests.post(f"{self.base_url}/accounts/login/", data={
                    'email': email,
                    'password': password
                })
                
                if response.status_code == 200:
                    token = response.json().get('access_token')
                    if role == 'admin':
                        self.admin_token = token
                    elif role == 'supplier':
                        self.supplier_token = token
                    else:
                        self.user_token = token
                    self.log_result(f"Authenticate {role.title()}", True, f"Token obtained successfully")
                else:
                    self.log_result(f"Authenticate {role.title()}", False, f"Authentication failed: {response.status_code}")
                    return False
            except Exception as e:
                self.log_result(f"Authenticate {role.title()}", False, f"Authentication error: {str(e)}")
                return False
        
        return True

    def get_headers(self, token):
        """Get request headers with authentication"""
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def create_sample_image_data(self):
        """Create sample image data for testing"""
        # Create a simple image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_data = img_bytes.getvalue()
        
        # Encode to base64
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/jpeg;base64,{img_b64}"

    def test_create_product_categories(self):
        """Test creating product categories with admin user"""
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
            },
            {
                'name': 'Prescription Medicines',
                'icon': 'https://via.placeholder.com/50x50/yellow/black?text=Rx',
                'parent': 1,  # Will be updated after first category is created
                'is_publish': True,
                'status': 'published'
            }
        ]

        for i, category_data in enumerate(categories_data):
            try:
                # Update parent reference if needed
                if i == 3 and self.created_entities['categories']:
                    category_data['parent'] = self.created_entities['categories'][0]['id']

                response = requests.post(
                    f"{self.base_url}/products/categories/",
                    headers=self.get_headers(self.admin_token),
                    json=category_data
                )

                if response.status_code == 201:
                    created_category = response.json()
                    self.created_entities['categories'].append(created_category)
                    self.log_result(
                        f"Create Category: {category_data['name']}", 
                        True, 
                        f"Category created with ID: {created_category['id']}", 
                        response
                    )
                else:
                    self.log_result(
                        f"Create Category: {category_data['name']}", 
                        False, 
                        f"Failed to create category", 
                        response
                    )
            except Exception as e:
                self.log_result(
                    f"Create Category: {category_data['name']}", 
                    False, 
                    f"Exception: {str(e)}"
                )

    def test_create_brands(self):
        """Test creating brands with admin user"""
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
            },
            {
                'name': 'Abbott',
                'image': 'https://via.placeholder.com/100x100/purple/white?text=Abbott'
            }
        ]

        for brand_data in brands_data:
            try:
                response = requests.post(
                    f"{self.base_url}/products/brands/",
                    headers=self.get_headers(self.admin_token),
                    json=brand_data
                )

                if response.status_code == 201:
                    created_brand = response.json()
                    self.created_entities['brands'].append(created_brand)
                    self.log_result(
                        f"Create Brand: {brand_data['name']}", 
                        True, 
                        f"Brand created with ID: {created_brand['id']}", 
                        response
                    )
                else:
                    self.log_result(
                        f"Create Brand: {brand_data['name']}", 
                        False, 
                        f"Failed to create brand", 
                        response
                    )
            except Exception as e:
                self.log_result(
                    f"Create Brand: {brand_data['name']}", 
                    False, 
                    f"Exception: {str(e)}"
                )

    def test_create_product_attributes(self):
        """Test creating product attributes"""
        attributes_data = [
            {'name': 'Size'},
            {'name': 'Color'},
            {'name': 'Dosage'},
            {'name': 'Pack Size'},
            {'name': 'Strength'}
        ]

        for attr_data in attributes_data:
            try:
                response = requests.post(
                    f"{self.base_url}/products/attributes/",
                    headers=self.get_headers(self.admin_token),
                    json=attr_data
                )

                if response.status_code == 201:
                    created_attr = response.json()
                    self.created_entities['attributes'].append(created_attr)
                    self.log_result(
                        f"Create Attribute: {attr_data['name']}", 
                        True, 
                        f"Attribute created with ID: {created_attr['id']}", 
                        response
                    )
                else:
                    self.log_result(
                        f"Create Attribute: {attr_data['name']}", 
                        False, 
                        f"Failed to create attribute", 
                        response
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
            self.log_result("Create Attribute Values", False, "No attributes available to create values")
            return

        # Create values for each attribute
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
                        response = requests.post(
                            f"{self.base_url}/products/attribute-values/",
                            headers=self.get_headers(self.admin_token),
                            json={
                                'attribute': attr['id'],
                                'value': value
                            }
                        )

                        if response.status_code == 201:
                            created_value = response.json()
                            self.created_entities['attribute_values'].append(created_value)
                            self.log_result(
                                f"Create Attribute Value: {attr_name} - {value}", 
                                True, 
                                f"Value created with ID: {created_value['id']}", 
                                response
                            )
                        else:
                            self.log_result(
                                f"Create Attribute Value: {attr_name} - {value}", 
                                False, 
                                f"Failed to create value", 
                                response
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

        token = self.admin_token if user_type == 'admin' else self.supplier_token
        
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
            response = requests.post(
                f"{self.base_url}/products/products/",
                headers=self.get_headers(token),
                json=medicine_data
            )

            if response.status_code == 201:
                created_product = response.json()
                self.created_entities['products'].append(created_product)
                self.log_result(
                    f"Create Medicine Product ({user_type})", 
                    True, 
                    f"Medicine product created with ID: {created_product['id']}", 
                    response
                )
            else:
                self.log_result(
                    f"Create Medicine Product ({user_type})", 
                    False, 
                    f"Failed to create medicine product", 
                    response
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

        token = self.admin_token if user_type == 'admin' else self.supplier_token
        
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
            response = requests.post(
                f"{self.base_url}/products/products/",
                headers=self.get_headers(token),
                json=equipment_data
            )

            if response.status_code == 201:
                created_product = response.json()
                self.created_entities['products'].append(created_product)
                self.log_result(
                    f"Create Equipment Product ({user_type})", 
                    True, 
                    f"Equipment product created with ID: {created_product['id']}", 
                    response
                )
            else:
                self.log_result(
                    f"Create Equipment Product ({user_type})", 
                    False, 
                    f"Failed to create equipment product", 
                    response
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

        token = self.admin_token if user_type == 'admin' else self.supplier_token
        
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
            response = requests.post(
                f"{self.base_url}/products/products/",
                headers=self.get_headers(token),
                json=pathology_data
            )

            if response.status_code == 201:
                created_product = response.json()
                self.created_entities['products'].append(created_product)
                self.log_result(
                    f"Create Pathology Product ({user_type})", 
                    True, 
                    f"Pathology product created with ID: {created_product['id']}", 
                    response
                )
            else:
                self.log_result(
                    f"Create Pathology Product ({user_type})", 
                    False, 
                    f"Failed to create pathology product", 
                    response
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

        # Create variants for the first product
        product = self.created_entities['products'][0]
        
        # Get dosage attribute values
        dosage_values = [av for av in self.created_entities['attribute_values'] 
                        if any(attr['name'] == 'Dosage' for attr in self.created_entities['attributes'] 
                               if attr['id'] == av['attribute'])]
        
        # Get pack size attribute values  
        pack_values = [av for av in self.created_entities['attribute_values'] 
                      if any(attr['name'] == 'Pack Size' for attr in self.created_entities['attributes'] 
                             if attr['id'] == av['attribute'])]

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
                response = requests.post(
                    f"{self.base_url}/products/variants/",
                    headers=self.get_headers(self.admin_token),
                    json=variant_data
                )

                if response.status_code == 201:
                    created_variant = response.json()
                    self.created_entities['variants'].append(created_variant)
                    self.log_result(
                        f"Create Product Variant {i+1}", 
                        True, 
                        f"Variant created with ID: {created_variant['id']}", 
                        response
                    )
                else:
                    self.log_result(
                        f"Create Product Variant {i+1}", 
                        False, 
                        f"Failed to create variant", 
                        response
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
                response = requests.post(
                    f"{self.base_url}/products/images/",
                    headers=self.get_headers(self.admin_token),
                    json=image_data
                )

                if response.status_code == 201:
                    created_image = response.json()
                    self.created_entities['images'].append(created_image)
                    self.log_result(
                        f"Create Product Image {i+1}", 
                        True, 
                        f"Image created with ID: {created_image['id']}", 
                        response
                    )
                else:
                    self.log_result(
                        f"Create Product Image {i+1}", 
                        False, 
                        f"Failed to create image", 
                        response
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
                response = requests.post(
                    f"{self.base_url}/products/supplier-prices/",
                    headers=self.get_headers(self.supplier_token),
                    json=price_data
                )

                if response.status_code == 201:
                    created_price = response.json()
                    self.created_entities['supplier_prices'].append(created_price)
                    self.log_result(
                        f"Create Supplier Price {i+1}", 
                        True, 
                        f"Price created with ID: {created_price['id']}", 
                        response
                    )
                else:
                    self.log_result(
                        f"Create Supplier Price {i+1}", 
                        False, 
                        f"Failed to create price", 
                        response
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
                response = requests.post(
                    f"{self.base_url}/products/reviews/",
                    headers=self.get_headers(self.user_token),
                    json=review_data
                )

                if response.status_code == 201:
                    created_review = response.json()
                    self.created_entities['reviews'].append(created_review)
                    self.log_result(
                        f"Create Product Review {i+1}", 
                        True, 
                        f"Review created with ID: {created_review['id']}", 
                        response
                    )
                else:
                    self.log_result(
                        f"Create Product Review {i+1}", 
                        False, 
                        f"Failed to create review", 
                        response
                    )
            except Exception as e:
                self.log_result(
                    f"Create Product Review {i+1}", 
                    False, 
                    f"Exception: {str(e)}"
                )

    def test_unauthorized_access(self):
        """Test unauthorized access scenarios"""
        # Test creating category without admin token
        try:
            response = requests.post(
                f"{self.base_url}/products/categories/",
                headers=self.get_headers(self.user_token),
                json={'name': 'Unauthorized Category'}
            )
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Unauthorized Category Creation", 
                    True, 
                    "Correctly blocked unauthorized access", 
                    response
                )
            else:
                self.log_result(
                    "Unauthorized Category Creation", 
                    False, 
                    "Should have blocked unauthorized access", 
                    response
                )
        except Exception as e:
            self.log_result(
                "Unauthorized Category Creation", 
                False, 
                f"Exception: {str(e)}"
            )

        # Test creating product without authentication
        try:
            response = requests.post(
                f"{self.base_url}/products/products/",
                json={'name': 'Unauthorized Product'}
            )
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Unauthenticated Product Creation", 
                    True, 
                    "Correctly blocked unauthenticated access", 
                    response
                )
            else:
                self.log_result(
                    "Unauthenticated Product Creation", 
                    False, 
                    "Should have blocked unauthenticated access", 
                    response
                )
        except Exception as e:
            self.log_result(
                "Unauthenticated Product Creation", 
                False, 
                f"Exception: {str(e)}"
            )

    def run_all_post_tests(self):
        """Run all POST endpoint tests"""
        print("🚀 Starting Comprehensive Product API POST Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_users():
            return False
        
        if not self.authenticate_users():
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
    tester = ProductPostAPITester()
    
    try:
        success = tester.run_all_post_tests()
        report = tester.generate_test_report()
        
        # Save detailed results to JSON file
        with open('product_post_test_results.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: product_post_test_results.json")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)