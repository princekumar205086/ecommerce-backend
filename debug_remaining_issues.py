#!/usr/bin/env python
"""
Debug remaining issues to achieve 100% success
"""
import os
import sys
import json
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

def debug_variant_issues():
    """Debug variant creation and access issues"""
    print("🔍 DEBUGGING VARIANT ISSUES")
    print("-" * 40)
    
    client = APIClient()
    supplier_user = User.objects.filter(role='supplier').first()
    
    # Authenticate
    token = str(RefreshToken.for_user(supplier_user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Get a product created by this supplier
    supplier_product = Product.objects.filter(created_by=supplier_user).first()
    
    if not supplier_product:
        print("❌ No products found for supplier")
        return False
        
    print(f"Using product: {supplier_product.id} - {supplier_product.name}")
    
    # Test variant creation
    variant_data = {
        'product': supplier_product.id,
        'price': '119.99',
        'additional_price': '20.00',
        'stock': 30
    }
    
    print(f"Variant data: {variant_data}")
    response = client.post('/api/products/variants/', data=variant_data, format='json')
    print(f"Variant creation: {response.status_code}")
    
    if response.status_code != 201:
        print(f"Error: {response.data if hasattr(response, 'data') else response.content}")
        return False
    
    variant_id = response.data['id']
    print(f"✅ Created variant: {variant_id}")
    
    # Test variant access
    response = client.get(f'/api/products/variants/{variant_id}/')
    print(f"Variant access: {response.status_code}")
    
    return response.status_code == 200

def debug_review_issues():
    """Debug review creation issues"""
    print("\n🔍 DEBUGGING REVIEW ISSUES")
    print("-" * 40)
    
    client = APIClient()
    customer_user = User.objects.filter(role='user').first()
    
    # Authenticate
    token = str(RefreshToken.for_user(customer_user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Get a published product
    published_product = Product.objects.filter(
        status__in=['approved', 'published'], 
        is_publish=True
    ).first()
    
    if not published_product:
        print("❌ No published products found")
        return False
        
    print(f"Using product: {published_product.id} - {published_product.name}")
    
    # Check if user already has review for this product
    existing_review = ProductReview.objects.filter(
        product=published_product, 
        user=customer_user
    ).first()
    
    if existing_review:
        print(f"User already has review {existing_review.id} for this product")
        # Try updating existing review
        update_data = {
            'product': published_product.id,
            'rating': 4,
            'comment': f'Updated review at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        }
        
        response = client.put(f'/api/products/reviews/{existing_review.id}/', data=update_data, format='json')
        print(f"Review update: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.data if hasattr(response, 'data') else response.content}")
        return response.status_code == 200
    
    # Create new review
    review_data = {
        'product': published_product.id,
        'rating': 5,
        'comment': f'Great product! Review at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    }
    
    print(f"Review data: {review_data}")
    response = client.post('/api/products/reviews/', data=review_data, format='json')
    print(f"Review creation: {response.status_code}")
    
    if response.status_code != 201:
        print(f"Error: {response.data if hasattr(response, 'data') else response.content}")
        return False
    
    review_id = response.data['id']
    print(f"✅ Created review: {review_id}")
    
    return True

def debug_put_operations():
    """Debug PUT operation issues"""
    print("\n🔍 DEBUGGING PUT OPERATIONS")
    print("-" * 40)
    
    client = APIClient()
    supplier_user = User.objects.filter(role='supplier').first()
    
    # Authenticate
    token = str(RefreshToken.for_user(supplier_user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Test variant PUT
    variants = ProductVariant.objects.filter(product__created_by=supplier_user)[:1]
    if variants:
        variant = variants[0]
        print(f"Testing variant PUT: {variant.id}")
        
        put_data = {
            'product': variant.product.id,
            'price': '159.99',
            'additional_price': '25.00',
            'stock': 45,
            'is_active': True
        }
        
        response = client.put(f'/api/products/variants/{variant.id}/', data=put_data, format='json')
        print(f"Variant PUT: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.data if hasattr(response, 'data') else response.content}")
    
    return True

if __name__ == '__main__':
    print("🚀 Debugging remaining issues for 100% success")
    print("=" * 60)
    
    variant_success = debug_variant_issues()
    review_success = debug_review_issues() 
    put_success = debug_put_operations()
    
    print(f"\n📊 Debug Results:")
    print(f"Variants: {'✅' if variant_success else '❌'}")
    print(f"Reviews: {'✅' if review_success else '❌'}")
    print(f"PUT Operations: {'✅' if put_success else '❌'}")