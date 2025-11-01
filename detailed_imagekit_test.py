#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.test import Client
from rest_framework_simplejwt.tokens import RefreshToken
from PIL import Image
from django.contrib.auth import get_user_model
import json

# Create admin user
User = get_user_model()
admin_user, _ = User.objects.get_or_create(
    email='admin_test@example.com',
    defaults={
        'is_staff': True,
        'is_superuser': True,
        'is_active': True
    }
)

if _ :
    admin_user.set_password('adminpass123')
    admin_user.save()

# Get JWT token
refresh = RefreshToken.for_user(admin_user)
access_token = str(refresh.access_token)

# Create test image
image = Image.new('RGB', (100, 100), color='blue')
image.save('test_upload.jpg')

print("Testing ImageKit Upload with Detailed Response")
print("=" * 80)

# Test upload
client = Client()
headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}

with open('test_upload.jpg', 'rb') as f:
    files = {'image_file': f}
    data = {
        'title': 'ImageKit Test Banner',
        'caption': 'Testing ImageKit',
        'is_active': 'true'
    }
    
    response = client.post(
        '/api/cms/admin/carousels/',
        data=data,
        files=files,
        **headers
    )

print(f"Status Code: {response.status_code}")
print(f"\nResponse:")

response_data = response.json()
print(json.dumps(response_data, indent=2))

# Save to file for inspection
with open('imagekit_upload_response.json', 'w') as f:
    json.dump(response_data, f, indent=2, default=str)

print("\nResponse saved to imagekit_upload_response.json")

# Check database
from cms.models import CarouselBanner
carousel = CarouselBanner.objects.get(id=response_data.get('id')) if response.status_code == 201 else None

if carousel:
    print(f"\nDatabase Record Created:")
    print(f"  ID: {carousel.id}")
    print(f"  Title: {carousel.title}")
    print(f"  Image: {carousel.image}")
    print(f"  Image length: {len(carousel.image) if carousel.image else 0}")

# Cleanup
os.remove('test_upload.jpg')
