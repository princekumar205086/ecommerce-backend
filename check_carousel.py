#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from cms.models import CarouselBanner

# Get the most recently created carousel
carousel = CarouselBanner.objects.last()
if carousel:
    print(f"ID: {carousel.id}")
    print(f"Title: {carousel.title}")
    print(f"Image: {carousel.image}")
    print(f"Image length: {len(carousel.image) if carousel.image else 0}")
    print(f"Is Active: {carousel.is_active}")
    print(f"Created: {carousel.created_at}")
    
    # Show image field info
    print(f"\nImage field info:")
    print(f"  Type: {type(carousel.image)}")
    print(f"  Value: '{carousel.image}'")
else:
    print("No carousels found")
