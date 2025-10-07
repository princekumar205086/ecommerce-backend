#!/usr/bin/env python3
"""
Simple focused test script to debug and fix product API issues
"""

import requests
import json
import random
import time

BASE_URL = "http://127.0.0.1:8000"

class SimpleProductTester:
    def __init__(self):
        self.admin_token = None
        self.supplier_token = None
        self.user_token = None
        
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
        
        if self.admin_token:
            print("✅ Admin logged in")
        if self.supplier_token:
            print("✅ Supplier logged in")
        if self.user_token:
            print("✅ User logged in")
    
    def test_account_creation(self):
        """Test account creation with proper role handling"""
        print("\n" + "="*50)
        print("👤 TESTING ACCOUNT CREATION")
        print("="*50)
        
        # Test user creation
        timestamp = int(time.time())
        user_data = {
            "email": f"testuser{timestamp}@example.com",
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
            "email": f"testsupplier{timestamp}@example.com",
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
    
    def test_category_crud(self):
        """Test category CRUD operations"""
        print("\n" + "="*50)
        print("🏷️ TESTING CATEGORY CRUD")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return None
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create category
        timestamp = int(time.time())
        category_data = {"name": f"Test Category {timestamp}"}
        response = requests.post(f"{BASE_URL}/api/products/categories/", 
                               json=category_data, headers=headers)
        print(f"CREATE Category: Status {response.status_code}")
        
        if response.status_code == 201:
            category = response.json()
            category_id = category['id']
            print(f"✅ Category created with ID: {category_id}")
            
            # Test UPDATE
            update_data = {"name": "Updated Test Category"}
            response = requests.put(f"{BASE_URL}/api/products/categories/{category_id}/",
                                  json=update_data, headers=headers)
            print(f"UPDATE Category: Status {response.status_code}")
            
            # Test PATCH
            patch_data = {"name": "Patched Test Category"}
            response = requests.patch(f"{BASE_URL}/api/products/categories/{category_id}/",
                                    json=patch_data, headers=headers)
            print(f"PATCH Category: Status {response.status_code}")
            
            return category_id
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_brand_crud(self):
        """Test brand CRUD operations"""
        print("\n" + "="*50)
        print("🏭 TESTING BRAND CRUD")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return None
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create brand
        timestamp = int(time.time())
        brand_data = {"name": f"Test Brand {timestamp}"}
        response = requests.post(f"{BASE_URL}/api/products/brands/", 
                               json=brand_data, headers=headers)
        print(f"CREATE Brand: Status {response.status_code}")
        
        if response.status_code == 201:
            brand = response.json()
            brand_id = brand['id']
            print(f"✅ Brand created with ID: {brand_id}")
            
            # Test UPDATE
            update_data = {"name": "Updated Test Brand"}
            response = requests.put(f"{BASE_URL}/api/products/brands/{brand_id}/",
                                  json=update_data, headers=headers)
            print(f"UPDATE Brand: Status {response.status_code}")
            
            # Test PATCH
            patch_data = {"name": "Patched Test Brand"}
            response = requests.patch(f"{BASE_URL}/api/products/brands/{brand_id}/",
                                    json=patch_data, headers=headers)
            print(f"PATCH Brand: Status {response.status_code}")
            
            return brand_id
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_product_crud(self, category_id, brand_id):
        """Test product CRUD operations"""
        print("\n" + "="*50)
        print("💊 TESTING PRODUCT CRUD")
        print("="*50)
        
        if not self.admin_token or not category_id:
            print("❌ No admin token or category available")
            return None
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create product
        timestamp = int(time.time())
        product_data = {
            "name": f"Test Medicine {timestamp}",
            "description": "A test medicine product",
            "product_type": "medicine",
            "price": "99.99",
            "stock": "100",
            "category": category_id,
            "brand": brand_id,
            "composition": "Test Composition",
            "quantity": "10mg",
            "manufacturer": "Test Manufacturer",
            "form": "tablet",
            "pack_size": "10 tablets"
        }
        
        response = requests.post(f"{BASE_URL}/api/products/products/", 
                               json=product_data, headers=headers)
        print(f"CREATE Product: Status {response.status_code}")
        
        if response.status_code == 201:
            product = response.json()
            product_id = product['id']
            print(f"✅ Product created with ID: {product_id}")
            
            # Test UPDATE
            update_data = {
                "name": "Updated Test Medicine",
                "description": "Updated description",
                "product_type": "medicine",
                "price": "129.99",
                "stock": "150",
                "category": category_id,
                "brand": brand_id,
                "composition": "Updated Composition"
            }
            response = requests.put(f"{BASE_URL}/api/products/products/{product_id}/",
                                  json=update_data, headers=headers)
            print(f"UPDATE Product: Status {response.status_code}")
            
            # Test PATCH
            patch_data = {"price": "139.99", "stock": "200"}
            response = requests.patch(f"{BASE_URL}/api/products/products/{product_id}/",
                                    json=patch_data, headers=headers)
            print(f"PATCH Product: Status {response.status_code}")
            
            return product_id
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_review_crud(self, product_id):
        """Test review CRUD operations"""
        print("\n" + "="*50)
        print("⭐ TESTING REVIEW CRUD")
        print("="*50)
        
        if not self.user_token or not product_id:
            print("❌ No user token or product available")
            return None
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Create review
        review_data = {
            "product": product_id,
            "rating": 5,
            "comment": "Excellent product!"
        }
        
        response = requests.post(f"{BASE_URL}/api/products/reviews/", 
                               json=review_data, headers=headers)
        print(f"CREATE Review: Status {response.status_code}")
        
        if response.status_code == 201:
            review = response.json()
            review_id = review['id']
            print(f"✅ Review created with ID: {review_id}")
            
            # Test UPDATE
            update_data = {
                "product": product_id,
                "rating": 4,
                "comment": "Good product, but could be better"
            }
            response = requests.put(f"{BASE_URL}/api/products/reviews/{review_id}/",
                                  json=update_data, headers=headers)
            print(f"UPDATE Review: Status {response.status_code}")
            
            # Test PATCH
            patch_data = {"rating": 5, "comment": "Actually, it's excellent!"}
            response = requests.patch(f"{BASE_URL}/api/products/reviews/{review_id}/",
                                    json=patch_data, headers=headers)
            print(f"PATCH Review: Status {response.status_code}")
            
            return review_id
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_deletes(self, category_id, brand_id, product_id, review_id):
        """Test DELETE operations"""
        print("\n" + "="*50)
        print("🗑️ TESTING DELETE OPERATIONS")
        print("="*50)
        
        headers_admin = {"Authorization": f"Bearer {self.admin_token}"}
        headers_user = {"Authorization": f"Bearer {self.user_token}"}
        
        # Delete review
        if review_id:
            response = requests.delete(f"{BASE_URL}/api/products/reviews/{review_id}/",
                                     headers=headers_user)
            print(f"DELETE Review: Status {response.status_code}")
        
        # Delete product
        if product_id:
            response = requests.delete(f"{BASE_URL}/api/products/products/{product_id}/",
                                     headers=headers_admin)
            print(f"DELETE Product: Status {response.status_code}")
        
        # Delete brand
        if brand_id:
            response = requests.delete(f"{BASE_URL}/api/products/brands/{brand_id}/",
                                     headers=headers_admin)
            print(f"DELETE Brand: Status {response.status_code}")
        
        # Delete category
        if category_id:
            response = requests.delete(f"{BASE_URL}/api/products/categories/{category_id}/",
                                     headers=headers_admin)
            print(f"DELETE Category: Status {response.status_code}")
    
    def run_tests(self):
        """Run all tests"""
        print("🚀 STARTING SIMPLE PRODUCT CRUD TESTS")
        print("="*60)
        
        self.setup_auth()
        
        if not all([self.admin_token, self.user_token]):
            print("❌ Missing required authentication tokens")
            return
        
        # Test account creation
        self.test_account_creation()
        
        # Test CRUD operations
        category_id = self.test_category_crud()
        brand_id = self.test_brand_crud()
        product_id = self.test_product_crud(category_id, brand_id)
        review_id = self.test_review_crud(product_id)
        
        # Test deletes
        self.test_deletes(category_id, brand_id, product_id, review_id)
        
        print("\n" + "="*60)
        print("✅ SIMPLE TESTS COMPLETED")
        print("="*60)

def main():
    tester = SimpleProductTester()
    tester.run_tests()

if __name__ == "__main__":
    main()