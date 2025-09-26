#!/usr/bin/env python
"""
Comprehensive API test to achieve 100% success
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
from products.models import Product, ProductCategory, Brand, ProductVariant, ProductReview

User = get_user_model()

class ComprehensiveAPITester:
    def __init__(self):
        self.admin_client = APIClient()
        self.supplier_client = APIClient()  
        self.customer_client = APIClient()
        self.setup_clients()
        self.results = {}
        
    def setup_clients(self):
        """Setup authenticated clients for different user roles"""
        # Admin
        admin_user = User.objects.filter(role='admin').first()
        if admin_user:
            token = str(RefreshToken.for_user(admin_user).access_token)
            self.admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            
        # Supplier
        supplier_user = User.objects.filter(role='supplier').first()
        if supplier_user:
            token = str(RefreshToken.for_user(supplier_user).access_token)
            self.supplier_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            self.supplier_user = supplier_user
            
        # Customer
        customer_user = User.objects.filter(role='user').first()
        if customer_user:
            token = str(RefreshToken.for_user(customer_user).access_token)
            self.customer_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            self.customer_user = customer_user
    
    def test_categories(self):
        """Test Categories CRUD operations"""
        print("🔥 Testing Categories...")
        operations = {}
        
        # GET list
        response = self.supplier_client.get('/api/products/categories/')
        operations['GET_LIST'] = response.status_code == 200
        
        # POST (create)
        category_data = {
            'name': f'Test Category {datetime.now().strftime("%Y%m%d%H%M%S")}',
            'description': 'Test category description'
        }
        response = self.supplier_client.post('/api/products/categories/', data=category_data)
        category_created = response.status_code == 201
        operations['POST'] = category_created
        
        if category_created:
            category_id = response.data['id']
            
            # GET detail
            response = self.supplier_client.get(f'/api/products/categories/{category_id}/')
            operations['GET_DETAIL'] = response.status_code == 200
            
            # PUT (update)
            update_data = {
                'name': f'Updated Category {datetime.now().strftime("%Y%m%d%H%M%S")}',
                'description': 'Updated description'
            }
            response = self.supplier_client.put(f'/api/products/categories/{category_id}/', data=update_data)
            operations['PUT'] = response.status_code == 200
            
            # PATCH (partial update)
            patch_data = {'description': 'Patched description'}
            response = self.supplier_client.patch(f'/api/products/categories/{category_id}/', data=patch_data)
            operations['PATCH'] = response.status_code == 200
            
            # DELETE
            response = self.supplier_client.delete(f'/api/products/categories/{category_id}/')
            operations['DELETE'] = response.status_code == 204
        
        self.results['categories'] = operations
        return operations
    
    def test_brands(self):
        """Test Brands CRUD operations"""
        print("🔥 Testing Brands...")
        operations = {}
        
        # GET list
        response = self.supplier_client.get('/api/products/brands/')
        operations['GET_LIST'] = response.status_code == 200
        
        # POST (create)
        brand_data = {
            'name': f'Test Brand {datetime.now().strftime("%Y%m%d%H%M%S")}',
            'description': 'Test brand description'
        }
        response = self.supplier_client.post('/api/products/brands/', data=brand_data)
        brand_created = response.status_code == 201
        operations['POST'] = brand_created
        
        if brand_created:
            brand_id = response.data['id']
            
            # GET detail
            response = self.supplier_client.get(f'/api/products/brands/{brand_id}/')
            operations['GET_DETAIL'] = response.status_code == 200
            
            # PUT (update)
            update_data = {
                'name': f'Updated Brand {datetime.now().strftime("%Y%m%d%H%M%S")}',
                'description': 'Updated description'
            }
            response = self.supplier_client.put(f'/api/products/brands/{brand_id}/', data=update_data)
            operations['PUT'] = response.status_code == 200
            
            # PATCH (partial update)
            patch_data = {'description': 'Patched description'}
            response = self.supplier_client.patch(f'/api/products/brands/{brand_id}/', data=patch_data)
            operations['PATCH'] = response.status_code == 200
            
            # DELETE
            response = self.supplier_client.delete(f'/api/products/brands/{brand_id}/')
            operations['DELETE'] = response.status_code == 204
        
        self.results['brands'] = operations
        return operations
    
    def test_products(self):
        """Test Products CRUD operations"""
        print("🔥 Testing Products...")
        operations = {}
        
        # GET list
        response = self.supplier_client.get('/api/products/products/')
        operations['GET_LIST'] = response.status_code == 200
        
        # Get category and brand for product creation
        category = ProductCategory.objects.first()
        brand = Brand.objects.first()
        
        if not category or not brand:
            print("Missing category or brand for product test")
            self.results['products'] = operations
            return operations
        
        # POST (create) - Medicine
        product_data = {
            'name': f'Test Medicine {datetime.now().strftime("%Y%m%d%H%M%S")}',
            'description': 'Test medicine description',
            'category': category.id,
            'brand': brand.id,
            'type': 'medicine',
            'base_price': '99.99'
        }
        
        response = self.supplier_client.post('/api/products/products/', data=product_data)
        product_created = response.status_code == 201
        operations['POST'] = product_created
        
        if product_created:
            product_id = response.data['id']
            
            # GET detail
            response = self.supplier_client.get(f'/api/products/products/{product_id}/')
            operations['GET_DETAIL'] = response.status_code == 200
            
            # PUT (update)
            update_data = {
                'name': f'Updated Product {datetime.now().strftime("%Y%m%d%H%M%S")}',
                'description': 'Updated description',
                'category': category.id,
                'brand': brand.id,
                'type': 'medicine',
                'base_price': '149.99'
            }
            response = self.supplier_client.put(f'/api/products/products/{product_id}/', data=update_data)
            operations['PUT'] = response.status_code == 200
            
            # PATCH (partial update)
            patch_data = {'description': 'Patched description'}
            response = self.supplier_client.patch(f'/api/products/products/{product_id}/', data=patch_data)
            operations['PATCH'] = response.status_code == 200
            
            # Store product for variant testing
            self.test_product_id = product_id
            
            # DELETE
            response = self.supplier_client.delete(f'/api/products/products/{product_id}/')
            operations['DELETE'] = response.status_code == 204
        
        self.results['products'] = operations
        return operations
    
    def test_variants(self):
        """Test Product Variants CRUD operations"""
        print("🔥 Testing Variants...")
        operations = {}
        
        # Get a supplier product
        supplier_product = Product.objects.filter(created_by=self.supplier_user).first()
        if not supplier_product:
            print("No supplier product found for variant testing")
            self.results['variants'] = operations
            return operations
        
        # GET list
        response = self.supplier_client.get('/api/products/variants/')
        operations['GET_LIST'] = response.status_code == 200
        
        # POST (create)
        variant_data = {
            'product': supplier_product.id,
            'price': '129.99',
            'additional_price': '15.00',
            'stock': 25
        }
        
        response = self.supplier_client.post('/api/products/variants/', data=variant_data)
        variant_created = response.status_code == 201
        operations['POST'] = variant_created
        
        if variant_created:
            variant_id = response.data['id']
            
            # GET detail
            response = self.supplier_client.get(f'/api/products/variants/{variant_id}/')
            operations['GET_DETAIL'] = response.status_code == 200
            
            # PUT (update)
            update_data = {
                'product': supplier_product.id,
                'price': '139.99',
                'additional_price': '20.00',
                'stock': 35,
                'is_active': True
            }
            response = self.supplier_client.put(f'/api/products/variants/{variant_id}/', data=update_data)
            operations['PUT'] = response.status_code == 200
            
            # PATCH (partial update)
            patch_data = {'stock': 40}
            response = self.supplier_client.patch(f'/api/products/variants/{variant_id}/', data=patch_data)
            operations['PATCH'] = response.status_code == 200
            
            # DELETE
            response = self.supplier_client.delete(f'/api/products/variants/{variant_id}/')
            operations['DELETE'] = response.status_code == 204
        
        self.results['variants'] = operations
        return operations
    
    def test_reviews(self):
        """Test Product Reviews CRUD operations"""
        print("🔥 Testing Reviews...")
        operations = {}
        
        # Get a published product
        published_product = Product.objects.filter(
            status__in=['approved', 'published'],
            is_publish=True
        ).first()
        
        if not published_product:
            print("No published product found for review testing")
            self.results['reviews'] = operations
            return operations
        
        # GET list
        response = self.customer_client.get('/api/products/reviews/')
        operations['GET_LIST'] = response.status_code == 200
        
        # Check if user already has a review for this product
        existing_review = ProductReview.objects.filter(
            product=published_product,
            user=self.customer_user
        ).first()
        
        if existing_review:
            # Delete existing review to test creation
            existing_review.delete()
        
        # POST (create)
        review_data = {
            'product': published_product.id,
            'rating': 5,
            'comment': f'Excellent product! Review at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        }
        
        response = self.customer_client.post('/api/products/reviews/', data=review_data)
        review_created = response.status_code == 201
        operations['POST'] = review_created
        
        if review_created:
            review_id = response.data['id']
            
            # GET detail
            response = self.customer_client.get(f'/api/products/reviews/{review_id}/')
            operations['GET_DETAIL'] = response.status_code == 200
            
            # PUT (update)
            update_data = {
                'product': published_product.id,
                'rating': 4,
                'comment': f'Updated review at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            response = self.customer_client.put(f'/api/products/reviews/{review_id}/', data=update_data)
            operations['PUT'] = response.status_code == 200
            
            # PATCH (partial update)
            patch_data = {'rating': 3}
            response = self.customer_client.patch(f'/api/products/reviews/{review_id}/', data=patch_data)
            operations['PATCH'] = response.status_code == 200
            
            # DELETE
            response = self.customer_client.delete(f'/api/products/reviews/{review_id}/')
            operations['DELETE'] = response.status_code == 204
        
        self.results['reviews'] = operations
        return operations
    
    def calculate_success_rate(self, operations):
        """Calculate success rate for operations"""
        if not operations:
            return 0.0
        total = len(operations)
        successful = sum(1 for success in operations.values() if success)
        return (successful / total) * 100
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 RUNNING COMPREHENSIVE API TESTS FOR 100% SUCCESS")
        print("=" * 70)
        
        # Run all tests
        category_ops = self.test_categories()
        brand_ops = self.test_brands()
        product_ops = self.test_products()
        variant_ops = self.test_variants()
        review_ops = self.test_reviews()
        
        # Calculate success rates
        category_rate = self.calculate_success_rate(category_ops)
        brand_rate = self.calculate_success_rate(brand_ops)
        product_rate = self.calculate_success_rate(product_ops)
        variant_rate = self.calculate_success_rate(variant_ops)
        review_rate = self.calculate_success_rate(review_ops)
        
        # Overall success rate
        all_operations = []
        for ops in [category_ops, brand_ops, product_ops, variant_ops, review_ops]:
            all_operations.extend(ops.values())
        
        overall_rate = (sum(1 for success in all_operations if success) / len(all_operations)) * 100 if all_operations else 0
        
        # Print results
        print("\n📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 50)
        print(f"Categories: {category_rate:.1f}% ({sum(category_ops.values())}/{len(category_ops)})")
        print(f"Brands: {brand_rate:.1f}% ({sum(brand_ops.values())}/{len(brand_ops)})")
        print(f"Products: {product_rate:.1f}% ({sum(product_ops.values())}/{len(product_ops)})")
        print(f"Variants: {variant_rate:.1f}% ({sum(variant_ops.values())}/{len(variant_ops)})")
        print(f"Reviews: {review_rate:.1f}% ({sum(review_ops.values())}/{len(review_ops)})")
        print("=" * 50)
        print(f"🎯 OVERALL SUCCESS RATE: {overall_rate:.1f}%")
        
        if overall_rate == 100.0:
            print("\n🎉 CONGRATULATIONS! 100% SUCCESS ACHIEVED! 🎉")
        else:
            print(f"\n⚠️  {100 - overall_rate:.1f}% remaining to achieve 100% success")
            
            # Show failed operations
            print("\n❌ Failed Operations:")
            for entity, ops in [('Categories', category_ops), ('Brands', brand_ops), 
                               ('Products', product_ops), ('Variants', variant_ops), 
                               ('Reviews', review_ops)]:
                failed = [op for op, success in ops.items() if not success]
                if failed:
                    print(f"  {entity}: {', '.join(failed)}")
        
        return overall_rate

if __name__ == '__main__':
    tester = ComprehensiveAPITester()
    success_rate = tester.run_all_tests()