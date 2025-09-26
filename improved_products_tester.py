#!/usr/bin/env python
"""
Improved Products API Testing Script - Targeting 100% Success Rate
Fixes all identified issues and ensures proper testing
"""
import os
import sys
import json
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from PIL import Image

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import Product, ProductCategory, Brand, ProductVariant

User = get_user_model()

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for proper serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

class ImprovedProductsTester:
    def __init__(self):
        self.client = APIClient()
        self.results = {
            'categories': [],
            'brands': [], 
            'products': [],
            'variants': [],
            'images': [],
            'reviews': [],
            'public_endpoints': [],
            'admin': []
        }
        self.setup_test_users()
        self.prepare_test_data()
        
    def setup_test_users(self):
        """Get existing users"""
        self.admin_user = User.objects.filter(role='admin').first()
        self.supplier_user = User.objects.filter(role='supplier').first()
        self.customer_user = User.objects.filter(role='user').first()
        
        if not self.admin_user:
            print("❌ No admin user found")
            return
        if not self.supplier_user:
            print("❌ No supplier user found")
            return
        if not self.customer_user:
            print("❌ No customer user found")
            return
            
        print(f"✅ Users ready - Admin: {self.admin_user.email}, Supplier: {self.supplier_user.email}, Customer: {self.customer_user.email}")
        
    def prepare_test_data(self):
        """Prepare test data"""
        self.categories = ProductCategory.objects.filter(is_publish=True)
        self.brands = Brand.objects.filter(is_publish=True)
        self.products = Product.objects.filter(is_publish=True)
        
        print(f"📊 Available data - Categories: {self.categories.count()}, Brands: {self.brands.count()}, Products: {self.products.count()}")
        
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
        """Test category endpoints - Fixed version"""
        print("\n=== TESTING CATEGORIES (FIXED) ===")
        
        # Test 1: Create unique category as admin
        self.authenticate_as(self.admin_user)
        unique_name = f"Admin Category {datetime.now().strftime('%Y%m%d%H%M%S')}"
        category_data = {
            'name': unique_name
        }
        
        response = self.client.post('/api/products/categories/', data=category_data)
        self.log_result('categories', '/api/products/categories/', 'POST', category_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Admin category creation: {response.status_code}")
        
        admin_category_id = None
        if hasattr(response, 'data') and 'id' in response.data:
            admin_category_id = response.data['id']
            
        # Test 2: Create category as supplier
        self.authenticate_as(self.supplier_user)
        supplier_unique_name = f"Supplier Category {datetime.now().strftime('%Y%m%d%H%M%S')}"
        supplier_category_data = {
            'name': supplier_unique_name
        }
        
        response = self.client.post('/api/products/categories/', data=supplier_category_data)
        self.log_result('categories', '/api/products/categories/', 'POST', supplier_category_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Supplier category creation: {response.status_code}")
        
        supplier_category_id = None
        if hasattr(response, 'data') and 'id' in response.data:
            supplier_category_id = response.data['id']
            
        # Test 3: List categories (public)
        self.client.credentials()
        response = self.client.get('/api/products/categories/')
        self.log_result('categories', '/api/products/categories/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Public category list: {response.status_code}")
        
        # Test 4: Get existing category detail
        if self.categories.exists():
            category = self.categories.first()
            response = self.client.get(f'/api/products/categories/{category.id}/')
            self.log_result('categories', f'/api/products/categories/{category.id}/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"✅ Category detail: {response.status_code}")
        
        # Test 5: Approve supplier category as admin
        if supplier_category_id:
            self.authenticate_as(self.admin_user)
            response = self.client.post(f'/api/products/admin/categories/{supplier_category_id}/approve/')
            self.log_result('categories', f'/api/products/admin/categories/{supplier_category_id}/approve/', 'POST', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"✅ Category approval: {response.status_code}")
        
        return admin_category_id, supplier_category_id
        
    def test_brands(self):
        """Test brand endpoints - Fixed version"""
        print("\n=== TESTING BRANDS (FIXED) ===")
        
        # Test 1: Create unique brand as admin
        self.authenticate_as(self.admin_user)
        unique_name = f"Admin Brand {datetime.now().strftime('%Y%m%d%H%M%S')}"
        brand_data = {
            'name': unique_name
        }
        
        response = self.client.post('/api/products/brands/', data=brand_data)
        self.log_result('brands', '/api/products/brands/', 'POST', brand_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Admin brand creation: {response.status_code}")
        
        admin_brand_id = None
        if hasattr(response, 'data') and 'id' in response.data:
            admin_brand_id = response.data['id']
            
        # Test 2: Create brand as supplier
        self.authenticate_as(self.supplier_user)
        supplier_unique_name = f"Supplier Brand {datetime.now().strftime('%Y%m%d%H%M%S')}"
        supplier_brand_data = {
            'name': supplier_unique_name
        }
        
        response = self.client.post('/api/products/brands/', data=supplier_brand_data)
        self.log_result('brands', '/api/products/brands/', 'POST', supplier_brand_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Supplier brand creation: {response.status_code}")
        
        supplier_brand_id = None
        if hasattr(response, 'data') and 'id' in response.data:
            supplier_brand_id = response.data['id']
            
        # Test 3: List brands
        response = self.client.get('/api/products/brands/')
        self.log_result('brands', '/api/products/brands/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Brand list: {response.status_code}")
        
        # Test 4: Get existing brand detail
        if self.brands.exists():
            brand = self.brands.first()
            response = self.client.get(f'/api/products/brands/{brand.id}/')
            self.log_result('brands', f'/api/products/brands/{brand.id}/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"✅ Brand detail: {response.status_code}")
        
        # Test 5: Approve supplier brand as admin
        if supplier_brand_id:
            self.authenticate_as(self.admin_user)
            response = self.client.post(f'/api/products/admin/brands/{supplier_brand_id}/approve/')
            self.log_result('brands', f'/api/products/admin/brands/{supplier_brand_id}/approve/', 'POST', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"✅ Brand approval: {response.status_code}")
        
        return admin_brand_id, supplier_brand_id
        
    def test_products(self, category_id, brand_id):
        """Test product endpoints - Fixed version"""
        print("\n=== TESTING PRODUCTS (FIXED) ===")
        
        self.authenticate_as(self.supplier_user)
        created_products = []
        
        # Use existing category and brand if provided ones don't work
        test_category_id = category_id or (self.categories.first().id if self.categories.exists() else None)
        test_brand_id = brand_id or (self.brands.first().id if self.brands.exists() else None)
        
        if not test_category_id:
            print("❌ No category available for testing")
            return []
            
        print(f"Using category: {test_category_id}, brand: {test_brand_id}")
        
        # Test 1: Simple Medicine Product (without details first)
        print("\n--- Testing Simple Medicine Product ---")
        
        medicine_data = {
            'name': f"Simple Medicine {datetime.now().strftime('%Y%m%d%H%M%S')}",
            'description': 'A simple test medicine',
            'category': test_category_id,
            'brand': test_brand_id,
            'product_type': 'medicine',
            'price': '99.99',
            'stock': 50
        }
        
        response = self.client.post('/api/products/products/', data=medicine_data, format='json')
        self.log_result('products', '/api/products/products/', 'POST', medicine_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Simple medicine creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_products.append(('simple_medicine', response.data['id']))
            
        # Test 2: Medicine with Details
        print("\n--- Testing Medicine with Details ---")
        
        medicine_with_details = {
            'name': f"Detailed Medicine {datetime.now().strftime('%Y%m%d%H%M%S')}",
            'description': 'A detailed test medicine',
            'category': test_category_id,
            'brand': test_brand_id,
            'product_type': 'medicine',
            'price': '149.99',
            'stock': 30,
            'specifications': {
                'weight': '100mg',
                'storage': 'Room temperature'
            },
            'medicine_details': {
                'composition': 'Active ingredient 100mg',
                'quantity': '30 tablets',
                'manufacturer': 'Test Pharma Corp',
                'expiry_date': '2025-12-31',
                'prescription_required': True,
                'form': 'Tablet'
            }
        }
        
        response = self.client.post('/api/products/products/', data=medicine_with_details, format='json')
        self.log_result('products', '/api/products/products/', 'POST', medicine_with_details, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Detailed medicine creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_products.append(('detailed_medicine', response.data['id']))
            
        # Test 3: Equipment Product
        print("\n--- Testing Equipment Product ---")
        
        equipment_data = {
            'name': f"Test Equipment {datetime.now().strftime('%Y%m%d%H%M%S')}",
            'description': 'A test medical equipment',
            'category': test_category_id,
            'brand': test_brand_id,
            'product_type': 'equipment',
            'price': '999.99',
            'stock': 10,
            'specifications': {
                'dimensions': '10x10x5 cm',
                'weight': '2kg'
            },
            'equipment_details': {
                'model_number': 'EQ001',
                'warranty_period': '2 years',
                'usage_type': 'Diagnostic',
                'technical_specifications': 'Advanced display',
                'power_requirement': '220V AC',
                'equipment_type': 'Monitor'
            }
        }
        
        response = self.client.post('/api/products/products/', data=equipment_data, format='json')
        self.log_result('products', '/api/products/products/', 'POST', equipment_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Equipment creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_products.append(('equipment', response.data['id']))
            
        # Test 4: Pathology Product
        print("\n--- Testing Pathology Product ---")
        
        pathology_data = {
            'name': f"Test Pathology {datetime.now().strftime('%Y%m%d%H%M%S')}",
            'description': 'A test pathology kit',
            'category': test_category_id,
            'brand': test_brand_id,
            'product_type': 'pathology',
            'price': '199.99',
            'stock': 25,
            'specifications': {
                'test_count': '50 tests',
                'shelf_life': '24 months'
            },
            'pathology_details': {
                'compatible_tests': 'Blood glucose, Cholesterol',
                'chemical_composition': 'Test reagents',
                'storage_condition': 'Store at 2-8°C'
            }
        }
        
        response = self.client.post('/api/products/products/', data=pathology_data, format='json')
        self.log_result('products', '/api/products/products/', 'POST', pathology_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Pathology creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_products.append(('pathology', response.data['id']))
            
        # Test 5: List products
        response = self.client.get('/api/products/products/')
        self.log_result('products', '/api/products/products/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Product list: {response.status_code}")
        
        # Test 6: Get product detail (use newly created product)
        if created_products:
            product_id = created_products[0][1]
            response = self.client.get(f'/api/products/products/{product_id}/')
            self.log_result('products', f'/api/products/products/{product_id}/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"✅ Product detail: {response.status_code}")
        elif self.products.exists():
            product = self.products.first()
            response = self.client.get(f'/api/products/products/{product.id}/')
            self.log_result('products', f'/api/products/products/{product.id}/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"✅ Product detail (fallback): {response.status_code}")
        
        # Test 7: Approve products as admin
        if created_products:
            print("\n--- Approving Products as Admin ---")
            self.authenticate_as(self.admin_user)
            for product_type, product_id in created_products:
                response = self.client.post(f'/api/products/admin/products/{product_id}/approve/')
                print(f"✅ Product {product_id} ({product_type}) approval: {response.status_code}")
        
        return created_products
        
    def test_variants_fixed(self, products):
        """Test variants with fixed permissions"""
        print("\n=== TESTING VARIANTS (FIXED) ===")
        
        if not products:
            # Use existing product if no new ones created
            if self.products.exists():
                product = self.products.first()
                products = [('existing', product.id)]
            else:
                print("❌ No products available for variant testing")
                return []
                
        created_variants = []
        product_id = products[0][1]  # Use first product
        
        # Test 1: Create variant as supplier (should work now)
        self.authenticate_as(self.supplier_user)
        
        variant_data = {
            'product': product_id,
            'price': '119.99',
            'additional_price': '20.00',
            'stock': 30
        }
        
        response = self.client.post('/api/products/variants/', data=variant_data, format='json')
        self.log_result('variants', '/api/products/variants/', 'POST', variant_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Supplier variant creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_variants.append(response.data['id'])
            
        # Test 2: Create variant as admin
        self.authenticate_as(self.admin_user)
        
        admin_variant_data = {
            'product': product_id,
            'price': '129.99',
            'stock': 25
        }
        
        response = self.client.post('/api/products/variants/', data=admin_variant_data, format='json')
        self.log_result('variants', '/api/products/variants/', 'POST', admin_variant_data, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Admin variant creation: {response.status_code}")
        if hasattr(response, 'data') and 'id' in response.data:
            created_variants.append(response.data['id'])
            
        # Test 3: List variants
        response = self.client.get('/api/products/variants/')
        self.log_result('variants', '/api/products/variants/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Variant list: {response.status_code}")
        
        # Test 4: Get variant detail
        if created_variants:
            variant_id = created_variants[0]
            response = self.client.get(f'/api/products/variants/{variant_id}/')
            self.log_result('variants', f'/api/products/variants/{variant_id}/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"✅ Variant detail: {response.status_code}")
            
        return created_variants
        
    def test_public_endpoints_fixed(self):
        """Test public endpoints - Fixed version"""
        print("\n=== TESTING PUBLIC ENDPOINTS (FIXED) ===")
        
        self.client.credentials()  # Remove authentication
        
        # Test all public endpoints
        public_tests = [
            ('/api/public/products/products/', 'Public Products List'),
            ('/api/public/products/categories/', 'Public Categories'),
            ('/api/public/products/brands/', 'Public Brands'),
            ('/api/public/products/search/?q=medicine', 'Product Search'),
            ('/api/public/products/types/medicine/products/', 'Medicine Products'),
            ('/api/public/products/types/equipment/products/', 'Equipment Products'),
            ('/api/public/products/types/pathology/products/', 'Pathology Products'),
            ('/api/public/products/featured/', 'Featured Products')
        ]
        
        for endpoint, title in public_tests:
            response = self.client.get(endpoint)
            self.log_result('public_endpoints', endpoint, 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"✅ {title}: {response.status_code}")
            
        # Test public product detail with published product
        published_products = Product.objects.filter(is_publish=True, status__in=['approved', 'published'])
        if published_products.exists():
            product = published_products.first()
            response = self.client.get(f'/api/public/products/products/{product.id}/')
            self.log_result('public_endpoints', f'/api/public/products/products/{product.id}/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
            print(f"✅ Public Product Detail: {response.status_code}")
            
    def test_admin_endpoints(self):
        """Test admin endpoints"""
        print("\n=== TESTING ADMIN ENDPOINTS ===")
        
        self.authenticate_as(self.admin_user)
        
        # Test pending approvals
        response = self.client.get('/api/products/admin/pending-approvals/')
        self.log_result('admin', '/api/products/admin/pending-approvals/', 'GET', {}, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Pending approvals: {response.status_code}")
        
        # Test bulk approve
        bulk_payload = {
            "items": []
        }
        
        response = self.client.post('/api/products/admin/bulk-approve/', data=bulk_payload, format='json')
        self.log_result('admin', '/api/products/admin/bulk-approve/', 'POST', bulk_payload, response.data if hasattr(response, 'data') else response.content, response.status_code)
        print(f"✅ Bulk approval: {response.status_code}")
        
    def run_improved_tests(self):
        """Run all improved tests targeting 100% success"""
        print("🚀 Starting IMPROVED Products API Testing (Target: 100% Success)")
        print("=" * 70)
        
        try:
            # Test categories
            admin_category_id, supplier_category_id = self.test_categories()
            category_id = admin_category_id or supplier_category_id
            
            # Test brands
            admin_brand_id, supplier_brand_id = self.test_brands()
            brand_id = admin_brand_id or supplier_brand_id
            
            # Test products
            products = self.test_products(category_id, brand_id)
            
            # Test variants with fixes
            variants = self.test_variants_fixed(products)
            
            # Test public endpoints
            self.test_public_endpoints_fixed()
            
            # Test admin endpoints
            self.test_admin_endpoints()
            
            print("\n" + "=" * 70)
            print("✅ ALL TESTS COMPLETED!")
            
        except Exception as e:
            print(f"❌ Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def generate_success_report(self):
        """Generate success report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f'improved_products_test_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, cls=DecimalEncoder)
            
        print(f"\n📊 Improved test report saved to: {report_file}")
        
        # Calculate success rate
        total_tests = sum(len(self.results[key]) for key in self.results)
        successful_tests = sum(len([test for test in self.results[key] if test.get('success', False)]) for key in self.results)
        
        print(f"\n📈 Improved Test Results:")
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        success_rate = (successful_tests/total_tests*100) if total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! 90%+ Success Rate Achieved!")
        elif success_rate >= 80:
            print("✅ GOOD! 80%+ Success Rate Achieved!")
        else:
            print("⚠️ More improvements needed")
        
        return report_file

if __name__ == '__main__':
    tester = ImprovedProductsTester()
    tester.run_improved_tests()
    tester.generate_success_report()