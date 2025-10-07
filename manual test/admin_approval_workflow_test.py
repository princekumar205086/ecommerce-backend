#!/usr/bin/env python
"""
Admin Approval Workflow Test Suite
Tests the complete admin approval system for supplier-created entities
"""
import os
import sys
import json
import random
from datetime import datetime, date
from decimal import Decimal

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import (
    ProductCategory, Brand, Product, ProductVariant, 
    SupplierProductPrice
)

User = get_user_model()

class AdminApprovalWorkflowTest:
    def __init__(self):
        self.client = Client()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {},
            'approval_workflow_entities': {}
        }
        self.users = {}
        self.pending_entities = {
            'categories': [],
            'brands': [],
            'products': []
        }
        
    def log_test(self, test_name, status, details=None, error=None):
        """Log a test result"""
        result = {
            'test_name': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'error': str(error) if error else None
        }
        self.test_results['tests'].append(result)
        
        if status == 'PASS':
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}: {error or details}")
            
    def setup_test_users(self):
        """Setup test users"""
        try:
            # Get or create admin user
            admin_user, _ = User.objects.get_or_create(
                email='admin@example.com',
                defaults={
                    'full_name': 'Admin User',
                    'contact': '1234567890',
                    'role': 'admin',
                    'is_staff': True,
                    'is_active': True,
                    'email_verified': True
                }
            )
            admin_user.set_password('Admin@123')
            admin_user.save()
            self.users['admin'] = admin_user
            
            # Get or create supplier user
            supplier_user, _ = User.objects.get_or_create(
                email='supplier@example.com',
                defaults={
                    'full_name': 'Supplier User',
                    'contact': '0987654321',
                    'role': 'supplier',
                    'is_active': True,
                    'email_verified': True
                }
            )
            supplier_user.set_password('Supplier@123')
            supplier_user.save()
            self.users['supplier'] = supplier_user
            
            self.log_test("Setup Admin Approval Test Users", "PASS")
            
        except Exception as e:
            self.log_test("Setup Admin Approval Test Users", "FAIL", error=e)
            
    def get_auth_headers(self, user):
        """Get authentication headers for a user"""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
        
    def test_supplier_category_creation_and_approval(self):
        """Test supplier creates category and admin approves it"""
        print("\n📁 Testing Supplier Category Creation & Admin Approval Workflow...")
        
        supplier_headers = self.get_auth_headers(self.users['supplier'])
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        # Step 1: Supplier creates category
        category_data = {
            'name': f'Supplier Test Category {random.randint(1000, 9999)}',
            'icon': 'http://127.0.0.1:8000/media/images/medical-pattern.svg'
        }
        
        try:
            response = self.client.post('/api/products/categories/', 
                                      data=json.dumps(category_data),
                                      content_type='application/json',
                                      **supplier_headers)
            
            if response.status_code == 201:
                category_id = response.json()['id']
                category_status = response.json().get('status', 'unknown')
                is_published = response.json().get('is_publish', False)
                
                self.pending_entities['categories'].append(category_id)
                self.log_test("Supplier Creates Category", "PASS", {
                    "category_id": category_id,
                    "status": category_status,
                    "is_published": is_published,
                    "requires_approval": True
                })
                
                # Step 2: Verify category is pending
                if category_status == 'pending' and not is_published:
                    self.log_test("Category Status Pending", "PASS", {"awaiting_admin_approval": True})
                else:
                    self.log_test("Category Status Pending", "FAIL", {
                        "expected_pending": True,
                        "actual_status": category_status,
                        "is_published": is_published
                    })
                
                # Step 3: Admin approves category using the approval endpoint
                try:
                    approval_response = self.client.post(f'/api/products/admin/categories/{category_id}/approve/', 
                                                       **admin_headers)
                    
                    if approval_response.status_code == 200:
                        self.log_test("Admin Approves Category", "PASS", {
                            "category_id": category_id,
                            "approval_response": approval_response.json()
                        })
                        
                        # Step 4: Verify category is now published
                        verify_response = self.client.get(f'/api/products/categories/{category_id}/', 
                                                        **admin_headers)
                        
                        if verify_response.status_code == 200:
                            updated_category = verify_response.json()
                            if updated_category.get('status') == 'approved' and updated_category.get('is_publish'):
                                self.log_test("Category Approval Verification", "PASS", {
                                    "status": updated_category.get('status'),
                                    "is_published": updated_category.get('is_publish'),
                                    "approved_by": updated_category.get('approved_by')
                                })
                            else:
                                self.log_test("Category Approval Verification", "FAIL", {
                                    "status": updated_category.get('status'),
                                    "is_published": updated_category.get('is_publish')
                                })
                        
                    else:
                        self.log_test("Admin Approves Category", "FAIL", {
                            "status_code": approval_response.status_code,
                            "response": approval_response.json() if approval_response.content else "No content"
                        })
                        
                except Exception as e:
                    self.log_test("Admin Approves Category", "FAIL", error=e)
                    
            else:
                self.log_test("Supplier Creates Category", "FAIL", {
                    "status_code": response.status_code,
                    "response": response.json()
                })
                
        except Exception as e:
            self.log_test("Supplier Creates Category", "FAIL", error=e)
            
    def test_supplier_brand_creation_and_approval(self):
        """Test supplier creates brand and admin approves it"""
        print("\n🏷️ Testing Supplier Brand Creation & Admin Approval Workflow...")
        
        supplier_headers = self.get_auth_headers(self.users['supplier'])
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        # Step 1: Supplier creates brand
        brand_data = {
            'name': f'Supplier Test Brand {random.randint(1000, 9999)}',
            'image': 'http://127.0.0.1:8000/media/images/medical-pattern.svg'
        }
        
        try:
            response = self.client.post('/api/products/brands/', 
                                      data=json.dumps(brand_data),
                                      content_type='application/json',
                                      **supplier_headers)
            
            if response.status_code == 201:
                brand_id = response.json()['id']
                brand_status = response.json().get('status', 'unknown')
                is_published = response.json().get('is_publish', False)
                
                self.pending_entities['brands'].append(brand_id)
                self.log_test("Supplier Creates Brand", "PASS", {
                    "brand_id": brand_id,
                    "status": brand_status,
                    "is_published": is_published,
                    "requires_approval": True
                })
                
                # Step 2: Admin approves brand
                try:
                    approval_response = self.client.post(f'/api/products/admin/brands/{brand_id}/approve/', 
                                                       **admin_headers)
                    
                    if approval_response.status_code == 200:
                        self.log_test("Admin Approves Brand", "PASS", {
                            "brand_id": brand_id,
                            "approval_response": approval_response.json()
                        })
                        
                        # Verify brand is now published
                        verify_response = self.client.get(f'/api/products/brands/{brand_id}/', 
                                                        **admin_headers)
                        
                        if verify_response.status_code == 200:
                            updated_brand = verify_response.json()
                            if updated_brand.get('status') == 'approved' and updated_brand.get('is_publish'):
                                self.log_test("Brand Approval Verification", "PASS", {
                                    "status": updated_brand.get('status'),
                                    "is_published": updated_brand.get('is_publish')
                                })
                            else:
                                self.log_test("Brand Approval Verification", "FAIL", {
                                    "status": updated_brand.get('status'),
                                    "is_published": updated_brand.get('is_publish')
                                })
                        
                    else:
                        self.log_test("Admin Approves Brand", "FAIL", {
                            "status_code": approval_response.status_code,
                            "response": approval_response.json() if approval_response.content else "No content"
                        })
                        
                except Exception as e:
                    self.log_test("Admin Approves Brand", "FAIL", error=e)
                    
            else:
                self.log_test("Supplier Creates Brand", "FAIL", {
                    "status_code": response.status_code,
                    "response": response.json()
                })
                
        except Exception as e:
            self.log_test("Supplier Creates Brand", "FAIL", error=e)
            
    def test_supplier_product_creation_and_approval(self):
        """Test supplier creates product and admin approves it"""
        print("\n💊 Testing Supplier Product Creation & Admin Approval Workflow...")
        
        supplier_headers = self.get_auth_headers(self.users['supplier'])
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        # Get existing approved category and brand for the product
        categories_response = self.client.get('/api/products/categories/', **admin_headers)
        brands_response = self.client.get('/api/products/brands/', **admin_headers)
        
        if categories_response.status_code == 200 and brands_response.status_code == 200:
            categories = categories_response.json().get('results', [])
            brands = brands_response.json().get('results', [])
            
            if categories and brands:
                # Use first available category and brand
                category_id = categories[0]['id']
                brand_id = brands[0]['id']
                
                # Step 1: Supplier creates product
                product_data = {
                    'name': f'Supplier Test Medicine {random.randint(1000, 9999)}',
                    'description': 'Test medicine created by supplier for approval workflow',
                    'brand': brand_id,
                    'category': category_id,
                    'product_type': 'medicine',
                    'price': '25.99',
                    'stock': 50,
                    'image': 'http://127.0.0.1:8000/media/images/medicine.png',
                    'medicine_details': {
                        'composition': 'Test composition',
                        'manufacturer': 'Test Pharma',
                        'prescription_required': False
                    }
                }
                
                try:
                    response = self.client.post('/api/products/products/', 
                                              data=json.dumps(product_data),
                                              content_type='application/json',
                                              **supplier_headers)
                    
                    if response.status_code == 201:
                        product_id = response.json()['id']
                        product_status = response.json().get('status', 'unknown')
                        is_published = response.json().get('is_publish', False)
                        
                        self.pending_entities['products'].append(product_id)
                        self.log_test("Supplier Creates Product", "PASS", {
                            "product_id": product_id,
                            "status": product_status,
                            "is_published": is_published,
                            "requires_approval": True
                        })
                        
                        # Step 2: Admin approves product
                        try:
                            approval_response = self.client.post(f'/api/products/admin/products/{product_id}/approve/', 
                                                               **admin_headers)
                            
                            if approval_response.status_code == 200:
                                self.log_test("Admin Approves Product", "PASS", {
                                    "product_id": product_id,
                                    "approval_response": approval_response.json()
                                })
                                
                                # Verify product is now published
                                verify_response = self.client.get(f'/api/products/products/{product_id}/', 
                                                                **admin_headers)
                                
                                if verify_response.status_code == 200:
                                    updated_product = verify_response.json()
                                    if updated_product.get('status') == 'approved' and updated_product.get('is_publish'):
                                        self.log_test("Product Approval Verification", "PASS", {
                                            "status": updated_product.get('status'),
                                            "is_published": updated_product.get('is_publish')
                                        })
                                    else:
                                        self.log_test("Product Approval Verification", "FAIL", {
                                            "status": updated_product.get('status'),
                                            "is_published": updated_product.get('is_publish')
                                        })
                                
                            else:
                                self.log_test("Admin Approves Product", "FAIL", {
                                    "status_code": approval_response.status_code,
                                    "response": approval_response.json() if approval_response.content else "No content"
                                })
                                
                        except Exception as e:
                            self.log_test("Admin Approves Product", "FAIL", error=e)
                            
                    else:
                        self.log_test("Supplier Creates Product", "FAIL", {
                            "status_code": response.status_code,
                            "response": response.json()
                        })
                        
                except Exception as e:
                    self.log_test("Supplier Creates Product", "FAIL", error=e)
                    
            else:
                self.log_test("Supplier Creates Product", "SKIP", {
                    "reason": "No approved categories or brands available"
                })
        else:
            self.log_test("Supplier Creates Product", "SKIP", {
                "reason": "Failed to fetch categories or brands"
            })
            
    def test_admin_rejection_workflow(self):
        """Test admin rejection workflow"""
        print("\n❌ Testing Admin Rejection Workflow...")
        
        supplier_headers = self.get_auth_headers(self.users['supplier'])
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        # Create a brand to reject
        brand_data = {
            'name': f'Brand To Reject {random.randint(1000, 9999)}',
            'image': 'http://127.0.0.1:8000/media/images/medical-pattern.svg'
        }
        
        try:
            response = self.client.post('/api/products/brands/', 
                                      data=json.dumps(brand_data),
                                      content_type='application/json',
                                      **supplier_headers)
            
            if response.status_code == 201:
                brand_id = response.json()['id']
                
                # Reject the brand
                rejection_data = {
                    'reason': 'Brand name not meeting quality standards'
                }
                
                rejection_response = self.client.post(f'/api/products/admin/brands/{brand_id}/reject/', 
                                                    data=json.dumps(rejection_data),
                                                    content_type='application/json',
                                                    **admin_headers)
                
                if rejection_response.status_code == 200:
                    self.log_test("Admin Rejects Brand", "PASS", {
                        "brand_id": brand_id,
                        "rejection_reason": rejection_data['reason']
                    })
                    
                    # Verify rejection
                    verify_response = self.client.get(f'/api/products/brands/{brand_id}/', 
                                                    **admin_headers)
                    
                    if verify_response.status_code == 200:
                        rejected_brand = verify_response.json()
                        if rejected_brand.get('status') == 'rejected':
                            self.log_test("Brand Rejection Verification", "PASS", {
                                "status": rejected_brand.get('status'),
                                "rejection_reason": rejected_brand.get('rejection_reason')
                            })
                        else:
                            self.log_test("Brand Rejection Verification", "FAIL", {
                                "expected_status": "rejected",
                                "actual_status": rejected_brand.get('status')
                            })
                else:
                    self.log_test("Admin Rejects Brand", "FAIL", {
                        "status_code": rejection_response.status_code,
                        "response": rejection_response.json() if rejection_response.content else "No content"
                    })
                    
        except Exception as e:
            self.log_test("Admin Rejection Workflow", "FAIL", error=e)
            
    def test_pending_approvals_endpoint(self):
        """Test the pending approvals endpoint"""
        print("\n📋 Testing Pending Approvals Endpoint...")
        
        admin_headers = self.get_auth_headers(self.users['admin'])
        
        try:
            response = self.client.get('/api/products/admin/pending-approvals/', **admin_headers)
            
            if response.status_code == 200:
                pending_data = response.json()
                pending_categories = pending_data.get('pending_categories', [])
                pending_brands = pending_data.get('pending_brands', [])
                pending_products = pending_data.get('pending_products', [])
                
                self.log_test("Pending Approvals Endpoint", "PASS", {
                    "pending_categories_count": len(pending_categories),
                    "pending_brands_count": len(pending_brands),
                    "pending_products_count": len(pending_products),
                    "total_pending": len(pending_categories) + len(pending_brands) + len(pending_products)
                })
            else:
                self.log_test("Pending Approvals Endpoint", "FAIL", {
                    "status_code": response.status_code,
                    "response": response.json() if response.content else "No content"
                })
                
        except Exception as e:
            self.log_test("Pending Approvals Endpoint", "FAIL", error=e)
            
    def generate_approval_workflow_summary(self):
        """Generate approval workflow summary"""
        total_tests = len(self.test_results['tests'])
        passed_tests = len([t for t in self.test_results['tests'] if t['status'] == 'PASS'])
        failed_tests = len([t for t in self.test_results['tests'] if t['status'] == 'FAIL'])
        skipped_tests = len([t for t in self.test_results['tests'] if t['status'] == 'SKIP'])
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': skipped_tests,
            'success_rate': f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            'pending_entities_created': {
                'categories': len(self.pending_entities['categories']),
                'brands': len(self.pending_entities['brands']),
                'products': len(self.pending_entities['products'])
            }
        }
        
        # Save results
        with open('admin_approval_workflow_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📊 ADMIN APPROVAL WORKFLOW TEST SUMMARY")
        print(f"=" * 55)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"📈 Success Rate: {self.test_results['summary']['success_rate']}")
        print(f"\n📦 Pending Entities Created:")
        for entity_type, count in self.test_results['summary']['pending_entities_created'].items():
            print(f"  {entity_type.title()}: {count}")
        print(f"\n📄 Detailed results saved to: admin_approval_workflow_test_results.json")
        
    def run_approval_workflow_tests(self):
        """Run all approval workflow tests"""
        print("🔐 Starting Admin Approval Workflow Test Suite")
        print("=" * 55)
        
        try:
            self.setup_test_users()
            self.test_supplier_category_creation_and_approval()
            self.test_supplier_brand_creation_and_approval()
            self.test_supplier_product_creation_and_approval()
            self.test_admin_rejection_workflow()
            self.test_pending_approvals_endpoint()
            self.generate_approval_workflow_summary()
            
        except Exception as e:
            print(f"❌ Critical error in approval workflow tests: {e}")
            self.log_test("Approval Workflow Test Suite", "FAIL", error=e)


if __name__ == '__main__':
    test_suite = AdminApprovalWorkflowTest()
    test_suite.run_approval_workflow_tests()