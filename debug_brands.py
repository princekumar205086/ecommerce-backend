#!/usr/bin/env python
"""
Debug script to test brand API endpoint and check query behavior
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Brand
from products.serializers import BrandSerializer

# Test the query that the public view uses
print("=== Brand Query Debug ===")
print(f"Total brands in database: {Brand.objects.count()}")

public_query = Brand.objects.filter(status__in=['approved', 'published'], is_publish=True)
print(f"Brands matching public query: {public_query.count()}")

print("\nBrand status breakdown:")
for status, is_publish in [('approved', True), ('published', True), ('pending', False), ('rejected', False)]:
    count = Brand.objects.filter(status=status, is_publish=is_publish).count()
    print(f"  {status} + is_publish={is_publish}: {count}")

print("\nFirst 5 matching brands:")
for brand in public_query[:5]:
    print(f"  - {brand.name} (status: {brand.status}, published: {brand.is_publish})")

print("\nTesting serializer:")
try:
    serializer = BrandSerializer(public_query, many=True)
    data = serializer.data
    print(f"Serializer returned {len(data)} items")
    if data:
        print(f"Sample serialized brand: {data[0]}")
except Exception as e:
    print(f"Serializer error: {e}")