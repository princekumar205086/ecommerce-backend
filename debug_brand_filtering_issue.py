#!/usr/bin/env python
"""
Diagnose Brand API filtering issue
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
from products.models import Brand
from django.db.models import Q

User = get_user_model()

def decode_jwt_token(token):
    """Decode JWT token to get user info"""
    import jwt
    from django.conf import settings
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return decoded
    except:
        return None

def analyze_brand_filtering():
    """Analyze brand filtering issue"""
    print("🔍 ANALYZING BRAND FILTERING ISSUE")
    print("=" * 60)
    
    # Get the JWT token from the curl request
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU5MzU0NzczLCJpYXQiOjE3NTkzNTM4NzMsImp0aSI6IjBiOTllNzZlM2M3YjQwYzc4ZDBmNjU5OTgyODhmZTA3IiwidXNlcl9pZCI6OH0.Li7nW4S3uOBITMWOO8BikgshZVM_-LOcMYJMm0a8OJg"
    
    # Decode token to get user info
    decoded_token = decode_jwt_token(jwt_token)
    if decoded_token:
        print(f"Token Info: {json.dumps(decoded_token, indent=2)}")
        user_id = decoded_token.get('user_id')
        
        # Get the actual user
        try:
            user = User.objects.get(id=user_id)
            print(f"User: {user.email} (ID: {user.id})")
            print(f"User Role: {user.role}")
            print(f"User Active: {user.is_active}")
            print()
        except User.DoesNotExist:
            print(f"❌ User with ID {user_id} does not exist")
            return
    else:
        print("❌ Could not decode JWT token")
        return
    
    # Analyze brand counts
    print("📊 BRAND ANALYSIS:")
    print("-" * 30)
    
    total_brands = Brand.objects.count()
    print(f"Total brands in database: {total_brands}")
    
    # Analyze brand statuses
    status_counts = {}
    for status_choice in ['pending', 'approved', 'published', 'rejected']:
        count = Brand.objects.filter(status=status_choice).count()
        status_counts[status_choice] = count
        print(f"Brands with status '{status_choice}': {count}")
    
    # Analyze publish status
    published_brands = Brand.objects.filter(is_publish=True).count()
    unpublished_brands = Brand.objects.filter(is_publish=False).count()
    print(f"Published brands (is_publish=True): {published_brands}")
    print(f"Unpublished brands (is_publish=False): {unpublished_brands}")
    print()
    
    # Test different queryset filters based on user role
    print("🔍 QUERYSET FILTERING ANALYSIS:")
    print("-" * 40)
    
    if user.role == 'admin':
        print("User is ADMIN - should see all brands")
        admin_queryset = Brand.objects.all()
        print(f"Admin queryset count: {admin_queryset.count()}")
        
    elif user.role == 'supplier':
        print("User is SUPPLIER - should see own brands + published brands")
        
        # Own brands
        own_brands = Brand.objects.filter(created_by=user)
        print(f"Own brands count: {own_brands.count()}")
        
        # Published brands from others
        published_brands_query = Brand.objects.filter(
            status__in=['approved', 'published'], 
            is_publish=True
        )
        print(f"Published brands (status in approved/published AND is_publish=True): {published_brands_query.count()}")
        
        # Combined supplier queryset
        supplier_queryset = Brand.objects.filter(
            Q(created_by=user) | Q(status__in=['approved', 'published'], is_publish=True)
        )
        print(f"Supplier combined queryset count: {supplier_queryset.count()}")
        
        # Debug the published brands filter
        print("\n🔍 DEBUGGING PUBLISHED BRANDS FILTER:")
        approved_brands = Brand.objects.filter(status='approved', is_publish=True)
        published_status_brands = Brand.objects.filter(status='published', is_publish=True)
        
        print(f"Brands with status='approved' AND is_publish=True: {approved_brands.count()}")
        print(f"Brands with status='published' AND is_publish=True: {published_status_brands.count()}")
        
        # Check what brands actually exist with these combinations
        print(f"\n📋 BRAND STATUS COMBINATIONS:")
        combinations = Brand.objects.values('status', 'is_publish').annotate(count=models.Count('id'))
        for combo in combinations:
            print(f"  Status: {combo['status']}, Is_publish: {combo['is_publish']}, Count: {combo['count']}")
    
    else:
        print(f"User role '{user.role}' - should see published brands only")
        customer_queryset = Brand.objects.filter(status__in=['approved', 'published'], is_publish=True)
        print(f"Customer queryset count: {customer_queryset.count()}")
    
    print()
    
    # Test the public endpoint logic
    print("🌐 PUBLIC ENDPOINT ANALYSIS:")
    print("-" * 30)
    public_queryset = Brand.objects.all()  # This is what public endpoint uses
    print(f"Public endpoint queryset count: {public_queryset.count()}")
    
    # Sample some brands to see their actual status
    print(f"\n📋 SAMPLE BRAND STATUS:")
    sample_brands = Brand.objects.all()[:10]
    for brand in sample_brands:
        print(f"  {brand.name}: status='{brand.status}', is_publish={brand.is_publish}, created_by={brand.created_by.role}")

def test_api_endpoints():
    """Test both API endpoints"""
    print("\n🚀 TESTING API ENDPOINTS:")
    print("-" * 40)
    
    client = APIClient()
    
    # Test authenticated endpoint
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU5MzU0NzczLCJpYXQiOjE3NTkzNTM4NzMsImp0aSI6IjBiOTllNzZlM2M3YjQwYzc4ZDBmNjU5OTgyODhmZTA3IiwidXNlcl9pZCI6OH0.Li7nW4S3uOBITMWOO8BikgshZVM_-LOcMYJMm0a8OJg"
    
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {jwt_token}')
    
    # Test private endpoint
    response = client.get('/api/products/brands/?page=1')
    print(f"Private endpoint (/api/products/brands/): {response.status_code}")
    if response.status_code == 200:
        print(f"  Results count: {response.data['count']}")
    else:
        print(f"  Error: {response.data if hasattr(response, 'data') else response.content}")
    
    # Test public endpoint  
    response = client.get('/api/public/products/brands/')
    print(f"Public endpoint (/api/public/products/brands/): {response.status_code}")
    if response.status_code == 200:
        print(f"  Results count: {response.data['count']}")
    else:
        print(f"  Error: {response.data if hasattr(response, 'data') else response.content}")

if __name__ == '__main__':
    from django.db import models
    analyze_brand_filtering()
    test_api_endpoints()