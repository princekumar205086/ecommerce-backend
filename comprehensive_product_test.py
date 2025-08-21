#!/usr/bin/env python3
"""
Comprehensive test script for Product App CRUD operations
Tests POST, PUT, PATCH, DELETE endpoints with proper authentication
Includes image upload testing with ImageKit integration
"""

import requests
import json
import os
from datetime import datetime, date

BASE_URL = "http://127.0.0.1:8000"

class ProductAPITester:
    def __init__(self):
        self.admin_token = None
        self.supplier_token = None
        self.user_token = None
        self.test_ids = {
            'category': None,
            'brand': None,
            'product': None,
            'variant': None,
            'review': None
        }
        
    def login(self, email, password):
        """Login and get JWT token"""
        response = requests.post(f"{BASE_URL}/api/accounts/login/", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json()['access']
        else:
            print(f"❌ Login failed for {email}: {response.text}")
            return None
    
    def setup_authentication(self):
        """Setup authentication tokens for all test users"""
        print("🔐 Setting up authentication...")
        
        # Admin login
        self.admin_token = self.login('admin@example.com', 'Admin@123')
        if self.admin_token:
            print("✅ Admin logged in successfully")
        
        # Supplier login
        self.supplier_token = self.login('supplier@example.com', 'testpass123')
        if self.supplier_token:
            print("✅ Supplier logged in successfully")
        
        # User login
        self.user_token = self.login('user@example.com', 'User@123')
        if self.user_token:
            print("✅ User logged in successfully")
    
    def get_headers(self, token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    def test_endpoint(self, method, endpoint, data=None, files=None, token=None, expected_status=None):
        """Test an API endpoint"""
        url = f"{BASE_URL}{endpoint}"
        headers = self.get_headers(token) if token else {}
        
        print(f"\n🧪 Testing {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                if files:
                    response = requests.put(url, data=data, files=files, headers=headers)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.put(url, json=data, headers=headers)
            elif method == 'PATCH':
                if files:
                    response = requests.patch(url, data=data, files=files, headers=headers)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            status_icon = "✅" if response.status_code in [200, 201, 204] else "❌"
            print(f"{status_icon} Status: {response.status_code}")
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    print(f"🔍 Error: {error_data}")
                except:
                    print(f"🔍 Error: {response.text}")
            else:
                try:
                    data = response.json()
                    if 'id' in data:
                        print(f"📦 Created/Updated ID: {data['id']}")
                        return data
                    elif isinstance(data, dict) and 'results' in data:
                        print(f"📦 Results count: {len(data['results'])}")
                    elif isinstance(data, list):
                        print(f"📦 Items count: {len(data)}")
                except:
                    pass
            
            return response.json() if response.status_code < 400 else None
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_image_file(self, filename):
        """Get image file for testing"""
        image_path = f"c:\\Users\\Prince Raj\\Desktop\\comestro\\ecommerce-backend\\media\\images\\{filename}"
        if os.path.exists(image_path):
            return open(image_path, 'rb')
        return None
    
    def test_categories(self):
        """Test ProductCategory CRUD operations"""
        print("\n" + "="*60)
        print("🏷️ TESTING PRODUCT CATEGORIES")
        print("="*60)
        
        # Test POST - Create category (Admin only)
        category_data = {
            "name": "Test Medicine Category",
        }
        
        # Try with image
        image_file = self.get_image_file("medicine.png")
        files = {"icon_file": image_file} if image_file else None
        
        category = self.test_endpoint(
            'POST', '/api/products/categories/',
            data=category_data,
            files=files,
            token=self.admin_token
        )
        
        if image_file:
            image_file.close()
        
        if category:
            self.test_ids['category'] = category['id']
            
            # Test PUT - Update category
            update_data = {
                "name": "Updated Test Medicine Category",
            }
            self.test_endpoint(
                'PUT', f"/api/products/categories/{category['id']}/",
                data=update_data,
                token=self.admin_token
            )
            
            # Test PATCH - Partial update
            patch_data = {"name": "Patched Medicine Category"}
            self.test_endpoint(
                'PATCH', f"/api/products/categories/{category['id']}/",
                data=patch_data,
                token=self.admin_token
            )
    
    def test_brands(self):
        """Test Brand CRUD operations"""
        print("\n" + "="*60)
        print("🏭 TESTING BRANDS")
        print("="*60)
        
        # Test POST - Create brand
        brand_data = {
            "name": "Test Pharma Brand"
        }
        
        # Try with image
        image_file = self.get_image_file("medixmall.jpg")
        files = {"image_file": image_file} if image_file else None
        
        brand = self.test_endpoint(
            'POST', '/api/products/brands/',
            data=brand_data,
            files=files,
            token=self.admin_token
        )
        
        if image_file:
            image_file.close()
        
        if brand:
            self.test_ids['brand'] = brand['id']
            
            # Test PUT - Update brand
            update_data = {"name": "Updated Test Pharma Brand"}
            self.test_endpoint(
                'PUT', f"/api/products/brands/{brand['id']}/",
                data=update_data,
                token=self.admin_token
            )
            
            # Test PATCH - Partial update
            patch_data = {"name": "Patched Pharma Brand"}
            self.test_endpoint(
                'PATCH', f"/api/products/brands/{brand['id']}/",
                data=patch_data,
                token=self.admin_token
            )
    
    def test_products(self):
        """Test Product CRUD operations"""
        print("\n" + "="*60)
        print("💊 TESTING PRODUCTS")
        print("="*60)
        
        # Test POST - Create product
        product_data = {
            "name": "Test Medicine Product",
            "description": "A test medicine for API testing",
            "product_type": "medicine",
            "price": "99.99",
            "stock": "100",
            "category": self.test_ids['category'],
            "brand": self.test_ids['brand'],
            # Medicine specific fields
            "composition": "Test Composition",
            "quantity": "10mg",
            "manufacturer": "Test Manufacturer",
            "form": "tablet",
            "pack_size": "10 tablets",
            "prescription_required": "false"
        }
        
        # Try with image
        image_file = self.get_image_file("glucose.webp")
        files = {"image_file": image_file} if image_file else None
        
        product = self.test_endpoint(
            'POST', '/api/products/products/',
            data=product_data,
            files=files,
            token=self.admin_token
        )
        
        if image_file:
            image_file.close()
        
        if product:
            self.test_ids['product'] = product['id']
            
            # Test PUT - Update product
            update_data = {
                "name": "Updated Test Medicine Product",
                "description": "Updated description",
                "product_type": "medicine",
                "price": "129.99",
                "stock": "150",
                "category": self.test_ids['category'],
                "brand": self.test_ids['brand'],
                "composition": "Updated Composition",
                "quantity": "20mg",
                "manufacturer": "Updated Manufacturer",
                "form": "capsule",
                "pack_size": "20 capsules",
                "prescription_required": "true"
            }
            self.test_endpoint(
                'PUT', f"/api/products/products/{product['id']}/",
                data=update_data,
                token=self.admin_token
            )
            
            # Test PATCH - Partial update
            patch_data = {
                "price": "139.99",
                "stock": "200"
            }
            self.test_endpoint(
                'PATCH', f"/api/products/products/{product['id']}/",
                data=patch_data,
                token=self.admin_token
            )
    
    def test_variants(self):
        """Test ProductVariant CRUD operations"""
        print("\n" + "="*60)
        print("🔄 TESTING PRODUCT VARIANTS")
        print("="*60)
        
        if not self.test_ids['product']:
            print("❌ No product available for variant testing")
            return
        
        # Test POST - Create variant
        variant_data = {
            "product": self.test_ids['product'],
            "size": "Large",
            "weight": "500g",
            "additional_price": "10.00",
            "stock": "50"
        }
        
        variant = self.test_endpoint(
            'POST', '/api/products/variants/',
            data=variant_data,
            token=self.admin_token
        )
        
        if variant:
            self.test_ids['variant'] = variant['id']
            
            # Test PUT - Update variant
            update_data = {
                "product": self.test_ids['product'],
                "size": "Extra Large",
                "weight": "750g",
                "additional_price": "15.00",
                "stock": "25"
            }
            self.test_endpoint(
                'PUT', f"/api/products/variants/{variant['id']}/",
                data=update_data,
                token=self.admin_token
            )
            
            # Test PATCH - Partial update
            patch_data = {
                "additional_price": "20.00",
                "stock": "30"
            }
            self.test_endpoint(
                'PATCH', f"/api/products/variants/{variant['id']}/",
                data=patch_data,
                token=self.admin_token
            )
    
    def test_reviews(self):
        """Test ProductReview CRUD operations"""
        print("\n" + "="*60)
        print("⭐ TESTING PRODUCT REVIEWS")
        print("="*60)
        
        if not self.test_ids['product']:
            print("❌ No product available for review testing")
            return
        
        # Test POST - Create review (as regular user)
        review_data = {
            "product": self.test_ids['product'],
            "rating": 5,
            "comment": "Excellent product! Works as expected."
        }
        
        review = self.test_endpoint(
            'POST', '/api/products/reviews/',
            data=review_data,
            token=self.user_token
        )
        
        if review:
            self.test_ids['review'] = review['id']
            
            # Test PUT - Update review
            update_data = {
                "product": self.test_ids['product'],
                "rating": 4,
                "comment": "Good product, but could be improved."
            }
            self.test_endpoint(
                'PUT', f"/api/products/reviews/{review['id']}/",
                data=update_data,
                token=self.user_token
            )
            
            # Test PATCH - Partial update
            patch_data = {
                "rating": 5,
                "comment": "Actually, it's excellent after using it more!"
            }
            self.test_endpoint(
                'PATCH', f"/api/products/reviews/{review['id']}/",
                data=patch_data,
                token=self.user_token
            )
    
    def test_supplier_prices(self):
        """Test SupplierProductPrice CRUD operations"""
        print("\n" + "="*60)
        print("💰 TESTING SUPPLIER PRICES")
        print("="*60)
        
        if not self.test_ids['product']:
            print("❌ No product available for supplier price testing")
            return
        
        # Test POST - Create supplier price (as supplier)
        price_data = {
            "product": self.test_ids['product'],
            "price": "89.99",
            "pincode": "110001",
            "district": "New Delhi"
        }
        
        supplier_price = self.test_endpoint(
            'POST', '/api/products/supplier-prices/',
            data=price_data,
            token=self.supplier_token
        )
        
        if supplier_price:
            # Test PUT - Update supplier price
            update_data = {
                "product": self.test_ids['product'],
                "price": "79.99",
                "pincode": "110001",
                "district": "New Delhi"
            }
            self.test_endpoint(
                'PUT', f"/api/products/supplier-prices/{supplier_price['id']}/",
                data=update_data,
                token=self.supplier_token
            )
            
            # Test PATCH - Partial update
            patch_data = {"price": "84.99"}
            self.test_endpoint(
                'PATCH', f"/api/products/supplier-prices/{supplier_price['id']}/",
                data=patch_data,
                token=self.supplier_token
            )
    
    def test_permission_errors(self):
        """Test that unauthorized users get proper errors"""
        print("\n" + "="*60)
        print("🔒 TESTING PERMISSION RESTRICTIONS")
        print("="*60)
        
        # Test regular user trying to create category (should fail)
        category_data = {"name": "Unauthorized Category"}
        self.test_endpoint(
            'POST', '/api/products/categories/',
            data=category_data,
            token=self.user_token
        )
        
        # Test unauthenticated user trying to create product (should fail)
        product_data = {
            "name": "Unauthorized Product",
            "price": "10.00"
        }
        self.test_endpoint(
            'POST', '/api/products/products/',
            data=product_data,
            token=None
        )
    
    def test_deletes(self):
        """Test DELETE operations"""
        print("\n" + "="*60)
        print("🗑️ TESTING DELETE OPERATIONS")
        print("="*60)
        
        # Delete review
        if self.test_ids['review']:
            self.test_endpoint(
                'DELETE', f"/api/products/reviews/{self.test_ids['review']}/",
                token=self.user_token
            )
        
        # Delete variant
        if self.test_ids['variant']:
            self.test_endpoint(
                'DELETE', f"/api/products/variants/{self.test_ids['variant']}/",
                token=self.admin_token
            )
        
        # Delete product
        if self.test_ids['product']:
            self.test_endpoint(
                'DELETE', f"/api/products/products/{self.test_ids['product']}/",
                token=self.admin_token
            )
        
        # Delete brand
        if self.test_ids['brand']:
            self.test_endpoint(
                'DELETE', f"/api/products/brands/{self.test_ids['brand']}/",
                token=self.admin_token
            )
        
        # Delete category
        if self.test_ids['category']:
            self.test_endpoint(
                'DELETE', f"/api/products/categories/{self.test_ids['category']}/",
                token=self.admin_token
            )
    
    def test_account_creation_fix(self):
        """Test account creation with role validation"""
        print("\n" + "="*60)
        print("👤 TESTING ACCOUNT CREATION FIX")
        print("="*60)
        
        # Test creating user account
        user_data = {
            "email": "newuser@example.com",
            "password": "TestPass123",
            "full_name": "New Test User",
            "contact": "9999999999"
        }
        
        response = self.test_endpoint(
            'POST', '/api/accounts/register/user/',
            data=user_data
        )
        
        if response:
            print(f"✅ User created with role: {response.get('user', {}).get('role')}")
        
        # Test creating supplier account
        supplier_data = {
            "email": "newsupplier@example.com",
            "password": "TestPass123",
            "full_name": "New Test Supplier",
            "contact": "8888888888"
        }
        
        response = self.test_endpoint(
            'POST', '/api/accounts/register/supplier/',
            data=supplier_data
        )
        
        if response:
            print(f"✅ Supplier created with role: {response.get('user', {}).get('role')}")
        
        # Test invalid role (should fail or default to user)
        invalid_data = {
            "email": "invalid@example.com",
            "password": "TestPass123",
            "full_name": "Invalid Role User",
            "contact": "7777777777"
        }
        
        response = self.test_endpoint(
            'POST', '/api/accounts/register/admin/',
            data=invalid_data
        )
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING COMPREHENSIVE PRODUCT API TESTS")
        print("="*60)
        
        # Setup authentication
        self.setup_authentication()
        
        if not all([self.admin_token, self.supplier_token, self.user_token]):
            print("❌ Failed to authenticate all users. Aborting tests.")
            return
        
        # Run tests in order
        self.test_account_creation_fix()
        self.test_categories()
        self.test_brands()
        self.test_products()
        self.test_variants()
        self.test_reviews()
        self.test_supplier_prices()
        self.test_permission_errors()
        self.test_deletes()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        print("📊 Check the output above for any failed tests")
        print("🔍 Look for ❌ symbols to identify issues")

def main():
    tester = ProductAPITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()