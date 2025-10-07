#!/usr/bin/env python3
"""
Comprehensive test including image upload functionality
"""

import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"

class ComprehensiveProductTester:
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
        
        return all([self.admin_token, self.supplier_token, self.user_token])
    
    def get_image_file(self, filename):
        """Get image file for testing"""
        image_path = f"c:\\Users\\Prince Raj\\Desktop\\comestro\\ecommerce-backend\\media\\images\\{filename}"
        if os.path.exists(image_path):
            return open(image_path, 'rb')
        return None
    
    def test_image_upload_category(self):
        """Test category creation with image upload"""
        print("\n" + "="*50)
        print("📷 TESTING CATEGORY WITH IMAGE UPLOAD")
        print("="*50)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        timestamp = int(time.time())
        
        # Test with image
        image_file = self.get_image_file("medicine.png")
        
        if image_file:
            data = {"name": f"Medicine Category {timestamp}"}
            files = {"icon_file": image_file}
            
            response = requests.post(f"{BASE_URL}/api/products/categories/",
                                   data=data, files=files, headers=headers)
            print(f"Category with image: Status {response.status_code}")
            
            if response.status_code == 201:
                category = response.json()
                print(f"✅ Category created with ID: {category['id']}")
                if category.get('icon'):
                    print(f"✅ Image URL: {category['icon']}")
                    return category['id']
                else:
                    print("⚠️ No image URL returned")
            else:
                print(f"❌ Error: {response.text}")
            
            image_file.close()
        else:
            print("❌ Image file not found")
        
        return None
    
    def test_image_upload_brand(self):
        """Test brand creation with image upload"""
        print("\n" + "="*50)
        print("📷 TESTING BRAND WITH IMAGE UPLOAD")
        print("="*50)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        timestamp = int(time.time())
        
        # Test with image
        image_file = self.get_image_file("medixmall.jpg")
        
        if image_file:
            data = {"name": f"Test Brand {timestamp}"}
            files = {"image_file": image_file}
            
            response = requests.post(f"{BASE_URL}/api/products/brands/",
                                   data=data, files=files, headers=headers)
            print(f"Brand with image: Status {response.status_code}")
            
            if response.status_code == 201:
                brand = response.json()
                print(f"✅ Brand created with ID: {brand['id']}")
                if brand.get('image'):
                    print(f"✅ Image URL: {brand['image']}")
                    return brand['id']
                else:
                    print("⚠️ No image URL returned")
            else:
                print(f"❌ Error: {response.text}")
            
            image_file.close()
        else:
            print("❌ Image file not found")
        
        return None
    
    def test_image_upload_product(self, category_id, brand_id):
        """Test product creation with image upload"""
        print("\n" + "="*50)
        print("📷 TESTING PRODUCT WITH IMAGE UPLOAD")
        print("="*50)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        timestamp = int(time.time())
        
        # Test with image
        image_file = self.get_image_file("glucose.webp")
        
        if image_file:
            data = {
                "name": f"Test Medicine {timestamp}",
                "description": "A test medicine with image",
                "product_type": "medicine",
                "price": "99.99",
                "stock": "100",
                "category": str(category_id),
                "brand": str(brand_id),
                "composition": "Test Composition",
                "quantity": "10mg",
                "manufacturer": "Test Manufacturer",
                "form": "tablet",
                "pack_size": "10 tablets"
            }
            files = {"image_file": image_file}
            
            response = requests.post(f"{BASE_URL}/api/products/products/",
                                   data=data, files=files, headers=headers)
            print(f"Product with image: Status {response.status_code}")
            
            if response.status_code == 201:
                product = response.json()
                print(f"✅ Product created with ID: {product['id']}")
                if product.get('image'):
                    print(f"✅ Image URL: {product['image']}")
                    return product['id']
                else:
                    print("⚠️ No image URL returned")
            else:
                print(f"❌ Error: {response.text}")
            
            image_file.close()
        else:
            print("❌ Image file not found")
        
        return None
    
    def test_variant_crud(self, product_id):
        """Test product variant CRUD operations"""
        print("\n" + "="*50)
        print("🔄 TESTING PRODUCT VARIANTS")
        print("="*50)
        
        if not product_id:
            print("❌ No product available")
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
            
            # Test UPDATE
            update_data = {
                "product": product_id,
                "size": "Extra Large",
                "weight": "750g",
                "additional_price": "15.00",
                "stock": "25"
            }
            response = requests.put(f"{BASE_URL}/api/products/variants/{variant_id}/",
                                  json=update_data, headers=headers)
            print(f"UPDATE Variant: Status {response.status_code}")
            
            # Test PATCH
            patch_data = {"additional_price": "20.00"}
            response = requests.patch(f"{BASE_URL}/api/products/variants/{variant_id}/",
                                    json=patch_data, headers=headers)
            print(f"PATCH Variant: Status {response.status_code}")
            
            return variant_id
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_supplier_prices(self, product_id):
        """Test supplier price CRUD operations"""
        print("\n" + "="*50)
        print("💰 TESTING SUPPLIER PRICES")
        print("="*50)
        
        if not product_id:
            print("❌ No product available")
            return None
        
        headers = {"Authorization": f"Bearer {self.supplier_token}"}
        
        # Create supplier price
        price_data = {
            "product": product_id,
            "price": "89.99",
            "pincode": "110001",
            "district": "New Delhi"
        }
        
        response = requests.post(f"{BASE_URL}/api/products/supplier-prices/",
                               json=price_data, headers=headers)
        print(f"CREATE Supplier Price: Status {response.status_code}")
        
        if response.status_code == 201:
            price = response.json()
            price_id = price['id']
            print(f"✅ Supplier price created with ID: {price_id}")
            
            # Test UPDATE
            update_data = {
                "product": product_id,
                "price": "79.99",
                "pincode": "110001",
                "district": "New Delhi"
            }
            response = requests.put(f"{BASE_URL}/api/products/supplier-prices/{price_id}/",
                                  json=update_data, headers=headers)
            print(f"UPDATE Supplier Price: Status {response.status_code}")
            
            # Test PATCH
            patch_data = {"price": "84.99"}
            response = requests.patch(f"{BASE_URL}/api/products/supplier-prices/{price_id}/",
                                    json=patch_data, headers=headers)
            print(f"PATCH Supplier Price: Status {response.status_code}")
            
            return price_id
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_equipment_product(self, category_id, brand_id):
        """Test equipment type product creation"""
        print("\n" + "="*50)
        print("🔧 TESTING EQUIPMENT PRODUCT")
        print("="*50)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        timestamp = int(time.time())
        
        # Create equipment product
        equipment_data = {
            "name": f"Test Equipment {timestamp}",
            "description": "A test equipment product",
            "product_type": "equipment",
            "price": "1999.99",
            "stock": "50",
            "category": category_id,
            "brand": brand_id,
            "model_number": "TEST-EQ-001",
            "warranty_period": "2 years",
            "usage_type": "Professional",
            "technical_specifications": "High-quality medical equipment",
            "power_requirement": "220V AC",
            "equipment_type": "Diagnostic"
        }
        
        response = requests.post(f"{BASE_URL}/api/products/products/",
                               json=equipment_data, headers=headers)
        print(f"CREATE Equipment: Status {response.status_code}")
        
        if response.status_code == 201:
            equipment = response.json()
            print(f"✅ Equipment created with ID: {equipment['id']}")
            return equipment['id']
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_pathology_product(self, category_id, brand_id):
        """Test pathology type product creation"""
        print("\n" + "="*50)
        print("🧪 TESTING PATHOLOGY PRODUCT")
        print("="*50)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        timestamp = int(time.time())
        
        # Create pathology product
        pathology_data = {
            "name": f"Test Pathology {timestamp}",
            "description": "A test pathology product",
            "product_type": "pathology",
            "price": "299.99",
            "stock": "200",
            "category": category_id,
            "brand": brand_id,
            "compatible_tests": "Blood Test, Urine Test",
            "chemical_composition": "Sodium Chloride, Potassium",
            "storage_condition": "Store in cool, dry place"
        }
        
        response = requests.post(f"{BASE_URL}/api/products/products/",
                               json=pathology_data, headers=headers)
        print(f"CREATE Pathology: Status {response.status_code}")
        
        if response.status_code == 201:
            pathology = response.json()
            print(f"✅ Pathology product created with ID: {pathology['id']}")
            return pathology['id']
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 STARTING COMPREHENSIVE PRODUCT API TESTS")
        print("="*60)
        
        if not self.setup_auth():
            print("❌ Authentication failed")
            return
        
        # Test with image uploads
        category_id = self.test_image_upload_category()
        brand_id = self.test_image_upload_brand()
        
        if category_id and brand_id:
            # Test products with different types
            medicine_id = self.test_image_upload_product(category_id, brand_id)
            equipment_id = self.test_equipment_product(category_id, brand_id)
            pathology_id = self.test_pathology_product(category_id, brand_id)
            
            # Test related functionality
            if medicine_id:
                variant_id = self.test_variant_crud(medicine_id)
                price_id = self.test_supplier_prices(medicine_id)
        
        print("\n" + "="*60)
        print("✅ COMPREHENSIVE TESTS COMPLETED")
        print("="*60)
        print("📊 Check the output above for any issues")
        print("📷 Pay special attention to image upload results")

def main():
    tester = ComprehensiveProductTester()
    tester.run_comprehensive_tests()

if __name__ == "__main__":
    main()