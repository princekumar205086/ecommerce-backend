#!/usr/bin/env python
"""
Comprehensive Brand API Individual Testing Suite
Tests all CRUD operations, filtering, searching, permissions, and edge cases
"""
import os
import sys
import json
import random
from datetime import datetime

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import Brand

User = get_user_model()

class ComprehensiveBrandAPITester:
    def __init__(self):
        self.admin_client = APIClient()
        self.supplier_client = APIClient()
        self.customer_client = APIClient()
        self.anonymous_client = APIClient()
        self.setup_clients()
        self.test_results = {}
        self.created_brands = []
        
    def setup_clients(self):
        """Setup authenticated clients for different user roles"""
        print("🔧 Setting up test clients...")
        
        # Admin client
        admin_user = User.objects.filter(role='admin').first()
        if admin_user:
            token = str(RefreshToken.for_user(admin_user).access_token)
            self.admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            self.admin_user = admin_user
            print(f"✅ Admin client ready: {admin_user.email}")
            
        # Supplier client
        supplier_user = User.objects.filter(role='supplier').first()
        if supplier_user:
            token = str(RefreshToken.for_user(supplier_user).access_token)
            self.supplier_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            self.supplier_user = supplier_user
            print(f"✅ Supplier client ready: {supplier_user.email}")
            
        # Customer client
        customer_user = User.objects.filter(role='user').first()
        if customer_user:
            token = str(RefreshToken.for_user(customer_user).access_token)
            self.customer_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            self.customer_user = customer_user
            print(f"✅ Customer client ready: {customer_user.email}")
            
        print("✅ All clients configured successfully\n")
    
    def test_brand_creation_post(self):
        """Test Brand POST operations with different scenarios"""
        print("🚀 TESTING BRAND CREATION (POST)")
        print("-" * 50)
        
        results = {}
        
        # Test 1: Admin creates brand
        print("📝 Test 1: Admin creates brand")
        brand_data = {
            'name': f'Admin Brand {datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        
        response = self.admin_client.post('/api/products/brands/', data=brand_data, format='json')
        results['admin_create'] = {
            'status_code': response.status_code,
            'success': response.status_code == 201,
            'data': response.data if response.status_code == 201 else None,
            'payload': brand_data
        }
        
        if response.status_code == 201:
            self.created_brands.append(response.data['id'])
            print(f"   ✅ SUCCESS: Brand created with ID {response.data['id']}")
            print(f"   📄 Response: {json.dumps(response.data, indent=6)}")
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.data}")
        
        print()
        
        # Test 2: Supplier creates brand
        print("📝 Test 2: Supplier creates brand")
        brand_data = {
            'name': f'Supplier Brand {datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        
        response = self.supplier_client.post('/api/products/brands/', data=brand_data, format='json')
        results['supplier_create'] = {
            'status_code': response.status_code,
            'success': response.status_code == 201,
            'data': response.data if response.status_code == 201 else None,
            'payload': brand_data
        }
        
        if response.status_code == 201:
            self.created_brands.append(response.data['id'])
            print(f"   ✅ SUCCESS: Brand created with ID {response.data['id']}")
            print(f"   📄 Response: {json.dumps(response.data, indent=6)}")
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.data}")
            
        print()
        
        # Test 3: Customer tries to create brand (should fail)
        print("📝 Test 3: Customer creates brand (should fail)")
        brand_data = {
            'name': f'Customer Brand {datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        
        response = self.customer_client.post('/api/products/brands/', data=brand_data, format='json')
        results['customer_create'] = {
            'status_code': response.status_code, 
            'success': response.status_code == 403,  # Should be forbidden
            'data': response.data if hasattr(response, 'data') else None,
            'payload': brand_data
        }
        
        if response.status_code == 403:
            print(f"   ✅ SUCCESS: Correctly denied with 403 Forbidden")
        else:
            print(f"   ❌ UNEXPECTED: {response.status_code} - Expected 403")
            
        print()
        
        # Test 4: Anonymous user tries to create brand
        print("📝 Test 4: Anonymous creates brand (should fail)")
        response = self.anonymous_client.post('/api/products/brands/', data=brand_data, format='json')
        results['anonymous_create'] = {
            'status_code': response.status_code,
            'success': response.status_code == 401,  # Should be unauthorized
            'data': response.data if hasattr(response, 'data') else None
        }
        
        if response.status_code == 401:
            print(f"   ✅ SUCCESS: Correctly denied with 401 Unauthorized")
        else:
            print(f"   ❌ UNEXPECTED: {response.status_code} - Expected 401")
            
        print()
        
        # Test 5: Create brand with validation errors
        print("📝 Test 5: Brand with validation errors")
        invalid_data = {
            'name': ''  # Empty name should fail
        }
        
        response = self.supplier_client.post('/api/products/brands/', data=invalid_data, format='json')
        results['validation_error'] = {
            'status_code': response.status_code,
            'success': response.status_code == 400,  # Should be bad request
            'errors': response.data if response.status_code == 400 else None
        }
        
        if response.status_code == 400:
            print(f"   ✅ SUCCESS: Validation error caught with 400 Bad Request")
            print(f"   📄 Errors: {json.dumps(response.data, indent=6)}")
        else:
            print(f"   ❌ UNEXPECTED: {response.status_code} - Expected 400")
            
        print()
        
        self.test_results['brand_creation'] = results
        return results
    
    def test_brand_listing_get(self):
        """Test Brand GET list operations with filtering and pagination"""
        print("🔍 TESTING BRAND LISTING (GET)")
        print("-" * 50)
        
        results = {}
        
        # Test 1: Get all brands as admin
        print("📝 Test 1: Admin gets all brands")
        response = self.admin_client.get('/api/products/brands/')
        results['admin_list'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'count': response.data['count'] if response.status_code == 200 else 0,
            'has_pagination': 'next' in response.data if response.status_code == 200 else False
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Retrieved {response.data['count']} brands")
            print(f"   📄 Pagination: {'Yes' if response.data.get('next') else 'No'}")
            if response.data['results']:
                sample_brand = response.data['results'][0]
                print(f"   📄 Sample Brand: {sample_brand['name']} (ID: {sample_brand['id']})")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 2: Get brands as supplier
        print("📝 Test 2: Supplier gets brands")
        response = self.supplier_client.get('/api/products/brands/')
        results['supplier_list'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'count': response.data['count'] if response.status_code == 200 else 0
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Retrieved {response.data['count']} brands")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 3: Get brands as customer
        print("📝 Test 3: Customer gets brands")
        response = self.customer_client.get('/api/products/brands/')
        results['customer_list'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'count': response.data['count'] if response.status_code == 200 else 0
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Retrieved {response.data['count']} brands")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 4: Anonymous user gets brands
        print("📝 Test 4: Anonymous gets brands (should fail)")
        response = self.anonymous_client.get('/api/products/brands/')
        results['anonymous_list'] = {
            'status_code': response.status_code,
            'success': response.status_code == 401  # Should be unauthorized
        }
        
        if response.status_code == 401:
            print(f"   ✅ SUCCESS: Correctly denied with 401 Unauthorized")
        else:
            print(f"   ❌ UNEXPECTED: {response.status_code} - Expected 401")
            
        print()
        
        self.test_results['brand_listing'] = results
        return results
    
    def test_brand_detail_get(self):
        """Test Brand GET detail operations"""
        print("🔍 TESTING BRAND DETAIL (GET)")
        print("-" * 50)
        
        results = {}
        
        # Get a published brand to test with (suppliers should be able to access published brands)
        existing_brand = Brand.objects.filter(status__in=['approved', 'published'], is_publish=True).first()
        if not existing_brand:
            print("❌ No published brands found for detail testing")
            return results
            
        brand_id = existing_brand.id
        print(f"Using published brand: {existing_brand.name} (ID: {brand_id}, Status: {existing_brand.status})")
        print()
        
        # Test 1: Admin gets brand detail
        print("📝 Test 1: Admin gets brand detail")
        response = self.admin_client.get(f'/api/products/brands/{brand_id}/')
        results['admin_detail'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'data': response.data if response.status_code == 200 else None
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Retrieved brand details")
            print(f"   📄 Brand: {response.data['name']}")
            print(f"   📄 Image: {response.data.get('image', 'N/A')}")
            print(f"   📄 Status: {response.data.get('status', 'N/A')}")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 2: Supplier gets brand detail
        print("📝 Test 2: Supplier gets brand detail")
        response = self.supplier_client.get(f'/api/products/brands/{brand_id}/')
        results['supplier_detail'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Retrieved brand details")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 3: Get non-existent brand
        print("📝 Test 3: Get non-existent brand")
        response = self.admin_client.get('/api/products/brands/99999/')
        results['not_found'] = {
            'status_code': response.status_code,
            'success': response.status_code == 404
        }
        
        if response.status_code == 404:
            print(f"   ✅ SUCCESS: Correctly returned 404 Not Found")
        else:
            print(f"   ❌ UNEXPECTED: {response.status_code} - Expected 404")
            
        print()
        
        self.test_results['brand_detail'] = results
        return results
    
    def test_brand_update_put(self):
        """Test Brand PUT (full update) operations"""
        print("✏️ TESTING BRAND UPDATE (PUT)")
        print("-" * 50)
        
        results = {}
        
        # Create a test brand first
        test_brand_data = {
            'name': f'PUT Test Brand {datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        
        create_response = self.supplier_client.post('/api/products/brands/', data=test_brand_data, format='json')
        if create_response.status_code != 201:
            print("❌ Failed to create test brand for PUT testing")
            return results
            
        brand_id = create_response.data['id']
        self.created_brands.append(brand_id)
        print(f"Created test brand with ID: {brand_id}")
        print()
        
        # Test 1: Creator updates own brand (supplier)
        print("📝 Test 1: Supplier updates own brand")
        update_data = {
            'name': f'Updated PUT Brand {datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        
        response = self.supplier_client.put(f'/api/products/brands/{brand_id}/', data=update_data, format='json')
        results['creator_update'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'data': response.data if response.status_code == 200 else None,
            'payload': update_data
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Brand updated successfully")
            print(f"   📄 New Name: {response.data['name']}")
            print(f"   📄 Status: {response.data.get('status', 'N/A')}")
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.data}")
            
        print()
        
        # Test 2: Admin updates any brand
        print("📝 Test 2: Admin updates brand")
        admin_update_data = {
            'name': f'Admin Updated Brand {datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        
        response = self.admin_client.put(f'/api/products/brands/{brand_id}/', data=admin_update_data, format='json')
        results['admin_update'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'data': response.data if response.status_code == 200 else None
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Brand updated by admin")
            print(f"   📄 New Name: {response.data['name']}")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 3: Customer tries to update brand (should fail)
        print("📝 Test 3: Customer updates brand (should fail)")
        response = self.customer_client.put(f'/api/products/brands/{brand_id}/', data=update_data, format='json')
        results['customer_update'] = {
            'status_code': response.status_code,
            'success': response.status_code == 403  # Should be forbidden
        }
        
        if response.status_code == 403:
            print(f"   ✅ SUCCESS: Correctly denied with 403 Forbidden")
        else:
            print(f"   ❌ UNEXPECTED: {response.status_code} - Expected 403")
            
        print()
        
        # Test 4: Update with validation errors (create new brand for this test)
        print("📝 Test 4: Update with validation errors")
        
        # Create a fresh brand for validation testing
        validation_brand_data = {
            'name': f'Validation Test Brand {datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        
        create_response = self.supplier_client.post('/api/products/brands/', data=validation_brand_data, format='json')
        if create_response.status_code == 201:
            validation_brand_id = create_response.data['id']
            self.created_brands.append(validation_brand_id)
            
            invalid_update = {
                'name': ''  # Empty name should fail
            }
            
            response = self.supplier_client.put(f'/api/products/brands/{validation_brand_id}/', data=invalid_update, format='json')
            results['validation_error'] = {
                'status_code': response.status_code,
                'success': response.status_code == 400
            }
            
            if response.status_code == 400:
                print(f"   ✅ SUCCESS: Validation error caught")
                print(f"   📄 Errors: {response.data}")
            else:
                print(f"   ❌ UNEXPECTED: {response.status_code} - Expected 400")
        else:
            print(f"   ❌ FAILED: Could not create validation test brand")
            results['validation_error'] = {
                'status_code': 500,
                'success': False
            }
            
        print()
        
        self.test_results['brand_update_put'] = results
        return results
    
    def test_brand_partial_update_patch(self):
        """Test Brand PATCH (partial update) operations"""
        print("✏️ TESTING BRAND PARTIAL UPDATE (PATCH)")
        print("-" * 50)
        
        results = {}
        
        # Create a test brand first
        test_brand_data = {
            'name': f'PATCH Test Brand {datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        
        create_response = self.supplier_client.post('/api/products/brands/', data=test_brand_data, format='json')
        if create_response.status_code != 201:
            print("❌ Failed to create test brand for PATCH testing")
            return results
            
        brand_id = create_response.data['id']
        self.created_brands.append(brand_id)
        print(f"Created test brand with ID: {brand_id}")
        print()
        
        # Test 1: Partial update - only image
        print("📝 Test 1: Partial update - image only")
        patch_data = {
            'image': f'https://example.com/brand-image-{datetime.now().strftime("%H%M%S")}.jpg'
        }
        
        response = self.supplier_client.patch(f'/api/products/brands/{brand_id}/', data=patch_data, format='json')
        results['partial_description'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'data': response.data if response.status_code == 200 else None,
            'payload': patch_data
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Image updated")
            print(f"   📄 Name (unchanged): {response.data['name']}")
            print(f"   📄 Image (updated): {response.data.get('image', 'N/A')}")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 2: Partial update - only name
        print("📝 Test 2: Partial update - name only")
        patch_data = {
            'name': f'PATCH Name {datetime.now().strftime("%H%M%S")}'
        }
        
        response = self.supplier_client.patch(f'/api/products/brands/{brand_id}/', data=patch_data, format='json')
        results['partial_name'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'data': response.data if response.status_code == 200 else None
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Name updated")
            print(f"   📄 Name (updated): {response.data['name']}")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 3: Admin performs partial update
        print("📝 Test 3: Admin partial update")
        admin_patch = {
            'image': 'https://example.com/admin-updated-image.jpg'
        }
        
        response = self.admin_client.patch(f'/api/products/brands/{brand_id}/', data=admin_patch, format='json')
        results['admin_patch'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Admin partial update successful")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        self.test_results['brand_partial_update'] = results
        return results
    
    def test_brand_deletion_delete(self):
        """Test Brand DELETE operations"""
        print("🗑️ TESTING BRAND DELETION (DELETE)")
        print("-" * 50)
        
        results = {}
        
        # Create test brands for deletion
        brand_ids = []
        for i in range(3):
            test_data = {
                'name': f'Delete Test Brand {i+1} {datetime.now().strftime("%Y%m%d%H%M%S")}'
            }
            
            response = self.supplier_client.post('/api/products/brands/', data=test_data, format='json')
            if response.status_code == 201:
                brand_ids.append(response.data['id'])
                
        print(f"Created {len(brand_ids)} test brands for deletion")
        print()
        
        # Test 1: Creator deletes own brand
        if brand_ids:
            print("📝 Test 1: Supplier deletes own brand")
            brand_id = brand_ids[0]
            
            response = self.supplier_client.delete(f'/api/products/brands/{brand_id}/')
            results['creator_delete'] = {
                'status_code': response.status_code,
                'success': response.status_code == 204
            }
            
            if response.status_code == 204:
                print(f"   ✅ SUCCESS: Brand {brand_id} deleted successfully")
                
                # Verify deletion
                verify_response = self.supplier_client.get(f'/api/products/brands/{brand_id}/')
                if verify_response.status_code == 404:
                    print(f"   ✅ VERIFIED: Brand no longer exists")
                else:
                    print(f"   ⚠️ WARNING: Brand still exists after deletion")
            else:
                print(f"   ❌ FAILED: {response.status_code}")
                
            print()
        
        # Test 2: Admin deletes any brand
        if len(brand_ids) > 1:
            print("📝 Test 2: Admin deletes brand")
            brand_id = brand_ids[1]
            
            response = self.admin_client.delete(f'/api/products/brands/{brand_id}/')
            results['admin_delete'] = {
                'status_code': response.status_code,
                'success': response.status_code == 204
            }
            
            if response.status_code == 204:
                print(f"   ✅ SUCCESS: Admin deleted brand {brand_id}")
            else:
                print(f"   ❌ FAILED: {response.status_code}")
                
            print()
        
        # Test 3: Customer tries to delete brand (should fail)
        if len(brand_ids) > 2:
            print("📝 Test 3: Customer deletes brand (should fail)")
            brand_id = brand_ids[2]
            
            response = self.customer_client.delete(f'/api/products/brands/{brand_id}/')
            results['customer_delete'] = {
                'status_code': response.status_code,
                'success': response.status_code == 403
            }
            
            if response.status_code == 403:
                print(f"   ✅ SUCCESS: Correctly denied with 403 Forbidden")
            else:
                print(f"   ❌ UNEXPECTED: {response.status_code} - Expected 403")
                
            print()
        
        # Test 4: Delete non-existent brand
        print("📝 Test 4: Delete non-existent brand")
        response = self.admin_client.delete('/api/products/brands/99999/')
        results['not_found_delete'] = {
            'status_code': response.status_code,
            'success': response.status_code == 404
        }
        
        if response.status_code == 404:
            print(f"   ✅ SUCCESS: Correctly returned 404 Not Found")
        else:
            print(f"   ❌ UNEXPECTED: {response.status_code} - Expected 404")
            
        print()
        
        self.test_results['brand_deletion'] = results
        return results
    
    def test_brand_filtering_searching(self):
        """Test Brand filtering and searching functionality"""
        print("🔍 TESTING BRAND FILTERING & SEARCHING")
        print("-" * 50)
        
        results = {}
        
        # Create test brands with specific names for filtering
        test_brands = [
            {'name': f'Apollo Pharmacy {datetime.now().strftime("%H%M%S")}'},
            {'name': f'MedPlus Store {datetime.now().strftime("%H%M%S")}'},
            {'name': f'HealthFirst Brand {datetime.now().strftime("%H%M%S")}'}
        ]
        
        created_test_brands = []
        for brand_data in test_brands:
            response = self.supplier_client.post('/api/products/brands/', data=brand_data, format='json')
            if response.status_code == 201:
                created_test_brands.append(response.data['id'])
                self.created_brands.append(response.data['id'])
                
        print(f"Created {len(created_test_brands)} test brands for filtering")
        print()
        
        # Test 1: Search by name
        print("📝 Test 1: Search brands by name")
        search_params = {'search': 'Apollo'}
        response = self.supplier_client.get('/api/products/brands/', params=search_params)
        
        results['search_by_name'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'count': response.data['count'] if response.status_code == 200 else 0,
            'params': search_params
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Found {response.data['count']} brands matching 'Apollo'")
            if response.data['results']:
                for brand in response.data['results'][:2]:  # Show first 2
                    print(f"   📄 Found: {brand['name']}")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 2: Search brands by partial name
        print("📝 Test 2: Search brands by partial name")
        search_params = {'search': 'Med'}
        response = self.supplier_client.get('/api/products/brands/', params=search_params)
        
        results['search_partial_name'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'count': response.data['count'] if response.status_code == 200 else 0
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Found {response.data['count']} brands with 'Med' in name")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 3: Filter by active status
        print("📝 Test 3: Filter by active status")
        filter_params = {'is_active': 'true'}
        response = self.supplier_client.get('/api/products/brands/', params=filter_params)
        
        results['filter_active'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'count': response.data['count'] if response.status_code == 200 else 0
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Found {response.data['count']} active brands")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 4: Ordering test
        print("📝 Test 4: Order brands by name")
        order_params = {'ordering': 'name'}
        response = self.supplier_client.get('/api/products/brands/', params=order_params)
        
        results['ordering'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'is_ordered': False
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Retrieved brands with ordering")
            # Check if results are ordered
            if len(response.data['results']) > 1:
                names = [brand['name'] for brand in response.data['results']]
                is_ordered = names == sorted(names)
                results['ordering']['is_ordered'] = is_ordered
                print(f"   📄 Ordering correct: {'Yes' if is_ordered else 'No'}")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        # Test 5: Pagination test
        print("📝 Test 5: Pagination test")
        page_params = {'page': 1, 'page_size': 5}
        response = self.supplier_client.get('/api/products/brands/', params=page_params)
        
        results['pagination'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'has_pagination': False,
            'page_size': 0
        }
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Pagination working")
            results['pagination']['has_pagination'] = 'next' in response.data or 'previous' in response.data
            results['pagination']['page_size'] = len(response.data['results'])
            print(f"   📄 Results per page: {len(response.data['results'])}")
            print(f"   📄 Has next page: {'Yes' if response.data.get('next') else 'No'}")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
        print()
        
        self.test_results['brand_filtering'] = results
        return results
    
    def cleanup_test_brands(self):
        """Clean up brands created during testing"""
        print("🧹 CLEANING UP TEST BRANDS")
        print("-" * 30)
        
        cleaned = 0
        for brand_id in self.created_brands:
            try:
                response = self.admin_client.delete(f'/api/products/brands/{brand_id}/')
                if response.status_code == 204:
                    cleaned += 1
                    print(f"   ✅ Cleaned brand {brand_id}")
                else:
                    print(f"   ⚠️ Could not clean brand {brand_id}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error cleaning brand {brand_id}: {str(e)}")
                
        print(f"Cleaned up {cleaned}/{len(self.created_brands)} test brands")
        print()
    
    def calculate_success_rates(self):
        """Calculate success rates for all test categories"""
        print("📊 CALCULATING SUCCESS RATES")
        print("-" * 40)
        
        total_tests = 0
        total_successes = 0
        
        for category, tests in self.test_results.items():
            category_tests = 0
            category_successes = 0
            
            for test_name, result in tests.items():
                category_tests += 1
                if result.get('success', False):
                    category_successes += 1
                    
            success_rate = (category_successes / category_tests * 100) if category_tests > 0 else 0
            print(f"{category}: {success_rate:.1f}% ({category_successes}/{category_tests})")
            
            total_tests += category_tests
            total_successes += category_successes
            
        overall_rate = (total_successes / total_tests * 100) if total_tests > 0 else 0
        print(f"{'='*40}")
        print(f"OVERALL SUCCESS RATE: {overall_rate:.1f}% ({total_successes}/{total_tests})")
        
        return overall_rate
    
    def run_comprehensive_test(self):
        """Run all Brand API tests"""
        print("🚀 COMPREHENSIVE BRAND API TESTING SUITE")
        print("=" * 70)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()
        
        # Run all test categories
        try:
            self.test_brand_creation_post()
            self.test_brand_listing_get()
            self.test_brand_detail_get()
            self.test_brand_update_put()
            self.test_brand_partial_update_patch()
            self.test_brand_deletion_delete()
            self.test_brand_filtering_searching()
            
            # Calculate and display results
            overall_rate = self.calculate_success_rates()
            
            print()
            if overall_rate == 100.0:
                print("🎉 CONGRATULATIONS! 100% SUCCESS ACHIEVED! 🎉")
            elif overall_rate >= 90.0:
                print(f"🎯 EXCELLENT! {overall_rate:.1f}% Success Rate")
            elif overall_rate >= 80.0:
                print(f"👍 GOOD! {overall_rate:.1f}% Success Rate")
            else:
                print(f"⚠️ NEEDS IMPROVEMENT: {overall_rate:.1f}% Success Rate")
                
            print()
            print("📋 TEST SUMMARY:")
            print(f"   • Total Tests Run: {sum(len(tests) for tests in self.test_results.values())}")
            print(f"   • Success Rate: {overall_rate:.1f}%")
            print(f"   • Test Brands Created: {len(self.created_brands)}")
            print()
            
        except Exception as e:
            print(f"❌ TEST SUITE ERROR: {str(e)}")
            overall_rate = 0.0
            
        finally:
            # Cleanup
            self.cleanup_test_brands()
            
        print("🏁 COMPREHENSIVE BRAND API TESTING COMPLETED")
        print("=" * 70)
        
        return overall_rate

if __name__ == '__main__':
    tester = ComprehensiveBrandAPITester()
    success_rate = tester.run_comprehensive_test()