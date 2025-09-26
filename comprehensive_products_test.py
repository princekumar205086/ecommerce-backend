#!/usr/bin/env python
"""
Comprehensive Products App Testing Script
Tests all product endpoints, types, categories, brands, and variants
"""
import os
import sys
import json
import requests
from datetime import datetime, date
from io import BytesIO
from PIL import Image
import base64

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class ProductsAPITester:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:8000'
        self.client = APIClient()
        self.results = {
            'categories': [],
            'brands': [], 
            'products': [],
            'variants': [],
            'images': [],
            'reviews': [],
            'public_endpoints': []
        }
        self.setup_test_users()
        
    def setup_test_users(self):
        """Create test users for different roles"""
        self.admin_user = self.get_or_create_user(
            email='admin@test.com',
            role='admin',
            full_name='Test Admin',
            is_staff=True,
            is_superuser=True
        )
        
        self.supplier_user = self.get_or_create_user(
            email='supplier@test.com',
            role='supplier',
            full_name='Test Supplier'
        )
        
        self.customer_user = self.get_or_create_user(
            email='customer@test.com',
            role='user',
            full_name='Test Customer'
        )
        
        print(f"✅ Test users created - Admin: {self.admin_user.id}, Supplier: {self.supplier_user.id}, Customer: {self.customer_user.id}")
        
    def get_or_create_user(self, email, role, full_name, is_staff=False, is_superuser=False):
        """Get or create a user with specified role"""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email,
                password='testpass123',
                full_name=full_name,
                role=role,
                is_staff=is_staff,
                is_superuser=is_superuser,
                is_active=True,
                email_verified=True
            )
        return user
    
    def get_jwt_token(self, user):
        """Get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate_as(self, user):
        """Authenticate client as specific user"""
        token = self.get_jwt_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token
        
    def create_test_image(self, name="test_image.jpg"):
        """Create a test image for file uploads"""
        image = Image.new('RGB', (100, 100), color='red')
        img_buffer = BytesIO()
        image.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        img_buffer.name = name
        return img_buffer
        
    def log_result(self, category, endpoint, method, payload, response, status_code):
        """Log test result"""
        result = {
            'endpoint': endpoint,
            'method': method,
            'payload': payload,
            'response_status': status_code,
            'response_data': response if isinstance(response, dict) else str(response),
            'timestamp': datetime.now().isoformat(),
            'success': 200 <= status_code < 300
        }
        self.results[category].append(result)
        
    def test_categories(self):
        """Test category endpoints"""
        print("\n=== TESTING CATEGORIES ===")
        
        # Test 1: Create category as admin
        self.authenticate_as(self.admin_user)
        category_data = {
            'name': 'Test Medicine Category Admin'
        }
        
        # Try with image file
        with self.create_test_image("category_admin.jpg") as img:
            files = {'icon_file': img}
            response = self.client.post('/api/products/categories/', data=category_data, files=files, format='multipart')
        
        self.log_result('categories', '/api/products/categories/', 'POST', category_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Admin category creation: {response.status_code} - {response.data if hasattr(response, 'data') else 'No data'}")
        
        admin_category_id = None
        if hasattr(response, 'data') and 'id' in response.data:
            admin_category_id = response.data['id']
            
        # Test 2: Create category as supplier (should need approval)
        self.authenticate_as(self.supplier_user)
        supplier_category_data = {
            'name': 'Test Equipment Category Supplier'
        }
        
        response = self.client.post('/api/products/categories/', data=supplier_category_data)
        self.log_result('categories', '/api/products/categories/', 'POST', supplier_category_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Supplier category creation: {response.status_code} - {response.data if hasattr(response, 'data') else 'No data'}")
        
        supplier_category_id = None
        if hasattr(response, 'data') and 'id' in response.data:
            supplier_category_id = response.data['id']
            
        # Test 3: Create subcategory
        if admin_category_id:
            subcategory_data = {
                'name': 'Test Subcategory',
                'parent': admin_category_id
            }
            response = self.client.post('/api/products/categories/', data=subcategory_data)
            self.log_result('categories', '/api/products/categories/', 'POST', subcategory_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"Subcategory creation: {response.status_code}")
        
        # Test 4: List categories (anonymous)
        self.client.credentials()  # Remove authentication
        response = self.client.get('/api/products/categories/')
        self.log_result('categories', '/api/products/categories/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Anonymous category list: {response.status_code} - Found {len(response.data) if hasattr(response, 'data') and isinstance(response.data, list) else 0} categories")
        
        # Test 5: List categories as admin (should see all)
        self.authenticate_as(self.admin_user)
        response = self.client.get('/api/products/categories/')
        self.log_result('categories', '/api/products/categories/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Admin category list: {response.status_code} - Found {len(response.data) if hasattr(response, 'data') and isinstance(response.data, list) else 0} categories")
        
        # Test 6: Approve supplier category as admin
        if supplier_category_id:
            response = self.client.post(f'/api/products/admin/categories/{supplier_category_id}/approve/')
            self.log_result('categories', f'/api/products/admin/categories/{supplier_category_id}/approve/', 'POST', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"Category approval: {response.status_code}")
        
        return admin_category_id, supplier_category_id
        
    def test_brands(self):
        """Test brand endpoints"""
        print("\n=== TESTING BRANDS ===")
        
        # Test 1: Create brand as admin
        self.authenticate_as(self.admin_user)
        brand_data = {
            'name': 'Test Brand Admin'
        }
        
        # Try with image file
        with self.create_test_image("brand_admin.jpg") as img:
            files = {'image_file': img}
            response = self.client.post('/api/products/brands/', data=brand_data, files=files, format='multipart')
        
        self.log_result('brands', '/api/products/brands/', 'POST', brand_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Admin brand creation: {response.status_code} - {response.data if hasattr(response, 'data') else 'No data'}")
        
        admin_brand_id = None
        if hasattr(response, 'data') and 'id' in response.data:
            admin_brand_id = response.data['id']
            
        # Test 2: Create brand as supplier
        self.authenticate_as(self.supplier_user)
        supplier_brand_data = {
            'name': 'Test Brand Supplier'
        }
        
        response = self.client.post('/api/products/brands/', data=supplier_brand_data)
        self.log_result('brands', '/api/products/brands/', 'POST', supplier_brand_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Supplier brand creation: {response.status_code} - {response.data if hasattr(response, 'data') else 'No data'}")
        
        supplier_brand_id = None
        if hasattr(response, 'data') and 'id' in response.data:
            supplier_brand_id = response.data['id']
            
        # Test 3: List brands
        response = self.client.get('/api/products/brands/')
        self.log_result('brands', '/api/products/brands/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Brand list: {response.status_code} - Found {len(response.data) if hasattr(response, 'data') and isinstance(response.data, list) else 0} brands")
        
        # Test 4: Approve supplier brand as admin
        if supplier_brand_id:
            self.authenticate_as(self.admin_user)
            response = self.client.post(f'/api/products/admin/brands/{supplier_brand_id}/approve/')
            self.log_result('brands', f'/api/products/admin/brands/{supplier_brand_id}/approve/', 'POST', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"Brand approval: {response.status_code}")
        
        return admin_brand_id, supplier_brand_id
        
    def test_products(self, category_id, brand_id):
        """Test product endpoints for all product types"""
        print("\n=== TESTING PRODUCTS ===")
        
        created_products = []
        
        # Test Medicine Product
        print("\n--- Testing Medicine Product ---")
        self.authenticate_as(self.supplier_user)
        
        medicine_data = {
            'name': 'Test Medicine Product',
            'description': 'A test medicine for testing purposes',
            'category': category_id,
            'brand': brand_id,
            'product_type': 'medicine',
            'price': '99.99',
            'stock': 50,
            'specifications': json.dumps({
                'weight': '100mg',
                'storage': 'Room temperature'
            }),
            'medicine_details': json.dumps({
                'composition': 'Active ingredient 100mg',
                'quantity': '30 tablets',
                'manufacturer': 'Test Pharma Corp',
                'expiry_date': '2025-12-31',
                'batch_number': 'BATCH001',
                'prescription_required': True,
                'form': 'Tablet',
                'pack_size': '30'
            })
        }
        
        # Add image
        with self.create_test_image("medicine_product.jpg") as img:
            files = {'image_file': img}
            response = self.client.post('/api/products/products/', data=medicine_data, files=files, format='multipart')
        
        self.log_result('products', '/api/products/products/', 'POST', medicine_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Medicine product creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_products.append(('medicine', response.data['id']))
            
        # Test Equipment Product
        print("\n--- Testing Equipment Product ---")
        
        equipment_data = {
            'name': 'Test Medical Equipment',
            'description': 'A test medical equipment for testing purposes', 
            'category': category_id,
            'brand': brand_id,
            'product_type': 'equipment',
            'price': '999.99',
            'stock': 10,
            'specifications': json.dumps({
                'dimensions': '10x10x5 cm',
                'weight': '2kg'
            }),
            'equipment_details': json.dumps({
                'model_number': 'EQ001',
                'warranty_period': '2 years',
                'usage_type': 'Diagnostic',
                'technical_specifications': 'Advanced digital display with LCD screen',
                'power_requirement': '220V AC',
                'equipment_type': 'Monitoring Device'
            })
        }
        
        response = self.client.post('/api/products/products/', data=equipment_data)
        self.log_result('products', '/api/products/products/', 'POST', equipment_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Equipment product creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_products.append(('equipment', response.data['id']))
            
        # Test Pathology Product
        print("\n--- Testing Pathology Product ---")
        
        pathology_data = {
            'name': 'Test Pathology Kit',
            'description': 'A test pathology testing kit',
            'category': category_id,
            'brand': brand_id, 
            'product_type': 'pathology',
            'price': '199.99',
            'stock': 25,
            'specifications': json.dumps({
                'test_count': '50 tests',
                'shelf_life': '24 months'
            }),
            'pathology_details': json.dumps({
                'compatible_tests': 'Blood glucose, Cholesterol, Hemoglobin',
                'chemical_composition': 'Test reagents and control solutions',
                'storage_condition': 'Store at 2-8°C, protect from light'
            })
        }
        
        response = self.client.post('/api/products/products/', data=pathology_data)
        self.log_result('products', '/api/products/products/', 'POST', pathology_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Pathology product creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_products.append(('pathology', response.data['id']))
            
        # Test without type-specific details (base product)
        print("\n--- Testing Base Product (no type details) ---")
        
        base_product_data = {
            'name': 'Test Base Product',
            'description': 'A basic product without specific type details',
            'category': category_id,
            'product_type': 'medicine',
            'price': '49.99',
            'stock': 100
        }
        
        response = self.client.post('/api/products/products/', data=base_product_data)
        self.log_result('products', '/api/products/products/', 'POST', base_product_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Base product creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_products.append(('base', response.data['id']))
        
        # Test List Products
        print("\n--- Testing Product Listing ---")
        response = self.client.get('/api/products/products/')
        self.log_result('products', '/api/products/products/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Product list: {response.status_code} - Found {len(response.data) if hasattr(response, 'data') and isinstance(response.data, list) else 0} products")
        
        # Approve products as admin
        print("\n--- Approving Products as Admin ---")
        self.authenticate_as(self.admin_user)
        for product_type, product_id in created_products:
            response = self.client.post(f'/api/products/admin/products/{product_id}/approve/')
            self.log_result('products', f'/api/products/admin/products/{product_id}/approve/', 'POST', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"Product {product_id} ({product_type}) approval: {response.status_code}")
        
        return created_products
        
    def test_variants(self, products):
        """Test product variant endpoints"""
        print("\n=== TESTING PRODUCT VARIANTS ===")
        
        if not products:
            print("No products available for variant testing")
            return []
            
        created_variants = []
        product_id = products[0][1]  # Use first product
        
        self.authenticate_as(self.supplier_user)
        
        # Test 1: Create basic variant
        variant_data = {
            'product': product_id,
            'price': '119.99',
            'additional_price': '20.00',
            'stock': 30
        }
        
        response = self.client.post('/api/products/variants/', data=variant_data)
        self.log_result('variants', '/api/products/variants/', 'POST', variant_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Basic variant creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_variants.append(response.data['id'])
            
        # Test 2: Create variant with attributes (first create attributes)
        print("\n--- Creating Product Attributes ---")
        
        # Create size attribute
        size_attr_data = {'name': 'Size'}
        response = self.client.post('/api/products/attributes/', data=size_attr_data)
        size_attr_id = response.data['id'] if hasattr(response, 'data') and 'id' in response.data else None
        print(f"Size attribute creation: {response.status_code}")
        
        # Create color attribute  
        color_attr_data = {'name': 'Color'}
        response = self.client.post('/api/products/attributes/', data=color_attr_data)
        color_attr_id = response.data['id'] if hasattr(response, 'data') and 'id' in response.data else None
        print(f"Color attribute creation: {response.status_code}")
        
        # Create attribute values
        created_attr_values = []
        if size_attr_id:
            for size in ['Small', 'Medium', 'Large']:
                attr_value_data = {'attribute': size_attr_id, 'value': size}
                response = self.client.post('/api/products/attribute-values/', data=attr_value_data)
                if hasattr(response, 'data') and 'id' in response.data:
                    created_attr_values.append(response.data['id'])
                    
        if color_attr_id:
            for color in ['Red', 'Blue', 'Green']:
                attr_value_data = {'attribute': color_attr_id, 'value': color}
                response = self.client.post('/api/products/attribute-values/', data=attr_value_data)
                if hasattr(response, 'data') and 'id' in response.data:
                    created_attr_values.append(response.data['id'])
        
        # Create variant with attributes
        if created_attr_values:
            variant_with_attrs_data = {
                'product': product_id,
                'price': '129.99',
                'stock': 20,
                'attribute_ids': created_attr_values[:2]  # Use first 2 attribute values
            }
            
            response = self.client.post('/api/products/variants/', data=variant_with_attrs_data)
            self.log_result('variants', '/api/products/variants/', 'POST', variant_with_attrs_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"Variant with attributes creation: {response.status_code}")
            if hasattr(response, 'data') and 'id' in response.data:
                created_variants.append(response.data['id'])
        
        # Test 3: List variants
        response = self.client.get('/api/products/variants/')
        self.log_result('variants', '/api/products/variants/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Variant list: {response.status_code} - Found {len(response.data) if hasattr(response, 'data') and isinstance(response.data, list) else 0} variants")
        
        # Approve variants as admin
        print("\n--- Approving Variants as Admin ---")
        self.authenticate_as(self.admin_user)
        for variant_id in created_variants:
            response = self.client.post(f'/api/products/admin/variants/{variant_id}/approve/')
            self.log_result('variants', f'/api/products/admin/variants/{variant_id}/approve/', 'POST', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"Variant {variant_id} approval: {response.status_code}")
            
        return created_variants
        
    def test_images(self, products):
        """Test product image endpoints"""
        print("\n=== TESTING PRODUCT IMAGES ===")
        
        if not products:
            print("No products available for image testing")
            return
            
        self.authenticate_as(self.supplier_user)
        product_id = products[0][1]  # Use first product
        
        # Test 1: Upload product image
        image_data = {
            'product': product_id,
            'alt_text': 'Test product image',
            'order': 1
        }
        
        with self.create_test_image("product_image_1.jpg") as img:
            files = {'image_file': img}
            response = self.client.post('/api/products/images/', data=image_data, files=files, format='multipart')
        
        self.log_result('images', '/api/products/images/', 'POST', image_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Product image upload: {response.status_code}")
        
        # Test 2: Upload multiple images
        for i in range(2, 4):
            image_data = {
                'product': product_id,
                'alt_text': f'Test product image {i}',
                'order': i
            }
            
            with self.create_test_image(f"product_image_{i}.jpg") as img:
                files = {'image_file': img}
                response = self.client.post('/api/products/images/', data=image_data, files=files, format='multipart')
            print(f"Additional image {i} upload: {response.status_code}")
        
        # Test 3: List images
        response = self.client.get('/api/products/images/')
        self.log_result('images', '/api/products/images/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Image list: {response.status_code} - Found {len(response.data) if hasattr(response, 'data') and isinstance(response.data, list) else 0} images")
        
    def test_reviews(self, products):
        """Test product review endpoints"""
        print("\n=== TESTING PRODUCT REVIEWS ===")
        
        if not products:
            print("No products available for review testing")
            return
            
        product_id = products[0][1]  # Use first product
        
        # Test 1: Create review as customer
        self.authenticate_as(self.customer_user)
        
        review_data = {
            'product': product_id,
            'rating': 5,
            'comment': 'Excellent product! Highly recommended.'
        }
        
        response = self.client.post('/api/products/reviews/', data=review_data)
        self.log_result('reviews', '/api/products/reviews/', 'POST', review_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Customer review creation: {response.status_code}")
        
        # Test 2: Create review as admin
        self.authenticate_as(self.admin_user)
        
        admin_review_data = {
            'product': product_id,
            'rating': 4,
            'comment': 'Good quality product with minor improvements needed.'
        }
        
        response = self.client.post('/api/products/reviews/', data=admin_review_data)
        self.log_result('reviews', '/api/products/reviews/', 'POST', admin_review_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Admin review creation: {response.status_code}")
        
        # Test 3: List reviews
        response = self.client.get('/api/products/reviews/')
        self.log_result('reviews', '/api/products/reviews/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Review list: {response.status_code} - Found {len(response.data) if hasattr(response, 'data') and isinstance(response.data, list) else 0} reviews")
        
        # Test 4: Try duplicate review (should fail)
        duplicate_review_data = {
            'product': product_id,
            'rating': 3,
            'comment': 'Trying to create duplicate review.'
        }
        
        response = self.client.post('/api/products/reviews/', data=duplicate_review_data)
        self.log_result('reviews', '/api/products/reviews/', 'POST', duplicate_review_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Duplicate review attempt: {response.status_code} (should fail)")
        
    def test_public_endpoints(self, products):
        """Test public endpoints"""
        print("\n=== TESTING PUBLIC ENDPOINTS ===")
        
        # Remove authentication for public tests
        self.client.credentials()
        
        # Test 1: Public category list
        response = self.client.get('/api/public/categories/')
        self.log_result('public_endpoints', '/api/public/categories/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Public categories: {response.status_code}")
        
        # Test 2: Public brand list
        response = self.client.get('/api/public/brands/')
        self.log_result('public_endpoints', '/api/public/brands/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Public brands: {response.status_code}")
        
        # Test 3: Public product list
        response = self.client.get('/api/public/products/')
        self.log_result('public_endpoints', '/api/public/products/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Public products: {response.status_code}")
        
        # Test 4: Public product search
        response = self.client.get('/api/public/search/?q=test')
        self.log_result('public_endpoints', '/api/public/search/', 'GET', {'q': 'test'}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Product search: {response.status_code}")
        
        # Test 5: Featured products
        response = self.client.get('/api/public/featured/')
        self.log_result('public_endpoints', '/api/public/featured/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"Featured products: {response.status_code}")
        
        # Test 6: Products by type
        for product_type in ['medicine', 'equipment', 'pathology']:
            response = self.client.get(f'/api/public/types/{product_type}/products/')
            self.log_result('public_endpoints', f'/api/public/types/{product_type}/products/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"Products by type {product_type}: {response.status_code}")
            
        # Test 7: Product detail (if we have products)
        if products:
            product_id = products[0][1]
            response = self.client.get(f'/api/public/products/{product_id}/')
            self.log_result('public_endpoints', f'/api/public/products/{product_id}/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"Public product detail: {response.status_code}")
            
            # Test product reviews
            response = self.client.get(f'/api/public/products/{product_id}/reviews/')
            self.log_result('public_endpoints', f'/api/public/products/{product_id}/reviews/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"Public product reviews: {response.status_code}")
        
    def test_error_scenarios(self):
        """Test various error scenarios"""
        print("\n=== TESTING ERROR SCENARIOS ===")
        
        # Test 1: Invalid product type
        self.authenticate_as(self.supplier_user)
        
        invalid_product_data = {
            'name': 'Invalid Product Type',
            'product_type': 'invalid_type',
            'category': 1,  # Assuming category 1 exists
            'price': '99.99'
        }
        
        response = self.client.post('/api/products/products/', data=invalid_product_data)
        print(f"Invalid product type: {response.status_code} (should fail)")
        
        # Test 2: Missing required fields
        incomplete_product_data = {
            'name': 'Incomplete Product'
            # Missing category, price, etc.
        }
        
        response = self.client.post('/api/products/products/', data=incomplete_product_data)
        print(f"Incomplete product data: {response.status_code} (should fail)")
        
        # Test 3: Unauthorized access
        self.client.credentials()  # Remove authentication
        
        unauthorized_data = {
            'name': 'Unauthorized Product',
            'category': 1,
            'price': '99.99'
        }
        
        response = self.client.post('/api/products/products/', data=unauthorized_data)
        print(f"Unauthorized product creation: {response.status_code} (should fail)")
        
    def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting Comprehensive Products API Testing")
        print("=" * 60)
        
        try:
            # Test categories first (needed for products)
            admin_category_id, supplier_category_id = self.test_categories()
            category_id = admin_category_id or supplier_category_id
            
            # Test brands (needed for products)
            admin_brand_id, supplier_brand_id = self.test_brands()
            brand_id = admin_brand_id or supplier_brand_id
            
            if not category_id:
                print("❌ No category created, skipping product tests")
                return
                
            # Test products (all types)
            products = self.test_products(category_id, brand_id)
            
            # Test variants
            variants = self.test_variants(products)
            
            # Test images
            self.test_images(products)
            
            # Test reviews
            self.test_reviews(products)
            
            # Test public endpoints
            self.test_public_endpoints(products)
            
            # Test error scenarios
            self.test_error_scenarios()
            
            print("\n" + "=" * 60)
            print("✅ All tests completed!")
            
        except Exception as e:
            print(f"❌ Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def generate_report(self):
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f'products_test_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        print(f"\n📊 Test report saved to: {report_file}")
        
        # Print summary
        total_tests = sum(len(self.results[key]) for key in self.results)
        successful_tests = sum(len([test for test in self.results[key] if test.get('success', False)]) for key in self.results)
        
        print(f"\n📈 Test Summary:")
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        return report_file

if __name__ == '__main__':
    tester = ProductsAPITester()
    tester.run_all_tests()
    tester.generate_report()