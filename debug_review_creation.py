#!/usr/bin/env python
"""
Debug review creation issue specifically
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
from products.models import Product, ProductReview

User = get_user_model()

def debug_review_creation():
    """Debug review creation issue"""
    print("🔍 DEBUGGING REVIEW CREATION ISSUE")
    print("-" * 50)
    
    client = APIClient()
    customer_user = User.objects.filter(role='user').first()
    
    if not customer_user:
        print("❌ No customer user found")
        return
    
    # Authenticate
    token = str(RefreshToken.for_user(customer_user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    print(f"Customer user: {customer_user.email} (ID: {customer_user.id})")
    
    # Get a published product that user hasn't reviewed yet
    published_products = Product.objects.filter(
        status__in=['approved', 'published'],
        is_publish=True
    )
    
    print(f"Found {published_products.count()} published products")
    
    suitable_product = None
    for product in published_products:
        existing_review = ProductReview.objects.filter(
            product=product,
            user=customer_user
        ).first()
        
        if not existing_review:
            suitable_product = product
            break
    
    if not suitable_product:
        print("❌ No suitable product found (user has reviewed all published products)")
        # Let's clean up some reviews to make space
        old_reviews = ProductReview.objects.filter(user=customer_user)[:2]
        for review in old_reviews:
            print(f"Deleting old review {review.id}")
            review.delete()
        
        suitable_product = published_products.first()
    
    print(f"Using product: {suitable_product.id} - {suitable_product.name}")
    
    # Test review creation with detailed error handling
    review_data = {
        'product': suitable_product.id,
        'rating': 4,
        'comment': f'Test review created at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    }
    
    print(f"Review data: {json.dumps(review_data, indent=2)}")
    
    response = client.post('/api/products/reviews/', data=review_data, format='json')
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        print(f"✅ Successfully created review: {response.data}")
        return True
    else:
        print(f"❌ Failed to create review")
        if hasattr(response, 'data'):
            print(f"Error details: {json.dumps(response.data, indent=2)}")
        else:
            print(f"Response content: {response.content}")
        
        # Check existing reviews for this user/product combo
        existing = ProductReview.objects.filter(
            product=suitable_product,
            user=customer_user
        ).first()
        
        if existing:
            print(f"⚠️  User already has review {existing.id} for this product")
        
        return False

if __name__ == '__main__':
    debug_review_creation()