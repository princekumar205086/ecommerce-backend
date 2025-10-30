#!/usr/bin/env python
"""
Debug script to test the actual public brand view
"""
import os
import django
import sys

# Setup Django first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

# Setup Django
sys.path.insert(0, '.')

from products.public_views import PublicBrandListView

# Create a test request
factory = RequestFactory()
request = factory.get('/api/public/products/brands/')
request.user = AnonymousUser()

# Test the view
print("=== Testing PublicBrandListView ===")
view = PublicBrandListView()
view.setup(request)

try:
    # Get queryset
    queryset = view.get_queryset()
    print(f"View queryset count: {queryset.count()}")
    
    # Apply filters
    filtered_queryset = view.filter_queryset(queryset)
    print(f"Filtered queryset count: {filtered_queryset.count()}")
    
    # Test serialization
    serializer = view.get_serializer(filtered_queryset, many=True)
    data = serializer.data
    print(f"Serialized data count: {len(data)}")
    
    # Test the actual view response
    response = view.get(request)
    print(f"View response status: {response.status_code}")
    print(f"Response data keys: {list(response.data.keys())}")
    print(f"Response count: {response.data.get('count', 'N/A')}")
    print(f"Response results length: {len(response.data.get('results', []))}")
    
    if response.data.get('results'):
        print(f"First result: {response.data['results'][0]}")
    
except Exception as e:
    print(f"Error testing view: {e}")
    import traceback
    traceback.print_exc()