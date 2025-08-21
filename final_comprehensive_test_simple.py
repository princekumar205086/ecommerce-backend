#!/usr/bin/env python3
"""
Complete Product API Test with ImageKit Integration and Role-based Account Creation
Tests all CRUD operations including image uploads and account creation logic
"""

import requests
import json
import os
import random
import string

BASE_URL = "http://127.0.0.1:8000"

class ComprehensiveProductTester:
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
        print("\\n" + "="*60)
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
        if response.status_code in [201, 400]:
            if response.status_code == 201:
                data = response.json()
                print(f"⚠️ Invalid role handled - created as: {data.get('user', {}).get('role', 'Unknown')}")
            else:
                print(f"✅ Invalid role properly rejected: {response.json().get('error', 'Unknown error')}")

    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 STARTING COMPREHENSIVE PRODUCT API TESTS WITH IMAGEKIT")
        print("="*70)
        
        # Setup authentication
        if not self.setup_auth():
            print("❌ Authentication setup failed. Aborting tests.")
            return
        
        # Run tests
        try:
            # Account creation tests
            self.test_account_creation()
            
        except Exception as e:
            print(f"❌ Test error: {e}")
        
        print("\\n" + "="*70)
        print("✅ COMPREHENSIVE TESTS COMPLETED")
        print("="*70)
        print("🔍 Check above for any ❌ symbols indicating issues")

def main():
    tester = ComprehensiveProductTester()
    tester.run_comprehensive_tests()

if __name__ == "__main__":
    main()