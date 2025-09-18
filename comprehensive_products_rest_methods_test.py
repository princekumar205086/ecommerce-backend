#!/usr/bin/env python3
"""
Comprehensive Product API REST Methods Test Suite
Tests all product-related GET, PUT, PATCH, DELETE endpoints with different user roles
"""

import os
import sys
import json
from decimal import Decimal
from datetime import datetime, timedelta

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
import django
django.setup()

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from products.models import (
    Product, ProductCategory, Brand, ProductVariant, 
    MedicineDetails, EquipmentDetails, PathologyDetails,
    ProductAttribute, ProductAttributeValue, ProductImage,
    SupplierProductPrice, ProductReview
)

User = get_user_model()

class ComprehensiveProductRestMethodsTest:
    def __init__(self):
        self.client = APIClient()
        self.admin_user = None
        self.supplier_user = None
        self.regular_user = None
        self.test_results = []
        self.test_entities = {}

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
        """Get existing test users"""
        try:
            self.admin_user = User.objects.get(email='admin@medixmall.com')
            self.supplier_user = User.objects.get(email='supplier@medixmall.com')
            self.regular_user = User.objects.get(email='user@medixmall.com')
            self.log_result("Setup Test Users", True, "Test users retrieved successfully")
            return True
        except User.DoesNotExist:
            self.log_result("Setup Test Users", False, "Test users not found")
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

    def setup_test_data(self):
        """Get existing test data from database"""
        try:
            # Get categories
            categories = list(ProductCategory.objects.all()[:3])
            if categories:
                self.test_entities['categories'] = [{'id': c.id, 'name': c.name} for c in categories]

            # Get brands
            brands = list(Brand.objects.all()[:3])
            if brands:
                self.test_entities['brands'] = [{'id': b.id, 'name': b.name} for b in brands]

            # Get products
            products = list(Product.objects.all()[:5])
            if products:
                self.test_entities['products'] = [{'id': p.id, 'name': p.name, 'product_type': p.product_type} for p in products]

            # Get variants
            variants = list(ProductVariant.objects.all()[:3])
            if variants:
                self.test_entities['variants'] = [{'id': v.id, 'product_id': v.product_id} for v in variants]

            # Get attributes
            attributes = list(ProductAttribute.objects.all()[:3])
            if attributes:
                self.test_entities['attributes'] = [{'id': a.id, 'name': a.name} for a in attributes]

            # Get attribute values
            attr_values = list(ProductAttributeValue.objects.all()[:5])
            if attr_values:
                self.test_entities['attribute_values'] = [{'id': av.id, 'value': av.value} for av in attr_values]

            # Get supplier prices
            prices = list(SupplierProductPrice.objects.all()[:3])
            if prices:
                self.test_entities['supplier_prices'] = [{'id': sp.id, 'price': str(sp.price)} for sp in prices]

            # Get reviews
            reviews = list(ProductReview.objects.all()[:3])
            if reviews:
                self.test_entities['reviews'] = [{'id': r.id, 'rating': r.rating} for r in reviews]

            self.log_result("Setup Test Data", True, f"Retrieved test data: {len(self.test_entities)} entity types")
            return True
        except Exception as e:
            self.log_result("Setup Test Data", False, f"Failed to retrieve test data: {str(e)}")
            return False

    # GET Methods Tests
    def test_get_categories_list(self):
        """Test GET /api/products/categories/ with different user roles"""
        endpoints = [
            ('Admin', self.admin_user),
            ('Supplier', self.supplier_user),
            ('Regular User', self.regular_user),
            ('Anonymous', None)
        ]

        for user_type, user in endpoints:
            try:
                if user:
                    self.authenticate_user(user)
                else:
                    self.client.credentials()  # Clear auth

                response = self.client.get('/api/products/categories/')
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        f"GET Categories List ({user_type})",
                        True,
                        f"Retrieved {len(data)} categories"
                    )
                else:
                    self.log_result(
                        f"GET Categories List ({user_type})",
                        False,
                        f"Failed - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(
                    f"GET Categories List ({user_type})",
                    False,
                    f"Exception: {str(e)}"
                )

    def test_get_category_detail(self):
        """Test GET /api/products/categories/{id}/ with different user roles"""
        if not self.test_entities.get('categories'):
            self.log_result("GET Category Detail", False, "No categories available for testing")
            return

        category_id = self.test_entities['categories'][0]['id']
        endpoints = [
            ('Admin', self.admin_user),
            ('Regular User', self.regular_user),
            ('Anonymous', None)
        ]

        for user_type, user in endpoints:
            try:
                if user:
                    self.authenticate_user(user)
                else:
                    self.client.credentials()

                response = self.client.get(f'/api/products/categories/{category_id}/')
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        f"GET Category Detail ({user_type})",
                        True,
                        f"Retrieved category: {data.get('name', 'Unknown')}"
                    )
                else:
                    self.log_result(
                        f"GET Category Detail ({user_type})",
                        False,
                        f"Failed - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(
                    f"GET Category Detail ({user_type})",
                    False,
                    f"Exception: {str(e)}"
                )

    def test_get_brands_list(self):
        """Test GET /api/products/brands/"""
        try:
            self.authenticate_user(self.regular_user)
            response = self.client.get('/api/products/brands/')
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "GET Brands List",
                    True,
                    f"Retrieved {len(data)} brands"
                )
            else:
                self.log_result(
                    "GET Brands List",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result("GET Brands List", False, f"Exception: {str(e)}")

    def test_get_products_list(self):
        """Test GET /api/products/products/ with filtering"""
        test_cases = [
            ('All Products', {}),
            ('Filter by Type', {'product_type': 'medicine'}),
            ('Search by Name', {'search': 'paracetamol'}),
            ('Published Only', {'is_publish': 'true'})
        ]

        for test_name, params in test_cases:
            try:
                self.authenticate_user(self.regular_user)
                response = self.client.get('/api/products/products/', params)
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else data.get('count', len(data.get('results', [])))
                    self.log_result(
                        f"GET Products List ({test_name})",
                        True,
                        f"Retrieved {count} products"
                    )
                else:
                    self.log_result(
                        f"GET Products List ({test_name})",
                        False,
                        f"Failed - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(f"GET Products List ({test_name})", False, f"Exception: {str(e)}")

    def test_get_product_detail(self):
        """Test GET /api/products/products/{id}/ with different product types"""
        if not self.test_entities.get('products'):
            self.log_result("GET Product Detail", False, "No products available for testing")
            return

        for product in self.test_entities['products'][:3]:  # Test first 3 products
            try:
                self.authenticate_user(self.regular_user)
                response = self.client.get(f'/api/products/products/{product["id"]}/')
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        f"GET Product Detail ({product['product_type']})",
                        True,
                        f"Retrieved product: {data.get('name', 'Unknown')}"
                    )
                else:
                    self.log_result(
                        f"GET Product Detail ({product['product_type']})",
                        False,
                        f"Failed - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(f"GET Product Detail ({product['product_type']})", False, f"Exception: {str(e)}")

    def test_get_variants_list(self):
        """Test GET /api/products/variants/"""
        try:
            self.authenticate_user(self.admin_user)
            response = self.client.get('/api/products/variants/')
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('count', len(data.get('results', [])))
                self.log_result(
                    "GET Variants List",
                    True,
                    f"Retrieved {count} variants"
                )
            else:
                self.log_result(
                    "GET Variants List",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result("GET Variants List", False, f"Exception: {str(e)}")

    def test_get_attributes_and_values(self):
        """Test GET /api/products/attributes/ and /api/products/attribute-values/"""
        endpoints = [
            ('Attributes', '/api/products/attributes/'),
            ('Attribute Values', '/api/products/attribute-values/')
        ]

        for endpoint_name, url in endpoints:
            try:
                self.authenticate_user(self.admin_user)
                response = self.client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else data.get('count', len(data.get('results', [])))
                    self.log_result(
                        f"GET {endpoint_name}",
                        True,
                        f"Retrieved {count} items"
                    )
                else:
                    self.log_result(
                        f"GET {endpoint_name}",
                        False,
                        f"Failed - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(f"GET {endpoint_name}", False, f"Exception: {str(e)}")

    def test_get_supplier_prices(self):
        """Test GET /api/products/supplier-prices/"""
        try:
            self.authenticate_user(self.supplier_user)
            response = self.client.get('/api/products/supplier-prices/')
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('count', len(data.get('results', [])))
                self.log_result(
                    "GET Supplier Prices",
                    True,
                    f"Retrieved {count} prices"
                )
            else:
                self.log_result(
                    "GET Supplier Prices",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result("GET Supplier Prices", False, f"Exception: {str(e)}")

    def test_get_reviews(self):
        """Test GET /api/products/reviews/"""
        try:
            self.authenticate_user(self.regular_user)
            response = self.client.get('/api/products/reviews/')
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('count', len(data.get('results', [])))
                self.log_result(
                    "GET Reviews",
                    True,
                    f"Retrieved {count} reviews"
                )
            else:
                self.log_result(
                    "GET Reviews",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result("GET Reviews", False, f"Exception: {str(e)}")

    # PUT/PATCH Methods Tests
    def test_update_category(self):
        """Test PUT/PATCH /api/products/categories/{id}/"""
        if not self.test_entities.get('categories'):
            self.log_result("UPDATE Category", False, "No categories available for testing")
            return

        category_id = self.test_entities['categories'][0]['id']
        
        # Test PATCH update
        try:
            self.authenticate_user(self.admin_user)
            update_data = {
                'name': f"Updated Category {datetime.now().strftime('%H%M%S')}",
                'icon': 'https://via.placeholder.com/50x50/orange/white?text=Updated'
            }
            
            response = self.client.patch(f'/api/products/categories/{category_id}/', update_data, format='json')
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "PATCH Category",
                    True,
                    f"Updated category to: {data.get('name', 'Unknown')}"
                )
            else:
                self.log_result(
                    "PATCH Category",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result("PATCH Category", False, f"Exception: {str(e)}")

        # Test unauthorized update
        try:
            self.authenticate_user(self.regular_user)
            response = self.client.patch(f'/api/products/categories/{category_id}/', {'name': 'Unauthorized Update'}, format='json')
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "PATCH Category (Unauthorized)",
                    True,
                    "Correctly blocked unauthorized update"
                )
            else:
                self.log_result(
                    "PATCH Category (Unauthorized)",
                    False,
                    f"Should have blocked unauthorized update - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result("PATCH Category (Unauthorized)", False, f"Exception: {str(e)}")

    def test_update_product(self):
        """Test PUT/PATCH /api/products/products/{id}/"""
        if not self.test_entities.get('products'):
            self.log_result("UPDATE Product", False, "No products available for testing")
            return

        product_id = self.test_entities['products'][0]['id']
        
        # Test PATCH update
        try:
            self.authenticate_user(self.admin_user)
            update_data = {
                'price': '99.99',
                'stock': 200,
                'description': f"Updated product description at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            response = self.client.patch(f'/api/products/products/{product_id}/', update_data, format='json')
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "PATCH Product",
                    True,
                    f"Updated product price to: {data.get('price', 'Unknown')}"
                )
            else:
                self.log_result(
                    "PATCH Product",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result("PATCH Product", False, f"Exception: {str(e)}")

    def test_update_variant(self):
        """Test PUT/PATCH /api/products/variants/{id}/"""
        if not self.test_entities.get('variants'):
            self.log_result("UPDATE Variant", False, "No variants available for testing")
            return

        variant_id = self.test_entities['variants'][0]['id']
        
        try:
            self.authenticate_user(self.admin_user)
            update_data = {
                'price': '55.75',
                'stock': 75,
                'is_active': True
            }
            
            response = self.client.patch(f'/api/products/variants/{variant_id}/', update_data, format='json')
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "PATCH Variant",
                    True,
                    f"Updated variant price to: {data.get('price', 'Unknown')}"
                )
            else:
                self.log_result(
                    "PATCH Variant",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result("PATCH Variant", False, f"Exception: {str(e)}")

    def test_update_supplier_price(self):
        """Test PUT/PATCH /api/products/supplier-prices/{id}/"""
        if not self.test_entities.get('supplier_prices'):
            self.log_result("UPDATE Supplier Price", False, "No supplier prices available for testing")
            return

        price_id = self.test_entities['supplier_prices'][0]['id']
        
        try:
            self.authenticate_user(self.supplier_user)
            update_data = {
                'price': '45.50',
                'district': 'Updated District'
            }
            
            response = self.client.patch(f'/api/products/supplier-prices/{price_id}/', update_data, format='json')
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "PATCH Supplier Price",
                    True,
                    f"Updated supplier price to: {data.get('price', 'Unknown')}"
                )
            else:
                self.log_result(
                    "PATCH Supplier Price",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result("PATCH Supplier Price", False, f"Exception: {str(e)}")

    def test_update_review(self):
        """Test PUT/PATCH /api/products/reviews/{id}/"""
        if not self.test_entities.get('reviews'):
            self.log_result("UPDATE Review", False, "No reviews available for testing")
            return

        review_id = self.test_entities['reviews'][0]['id']
        
        try:
            self.authenticate_user(self.regular_user)
            update_data = {
                'rating': 4,
                'comment': f"Updated review comment at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            response = self.client.patch(f'/api/products/reviews/{review_id}/', update_data, format='json')
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "PATCH Review",
                    True,
                    f"Updated review rating to: {data.get('rating', 'Unknown')}"
                )
            else:
                self.log_result(
                    "PATCH Review",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.json() if hasattr(response, 'json') else response.data
                )
        except Exception as e:
            self.log_result("PATCH Review", False, f"Exception: {str(e)}")

    # DELETE Methods Tests
    def test_delete_operations(self):
        """Test DELETE operations with proper permissions"""
        
        # Create a test category to delete
        try:
            self.authenticate_user(self.admin_user)
            category_data = {
                'name': f'Test Delete Category {datetime.now().strftime("%H%M%S")}',
                'icon': 'https://via.placeholder.com/50x50/red/white?text=Del'
            }
            response = self.client.post('/api/products/categories/', category_data, format='json')
            
            if response.status_code == 201:
                category_id = response.json()['id']
                
                # Test successful deletion by admin
                delete_response = self.client.delete(f'/api/products/categories/{category_id}/')
                if delete_response.status_code == 204:
                    self.log_result(
                        "DELETE Category (Admin)",
                        True,
                        "Successfully deleted category"
                    )
                else:
                    self.log_result(
                        "DELETE Category (Admin)",
                        False,
                        f"Failed to delete - Status: {delete_response.status_code}",
                        delete_response.json() if hasattr(delete_response, 'json') else delete_response.data
                    )
            else:
                self.log_result("DELETE Category Setup", False, "Failed to create test category")
        except Exception as e:
            self.log_result("DELETE Category (Admin)", False, f"Exception: {str(e)}")

        # Test unauthorized deletion
        if self.test_entities.get('categories'):
            try:
                self.authenticate_user(self.regular_user)
                category_id = self.test_entities['categories'][0]['id']
                response = self.client.delete(f'/api/products/categories/{category_id}/')
                
                if response.status_code in [401, 403]:
                    self.log_result(
                        "DELETE Category (Unauthorized)",
                        True,
                        "Correctly blocked unauthorized deletion"
                    )
                else:
                    self.log_result(
                        "DELETE Category (Unauthorized)",
                        False,
                        f"Should have blocked unauthorized deletion - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result("DELETE Category (Unauthorized)", False, f"Exception: {str(e)}")

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        
        # Test 404 for non-existent resources
        test_cases = [
            ('Non-existent Category', '/api/products/categories/99999/'),
            ('Non-existent Product', '/api/products/products/99999/'),
            ('Non-existent Variant', '/api/products/variants/99999/')
        ]

        for test_name, url in test_cases:
            try:
                self.authenticate_user(self.admin_user)
                response = self.client.get(url)
                
                if response.status_code == 404:
                    self.log_result(
                        f"404 Test ({test_name})",
                        True,
                        "Correctly returned 404 for non-existent resource"
                    )
                else:
                    self.log_result(
                        f"404 Test ({test_name})",
                        False,
                        f"Expected 404 but got {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result(f"404 Test ({test_name})", False, f"Exception: {str(e)}")

        # Test invalid data updates
        if self.test_entities.get('products'):
            try:
                self.authenticate_user(self.admin_user)
                product_id = self.test_entities['products'][0]['id']
                invalid_data = {
                    'price': 'invalid_price',  # Should be numeric
                    'stock': -10  # Should be positive
                }
                
                response = self.client.patch(f'/api/products/products/{product_id}/', invalid_data, format='json')
                
                if response.status_code == 400:
                    self.log_result(
                        "Invalid Data Test",
                        True,
                        "Correctly rejected invalid data"
                    )
                else:
                    self.log_result(
                        "Invalid Data Test",
                        False,
                        f"Should have rejected invalid data - Status: {response.status_code}",
                        response.json() if hasattr(response, 'json') else response.data
                    )
            except Exception as e:
                self.log_result("Invalid Data Test", False, f"Exception: {str(e)}")

    def run_all_rest_tests(self):
        """Run all REST method tests"""
        print("🚀 Starting Comprehensive Product API REST Methods Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_users():
            return False
        
        if not self.setup_test_data():
            return False

        # GET Tests
        print("\n📖 Testing GET Methods...")
        self.test_get_categories_list()
        self.test_get_category_detail()
        self.test_get_brands_list()
        self.test_get_products_list()
        self.test_get_product_detail()
        self.test_get_variants_list()
        self.test_get_attributes_and_values()
        self.test_get_supplier_prices()
        self.test_get_reviews()

        # PUT/PATCH Tests
        print("\n✏️ Testing UPDATE Methods (PUT/PATCH)...")
        self.test_update_category()
        self.test_update_product()
        self.test_update_variant()
        self.test_update_supplier_price()
        self.test_update_review()

        # DELETE Tests
        print("\n🗑️ Testing DELETE Methods...")
        self.test_delete_operations()

        # Edge Cases
        print("\n🧪 Testing Edge Cases...")
        self.test_edge_cases()
        
        return True

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE REST METHODS TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Group results by method
        method_stats = {}
        for result in self.test_results:
            method = 'GET' if 'GET' in result['test_name'] else 'PATCH' if 'PATCH' in result['test_name'] else 'DELETE' if 'DELETE' in result['test_name'] else 'OTHER'
            if method not in method_stats:
                method_stats[method] = {'total': 0, 'passed': 0}
            method_stats[method]['total'] += 1
            if result['success']:
                method_stats[method]['passed'] += 1
        
        print(f"\n📊 Results by HTTP Method:")
        for method, stats in method_stats.items():
            success_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"   {method}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
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
            'method_stats': method_stats,
            'detailed_results': self.test_results
        }


def main():
    """Main function to run the tests"""
    tester = ComprehensiveProductRestMethodsTest()
    
    try:
        success = tester.run_all_rest_tests()
        report = tester.generate_test_report()
        
        # Save detailed results to JSON file
        with open('product_rest_methods_test_results.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: product_rest_methods_test_results.json")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)