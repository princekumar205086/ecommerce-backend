#!/usr/bin/env python
"""
Test pagination issue in public endpoints
"""
import os
import sys

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from rest_framework.test import APIClient
from products.models import Brand, ProductCategory

def test_pagination_issue():
    """Test pagination behavior in public endpoints"""
    print("🔍 TESTING PAGINATION ISSUE")
    print("=" * 50)
    
    client = APIClient()
    
    # Count actual data in database
    total_published_brands = Brand.objects.filter(
        status__in=['approved', 'published'], 
        is_publish=True
    ).count()
    
    total_published_categories = ProductCategory.objects.filter(
        status='published', 
        is_publish=True
    ).count()
    
    print(f"Database counts:")
    print(f"  Published brands: {total_published_brands}")
    print(f"  Published categories: {total_published_categories}")
    print()
    
    # Test public brand endpoint without page parameter
    print("Testing /api/public/products/brands/ (no page param):")
    response = client.get('/api/public/products/brands/')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Count: {response.data['count']}")
        print(f"  Results length: {len(response.data['results'])}")
        print(f"  Expected: All {total_published_brands} brands")
        print(f"  Issue: {'✅ Fixed' if len(response.data['results']) == total_published_brands else '❌ Still paginated'}")
    print()
    
    # Test public brand endpoint with page parameter
    print("Testing /api/public/products/brands/?page=1:")
    response = client.get('/api/public/products/brands/?page=1')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Count: {response.data['count']}")
        print(f"  Results length: {len(response.data['results'])}")
        print(f"  Has next: {response.data.get('next') is not None}")
    print()
    
    # Test public categories endpoint
    print("Testing /api/public/products/categories/ (no page param):")
    response = client.get('/api/public/products/categories/')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Count: {response.data['count']}")
        print(f"  Results length: {len(response.data['results'])}")
        print(f"  Expected: All {total_published_categories} categories")
        print(f"  Issue: {'✅ Fixed' if len(response.data['results']) == total_published_categories else '❌ Still paginated'}")
    print()
    
    # Test with search parameter (should still work)
    print("Testing /api/public/products/brands/?search=Test:")
    response = client.get('/api/public/products/brands/?search=Test')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Count: {response.data['count']}")
        print(f"  Results length: {len(response.data['results'])}")
        print(f"  Search working: {'✅ Yes' if response.status_code == 200 else '❌ No'}")

if __name__ == '__main__':
    test_pagination_issue()