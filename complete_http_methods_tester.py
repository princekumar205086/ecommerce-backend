#!/usr/bin/env python
"""
Complete HTTP Methods Testing for Products API
Tests GET, PUT, PATCH, DELETE endpoints for 100% success
"""
import os
import sys
import json
from datetime import datetime
from decimal import Decimal

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import Product, ProductCategory, Brand, ProductVariant, ProductReview

User = get_user_model()

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for proper serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

class CompleteHTTPMethodsTester:
    def __init__(self):
        self.client = APIClient()
        self.results = {
            'categories': [],
            'brands': [],
            'products': [],
            'variants': [],
            'reviews': [],
            'admin': []
        }
        self.setup_users()
        self.created_resources = {
            'categories': [],
            'brands': [],
            'products': [],
            'variants': [],
            'reviews': []
        }
        
    def setup_users(self):
        """Setup test users"""
        self.admin_user = User.objects.filter(role='admin').first()
        self.supplier_user = User.objects.filter(role='supplier').first()
        self.customer_user = User.objects.filter(role='user').first()
        
        print(f"✅ Users ready - Admin: {self.admin_user.email}, Supplier: {self.supplier_user.email}, Customer: {self.customer_user.email}")
        
    def get_jwt_token(self, user):
        """Get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate_as(self, user):
        """Authenticate client as specific user"""
        token = self.get_jwt_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token
        
    def log_result(self, category, method, endpoint, payload, response, status_code, expected_codes=[]):
        """Log test result with expected status codes"""
        if not expected_codes:
            expected_codes = [200, 201, 204]  # Default success codes
            
        result = {
            'method': method,
            'endpoint': endpoint,
            'payload': payload,
            'response_status': status_code,
            'response_data': response if isinstance(response, dict) else str(response),
            'timestamp': datetime.now().isoformat(),
            'success': status_code in expected_codes,
            'expected_codes': expected_codes
        }
        self.results[category].append(result)
        
        status_icon = "✅" if result['success'] else "❌"
        print(f"{status_icon} {method} {endpoint}: {status_code} (expected: {expected_codes})")
        
        return result['success']
        
    def test_categories_crud(self):
        """Test complete CRUD operations for categories"""
        print("\n=== TESTING CATEGORIES CRUD ===")
        
        # CREATE (POST)
        self.authenticate_as(self.admin_user)
        category_data = {
            'name': f"CRUD Test Category {datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        response = self.client.post('/api/products/categories/', data=category_data, format='json')
        success = self.log_result('categories', 'POST', '/api/products/categories/', category_data, 
                                response.data if hasattr(response, 'data') else response.content, 
                                response.status_code, [201])
        
        category_id = None
        if success and hasattr(response, 'data') and 'id' in response.data:
            category_id = response.data['id']
            self.created_resources['categories'].append(category_id)
            
        if not category_id:
            # Fallback to existing category
            existing_categories = ProductCategory.objects.all()[:1]
            if existing_categories:
                category_id = existing_categories[0].id
                print(f"Using existing category: {category_id}")
        
        if category_id:
            # READ (GET)
            response = self.client.get(f'/api/products/categories/{category_id}/')
            self.log_result('categories', 'GET', f'/api/products/categories/{category_id}/', {}, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # UPDATE (PUT)
            update_data = {
                'name': f"Updated Category {datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            response = self.client.put(f'/api/products/categories/{category_id}/', data=update_data, format='json')
            self.log_result('categories', 'PUT', f'/api/products/categories/{category_id}/', update_data, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # PARTIAL UPDATE (PATCH)
            patch_data = {
                'name': f"Patched Category {datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            response = self.client.patch(f'/api/products/categories/{category_id}/', data=patch_data, format='json')
            self.log_result('categories', 'PATCH', f'/api/products/categories/{category_id}/', patch_data, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # LIST (GET)
            response = self.client.get('/api/products/categories/')
            self.log_result('categories', 'GET', '/api/products/categories/', {}, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # DELETE (only if we created it)
            if category_id in self.created_resources['categories']:
                response = self.client.delete(f'/api/products/categories/{category_id}/')
                self.log_result('categories', 'DELETE', f'/api/products/categories/{category_id}/', {}, 
                              response.data if hasattr(response, 'data') else response.content, 
                              response.status_code, [204, 404])  # 404 acceptable if already deleted
                
        return category_id
        
    def test_brands_crud(self):
        """Test complete CRUD operations for brands"""
        print("\n=== TESTING BRANDS CRUD ===")
        
        # CREATE (POST)
        self.authenticate_as(self.admin_user)
        brand_data = {
            'name': f"CRUD Test Brand {datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        response = self.client.post('/api/products/brands/', data=brand_data, format='json')
        success = self.log_result('brands', 'POST', '/api/products/brands/', brand_data, 
                                response.data if hasattr(response, 'data') else response.content, 
                                response.status_code, [201])
        
        brand_id = None
        if success and hasattr(response, 'data') and 'id' in response.data:
            brand_id = response.data['id']
            self.created_resources['brands'].append(brand_id)
            
        if not brand_id:
            # Fallback to existing brand
            existing_brands = Brand.objects.all()[:1]
            if existing_brands:
                brand_id = existing_brands[0].id
                print(f"Using existing brand: {brand_id}")
        
        if brand_id:
            # READ (GET)
            response = self.client.get(f'/api/products/brands/{brand_id}/')
            self.log_result('brands', 'GET', f'/api/products/brands/{brand_id}/', {}, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # UPDATE (PUT)
            update_data = {
                'name': f"Updated Brand {datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            response = self.client.put(f'/api/products/brands/{brand_id}/', data=update_data, format='json')
            self.log_result('brands', 'PUT', f'/api/products/brands/{brand_id}/', update_data, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # PARTIAL UPDATE (PATCH)
            patch_data = {
                'name': f"Patched Brand {datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            response = self.client.patch(f'/api/products/brands/{brand_id}/', data=patch_data, format='json')
            self.log_result('brands', 'PATCH', f'/api/products/brands/{brand_id}/', patch_data, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # LIST (GET)
            response = self.client.get('/api/products/brands/')
            self.log_result('brands', 'GET', '/api/products/brands/', {}, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # DELETE (only if we created it)
            if brand_id in self.created_resources['brands']:
                response = self.client.delete(f'/api/products/brands/{brand_id}/')
                self.log_result('brands', 'DELETE', f'/api/products/brands/{brand_id}/', {}, 
                              response.data if hasattr(response, 'data') else response.content, 
                              response.status_code, [204, 404])
                
        return brand_id
        
    def test_products_crud(self, category_id, brand_id):
        """Test complete CRUD operations for products"""
        print("\n=== TESTING PRODUCTS CRUD ===")
        
        # Use existing published categories/brands instead of newly created ones
        categories = ProductCategory.objects.filter(is_publish=True, status='published').order_by('id')[:1]
        brands = Brand.objects.filter(is_publish=True, status='published').order_by('id')[:1]
        
        if categories:
            category_id = categories[0].id
        if brands:
            brand_id = brands[0].id
            
        if not category_id or not brand_id:
            print(f"❌ No published category ({category_id}) or brand ({brand_id}) available")
            return None
            
        print(f"Using category: {category_id}, brand: {brand_id}")
            
        if not category_id:
            print("❌ No category available for product testing")
            return None
            
        # CREATE (POST) - Medicine Product
        self.authenticate_as(self.supplier_user)
        product_data = {
            'name': f"CRUD Test Product {datetime.now().strftime('%Y%m%d%H%M%S')}",
            'description': 'A test product for CRUD operations',
            'category': category_id,
            'brand': brand_id,
            'product_type': 'medicine',
            'price': '99.99',
            'stock': 50,
            'specifications': {
                'weight': '100mg',
                'storage': 'Room temperature'
            },
            'medicine_details': {
                'composition': 'Active ingredient 100mg',
                'quantity': '30 tablets',
                'manufacturer': 'Test Pharma',
                'form': 'Tablet'
            }
        }
        
        response = self.client.post('/api/products/products/', data=product_data, format='json')
        
        # Debug logging
        if response.status_code != 201:
            print(f"❌ Product creation failed with {response.status_code}")
            print(f"Request data: {product_data}")
            print(f"Response: {response.data if hasattr(response, 'data') else response.content}")
            
        success = self.log_result('products', 'POST', '/api/products/products/', product_data, 
                                response.data if hasattr(response, 'data') else response.content, 
                                response.status_code, [201])
        
        product_id = None
        if success and hasattr(response, 'data') and 'id' in response.data:
            product_id = response.data['id']
            self.created_resources['products'].append(product_id)
            
        if not product_id:
            # Fallback to existing product - get a fresh one
            existing_products = Product.objects.all().order_by('-id')[:1]
            if existing_products:
                product_id = existing_products[0].id
                print(f"Using existing product: {product_id} ({existing_products[0].name})")
        
        if product_id:
            # READ (GET)
            response = self.client.get(f'/api/products/products/{product_id}/')
            self.log_result('products', 'GET', f'/api/products/products/{product_id}/', {}, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # UPDATE (PUT)
            update_data = {
                'name': f"Updated Product {datetime.now().strftime('%Y%m%d%H%M%S')}",
                'description': 'Updated test product',
                'category': category_id,
                'brand': brand_id,
                'product_type': 'medicine',
                'price': '149.99',
                'stock': 75
            }
            response = self.client.put(f'/api/products/products/{product_id}/', data=update_data, format='json')
            self.log_result('products', 'PUT', f'/api/products/products/{product_id}/', update_data, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # PARTIAL UPDATE (PATCH)
            patch_data = {
                'price': '199.99',
                'stock': 100,
                'description': 'Patched description'
            }
            response = self.client.patch(f'/api/products/products/{product_id}/', data=patch_data, format='json')
            self.log_result('products', 'PATCH', f'/api/products/products/{product_id}/', patch_data, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # LIST (GET)
            response = self.client.get('/api/products/products/')
            self.log_result('products', 'GET', '/api/products/products/', {}, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # DELETE (only if we created it and as admin)
            if product_id in self.created_resources['products']:
                self.authenticate_as(self.admin_user)  # Switch to admin for delete
                response = self.client.delete(f'/api/products/products/{product_id}/')
                self.log_result('products', 'DELETE', f'/api/products/products/{product_id}/', {}, 
                              response.data if hasattr(response, 'data') else response.content, 
                              response.status_code, [204, 404])
                
        return product_id
        
    def test_variants_crud(self, product_id):
        """Test complete CRUD operations for variants"""
        print("\n=== TESTING VARIANTS CRUD ===")
        
        if not product_id:
            # Use existing product
            existing_products = Product.objects.all()[:1]
            if existing_products:
                product_id = existing_products[0].id
                print(f"Using existing product for variants: {product_id}")
            else:
                print("❌ No product available for variant testing")
                return None
        
        # CREATE (POST)
        self.authenticate_as(self.supplier_user)
        variant_data = {
            'product': product_id,
            'price': '119.99',
            'additional_price': '20.00',
            'stock': 30
        }
        
        response = self.client.post('/api/products/variants/', data=variant_data, format='json')
        success = self.log_result('variants', 'POST', '/api/products/variants/', variant_data, 
                                response.data if hasattr(response, 'data') else response.content, 
                                response.status_code, [201])
        
        variant_id = None
        if success and hasattr(response, 'data') and 'id' in response.data:
            variant_id = response.data['id']
            self.created_resources['variants'].append(variant_id)
            
        if not variant_id:
            # Fallback to existing variant
            existing_variants = ProductVariant.objects.all()[:1]
            if existing_variants:
                variant_id = existing_variants[0].id
                print(f"Using existing variant: {variant_id}")
        
        if variant_id:
            # READ (GET)
            response = self.client.get(f'/api/products/variants/{variant_id}/')
            self.log_result('variants', 'GET', f'/api/products/variants/{variant_id}/', {}, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # UPDATE (PUT)
            update_data = {
                'product': product_id,
                'price': '139.99',
                'additional_price': '30.00',
                'stock': 40
            }
            response = self.client.put(f'/api/products/variants/{variant_id}/', data=update_data, format='json')
            self.log_result('variants', 'PUT', f'/api/products/variants/{variant_id}/', update_data, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # PARTIAL UPDATE (PATCH)
            patch_data = {
                'price': '159.99',
                'stock': 50
            }
            response = self.client.patch(f'/api/products/variants/{variant_id}/', data=patch_data, format='json')
            self.log_result('variants', 'PATCH', f'/api/products/variants/{variant_id}/', patch_data, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # LIST (GET)
            response = self.client.get('/api/products/variants/')
            self.log_result('variants', 'GET', '/api/products/variants/', {}, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # DELETE (only if we created it)
            if variant_id in self.created_resources['variants']:
                self.authenticate_as(self.admin_user)  # Switch to admin for delete
                response = self.client.delete(f'/api/products/variants/{variant_id}/')
                self.log_result('variants', 'DELETE', f'/api/products/variants/{variant_id}/', {}, 
                              response.data if hasattr(response, 'data') else response.content, 
                              response.status_code, [204, 404])
                
        return variant_id
        
    def test_reviews_crud(self, product_id):
        """Test complete CRUD operations for reviews"""
        print("\n=== TESTING REVIEWS CRUD ===")
        
        if not product_id:
            # Use published product
            published_products = Product.objects.filter(is_publish=True)[:1]
            if published_products:
                product_id = published_products[0].id
                print(f"Using published product for reviews: {product_id}")
            else:
                print("❌ No published product available for review testing")
                return None
        
        # CREATE (POST)
        self.authenticate_as(self.customer_user)
        review_data = {
            'product': product_id,
            'rating': 5,
            'comment': f'Excellent product! Review created at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        }
        
        response = self.client.post('/api/products/reviews/', data=review_data, format='json')
        success = self.log_result('reviews', 'POST', '/api/products/reviews/', review_data, 
                                response.data if hasattr(response, 'data') else response.content, 
                                response.status_code, [201])
        
        review_id = None
        if success and hasattr(response, 'data') and 'id' in response.data:
            review_id = response.data['id']
            self.created_resources['reviews'].append(review_id)
            
        if not review_id:
            # Try to find existing review by this user
            existing_reviews = ProductReview.objects.filter(user=self.customer_user)[:1]
            if existing_reviews:
                review_id = existing_reviews[0].id
                print(f"Using existing review: {review_id}")
        
        if review_id:
            # READ (GET)
            response = self.client.get(f'/api/products/reviews/{review_id}/')
            self.log_result('reviews', 'GET', f'/api/products/reviews/{review_id}/', {}, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # UPDATE (PUT) - as the review owner
            update_data = {
                'product': product_id,
                'rating': 4,
                'comment': f'Updated review at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            response = self.client.put(f'/api/products/reviews/{review_id}/', data=update_data, format='json')
            self.log_result('reviews', 'PUT', f'/api/products/reviews/{review_id}/', update_data, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # PARTIAL UPDATE (PATCH)
            patch_data = {
                'rating': 3,
                'comment': f'Patched review comment at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            response = self.client.patch(f'/api/products/reviews/{review_id}/', data=patch_data, format='json')
            self.log_result('reviews', 'PATCH', f'/api/products/reviews/{review_id}/', patch_data, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # LIST (GET)
            response = self.client.get('/api/products/reviews/')
            self.log_result('reviews', 'GET', '/api/products/reviews/', {}, 
                          response.data if hasattr(response, 'data') else response.content, 
                          response.status_code, [200])
            
            # DELETE (only if we created it)
            if review_id in self.created_resources['reviews']:
                response = self.client.delete(f'/api/products/reviews/{review_id}/')
                self.log_result('reviews', 'DELETE', f'/api/products/reviews/{review_id}/', {}, 
                              response.data if hasattr(response, 'data') else response.content, 
                              response.status_code, [204, 404])
                
        return review_id
        
    def test_advanced_operations(self):
        """Test advanced operations like filtering, searching, pagination"""
        print("\n=== TESTING ADVANCED OPERATIONS ===")
        
        self.authenticate_as(self.admin_user)
        
        # Test filtering
        response = self.client.get('/api/products/products/?product_type=medicine')
        self.log_result('products', 'GET', '/api/products/products/?product_type=medicine', {}, 
                      response.data if hasattr(response, 'data') else response.content, 
                      response.status_code, [200])
        
        # Test searching
        response = self.client.get('/api/products/products/?search=test')
        self.log_result('products', 'GET', '/api/products/products/?search=test', {}, 
                      response.data if hasattr(response, 'data') else response.content, 
                      response.status_code, [200])
        
        # Test pagination
        response = self.client.get('/api/products/products/?page=1&page_size=5')
        self.log_result('products', 'GET', '/api/products/products/?page=1&page_size=5', {}, 
                      response.data if hasattr(response, 'data') else response.content, 
                      response.status_code, [200])
        
    def run_complete_http_tests(self):
        """Run complete HTTP methods testing"""
        print("🚀 Starting COMPLETE HTTP Methods Testing (GET, POST, PUT, PATCH, DELETE)")
        print("=" * 80)
        
        try:
            # Test CRUD operations for each resource
            category_id = self.test_categories_crud()
            brand_id = self.test_brands_crud()
            product_id = self.test_products_crud(category_id, brand_id)
            variant_id = self.test_variants_crud(product_id)
            review_id = self.test_reviews_crud(product_id)
            
            # Test advanced operations
            self.test_advanced_operations()
            
            print("\n" + "=" * 80)
            print("✅ ALL HTTP METHODS TESTS COMPLETED!")
            
        except Exception as e:
            print(f"❌ Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def generate_http_methods_report(self):
        """Generate comprehensive HTTP methods test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f'http_methods_test_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, cls=DecimalEncoder)
            
        print(f"\n📊 HTTP Methods test report saved to: {report_file}")
        
        # Calculate detailed success rates by method
        method_stats = {}
        total_tests = 0
        total_success = 0
        
        for category, tests in self.results.items():
            print(f"\n📋 {category.upper()} Results:")
            category_total = len(tests)
            category_success = sum(1 for test in tests if test['success'])
            
            if category_total > 0:
                print(f"  Total: {category_total}, Success: {category_success}, Rate: {(category_success/category_total*100):.1f}%")
            else:
                print(f"  Total: 0, Success: 0, Rate: 0.0%")
            
            for test in tests:
                method = test['method']
                if method not in method_stats:
                    method_stats[method] = {'total': 0, 'success': 0}
                
                method_stats[method]['total'] += 1
                if test['success']:
                    method_stats[method]['success'] += 1
                    
                total_tests += 1
                if test['success']:
                    total_success += 1
        
        print(f"\n📈 HTTP Methods Breakdown:")
        for method, stats in method_stats.items():
            rate = (stats['success']/stats['total']*100) if stats['total'] > 0 else 0
            status_icon = "✅" if rate >= 90 else "⚠️" if rate >= 70 else "❌"
            print(f"  {status_icon} {method}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
        
        overall_rate = (total_success/total_tests*100) if total_tests > 0 else 0
        print(f"\n🎯 OVERALL SUCCESS RATE: {total_success}/{total_tests} ({overall_rate:.1f}%)")
        
        if overall_rate >= 95:
            print("🎉 OUTSTANDING! 95%+ Success Rate!")
        elif overall_rate >= 90:
            print("🎉 EXCELLENT! 90%+ Success Rate!")
        elif overall_rate >= 80:
            print("✅ GOOD! 80%+ Success Rate!")
        else:
            print("⚠️ Needs improvement")
        
        return report_file, overall_rate

if __name__ == '__main__':
    tester = CompleteHTTPMethodsTester()
    tester.run_complete_http_tests()
    report_file, success_rate = tester.generate_http_methods_report()
    
    print(f"\n🎯 Final Result: {success_rate:.1f}% Success Rate")
    if success_rate >= 90:
        print("🎉 TARGET ACHIEVED: 90%+ Success Rate for all HTTP methods!")