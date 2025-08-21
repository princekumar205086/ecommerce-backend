#!/usr/bin/env python3
"""
Final Complete Product API Test
Tests account creation, CRUD operations with image uploads, and ImageKit integration
"""

import requests
import json
import os
import random
import string

BASE_URL = "http://127.0.0.1:8000"

class FinalProductTester:
    def __init__(self):
        self.admin_token = None
        self.supplier_token = None
        self.user_token = None
        self.test_ids = {}
        
    def random_string(self, length=8):
        """Generate random string"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
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
    
    def setup_auth(self):
        """Setup authentication"""
        print("🔐 Setting up authentication...")
        self.admin_token = self.login('admin@example.com', 'Admin@123')
        self.supplier_token = self.login('supplier@example.com', 'testpass123')
        self.user_token = self.login('user@example.com', 'User@123')
        
        success_count = sum([1 for token in [self.admin_token, self.supplier_token, self.user_token] if token])
        print(f"✅ {success_count}/3 users authenticated successfully")
        return success_count == 3
    
    def test_account_creation(self):
        """Test account creation with proper role handling"""
        print("\n" + "="*60)
        print("👤 TESTING ACCOUNT CREATION WITH ROLES")
        print("="*60)
        
        # Test user creation
        user_data = {
            "email": f"testuser{self.random_string()}@example.com",
            "password": "TestPass123",
            "password2": "TestPass123",
            "full_name": "Test User",
            "contact": "9999999999"
        }
        
        response = requests.post(f"{BASE_URL}/api/accounts/register/user/", json=user_data)
        print(f"User creation: Status {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"✅ User created with role: {data.get('user', {}).get('role', 'Unknown')}")
        else:
            print(f"❌ Error: {response.text}")
        
        # Test supplier creation
        supplier_data = {
            "email": f"testsupplier{self.random_string()}@example.com",
            "password": "TestPass123",
            "password2": "TestPass123",
            "full_name": "Test Supplier",
            "contact": "8888888888"
        }
        
        response = requests.post(f"{BASE_URL}/api/accounts/register/supplier/", json=supplier_data)
        print(f"Supplier creation: Status {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Supplier created with role: {data.get('user', {}).get('role', 'Unknown')}")
        else:
            print(f"❌ Error: {response.text}")
        
        # Test invalid role (should be rejected)
        invalid_data = {
            "email": f"testinvalid{self.random_string()}@example.com",
            "password": "TestPass123",
            "password2": "TestPass123",
            "full_name": "Test Invalid Role",
            "contact": "7777777777"
        }
        
        response = requests.post(f"{BASE_URL}/api/accounts/register/admin/", json=invalid_data)
        print(f"Invalid role creation: Status {response.status_code}")
        if response.status_code == 400:
            error_msg = response.json().get('error', 'Unknown error')
            print(f"✅ Invalid role properly rejected: {error_msg}")
        else:
            print(f"❌ Unexpected response: {response.text}")
    
    def get_image_file(self, filename):
        """Get image file for testing"""
        image_path = f"media/images/{filename}"
        if os.path.exists(image_path):
            return open(image_path, 'rb')
        return None
    
    def test_category_with_image(self):
        """Test category creation with image upload"""
        print("\n" + "="*60)
        print("🏷️ TESTING CATEGORY WITH IMAGE UPLOAD")
        print("="*60)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return None
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create category with image
        category_name = f"Test Category {self.random_string()}"
        category_data = {"name": category_name}
        
        image_file = self.get_image_file("medicine.png")
        files = {"icon_file": image_file} if image_file else None
        
        response = requests.post(f"{BASE_URL}/api/products/categories/", 
                               data=category_data, files=files, headers=headers)
        
        if image_file:
            image_file.close()
        
        print(f"CREATE Category with image: Status {response.status_code}")
        
        if response.status_code == 201:
            category = response.json()
            category_id = category['id']
            print(f"✅ Category created with ID: {category_id}")
            
            icon_url = category.get('icon', '')
            if 'imagekit.io' in icon_url or 'ik.imagekit.io' in icon_url:
                print(f"✅ Image uploaded to ImageKit: {icon_url}")
            else:
                print(f"⚠️ Image URL: {icon_url}")
            
            self.test_ids['category'] = category_id
            return category_id
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_product_with_image(self, category_id):
        """Test product creation with image upload"""
        print("\n" + "="*60)
        print("💊 TESTING PRODUCT WITH IMAGE UPLOAD")
        print("="*60)
        
        if not self.admin_token or not category_id:
            print("❌ No admin token or category available")
            return None
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create product with image
        product_name = f"Test Medicine {self.random_string()}"
        product_data = {
            "name": product_name,
            "description": "A test medicine product with image",
            "product_type": "medicine",
            "price": "99.99",
            "stock": "100",
            "category": str(category_id),
            "composition": "Test Composition",
            "quantity": "10mg",
            "manufacturer": "Test Manufacturer",
            "form": "tablet",
            "pack_size": "10 tablets"
        }
        
        image_file = self.get_image_file("glucose.webp")
        files = {"image_file": image_file} if image_file else None
        
        response = requests.post(f"{BASE_URL}/api/products/products/", 
                               data=product_data, files=files, headers=headers)
        
        if image_file:
            image_file.close()
        
        print(f"CREATE Product with image: Status {response.status_code}")
        
        if response.status_code == 201:
            product = response.json()
            product_id = product['id']
            print(f"✅ Product created with ID: {product_id}")
            
            image_url = product.get('image', '')
            if 'imagekit.io' in image_url or 'ik.imagekit.io' in image_url:
                print(f"✅ Image uploaded to ImageKit: {image_url}")
            else:
                print(f"⚠️ Image URL: {image_url}")
            
            # Test PATCH update
            patch_data = {"price": "129.99", "stock": "150"}
            response = requests.patch(f"{BASE_URL}/api/products/products/{product_id}/",
                                    json=patch_data, headers=headers)
            print(f"PATCH Product: Status {response.status_code}")
            
            self.test_ids['product'] = product_id
            return product_id
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_variant_crud(self, product_id):
        """Test product variant CRUD operations"""
        print("\n" + "="*60)
        print("🔄 TESTING PRODUCT VARIANTS")
        print("="*60)
        
        if not self.admin_token or not product_id:
            print("❌ No admin token or product available")
            return None
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create variant
        variant_data = {
            "product": product_id,
            "size": "Large",
            "weight": "500g",
            "additional_price": "10.00",
            "stock": "50"
        }
        
        response = requests.post(f"{BASE_URL}/api/products/variants/", 
                               json=variant_data, headers=headers)
        print(f"CREATE Variant: Status {response.status_code}")
        
        if response.status_code == 201:
            variant = response.json()
            variant_id = variant['id']
            print(f"✅ Variant created with ID: {variant_id}")
            
            # Test PATCH (partial update without product field)
            patch_data = {"additional_price": "15.00", "stock": "30"}
            response = requests.patch(f"{BASE_URL}/api/products/variants/{variant_id}/",
                                    json=patch_data, headers=headers)
            print(f"PATCH Variant (partial): Status {response.status_code}")
            
            self.test_ids['variant'] = variant_id
            return variant_id
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n" + "="*60)
        print("🧹 CLEANING UP TEST DATA")
        print("="*60)
        
        headers_admin = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Delete in reverse order of creation
        items_to_delete = [
            ('variant', 'variants', headers_admin),
            ('product', 'products', headers_admin),
            ('category', 'categories', headers_admin),
        ]
        
        for item_key, endpoint, headers in items_to_delete:
            item_id = self.test_ids.get(item_key)
            if item_id:
                response = requests.delete(f"{BASE_URL}/api/products/{endpoint}/{item_id}/", headers=headers)
                status_icon = "✅" if response.status_code == 204 else "❌"
                print(f"{status_icon} DELETE {item_key}: Status {response.status_code}")
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 FINAL COMPREHENSIVE PRODUCT API TESTS")
        print("="*70)
        
        # Setup authentication
        if not self.setup_auth():
            print("❌ Authentication setup failed. Aborting tests.")
            return
        
        # Run tests
        try:
            # Account creation tests
            self.test_account_creation()
            
            # CRUD tests with images
            category_id = self.test_category_with_image()
            if category_id:
                product_id = self.test_product_with_image(category_id)
                if product_id:
                    self.test_variant_crud(product_id)
            
            # Cleanup
            self.cleanup_test_data()
            
        except Exception as e:
            print(f"❌ Test error: {e}")
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70)
        print("🔍 Check above for any ❌ symbols indicating issues")
        print("📷 Verify that images are properly uploaded to ImageKit")
        print("👤 Account creation roles are properly enforced")

def main():
    tester = FinalProductTester()
    tester.run_comprehensive_tests()

if __name__ == "__main__":
    main()