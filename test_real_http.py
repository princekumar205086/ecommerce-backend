#!/usr/bin/env python
"""Test ImageKit upload using actual HTTP request"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from PIL import Image
import requests
import json

# Get Django test server running
from django.test.utils import setup_test_environment, teardown_test_environment
from django.test import Client
from django.core.management import call_command

print("Testing ImageKit Upload with Real HTTP Request")
print("=" * 80)

# Create admin user
User = get_user_model()
admin_user, created = User.objects.get_or_create(
    email='admin_imagekit_test@example.com',
    defaults={
        'is_staff': True,
        'is_superuser': True,
        'is_active': True
    }
)

if created:
    admin_user.set_password('password123')
    admin_user.save()
    print(f"✅ Created admin user")
else:
    print(f"✅ Using existing admin user")

# Get token
refresh = RefreshToken.for_user(admin_user)
access_token = str(refresh.access_token)
print(f"✅ Got JWT token")

# Create test image
image = Image.new('RGB', (100, 100), color='purple')
image.save('test_real.jpg')

# Post using Django test client with proper method
client = Client()

with open('test_real.jpg', 'rb') as img_file:
    data = {
        'title': 'Real HTTP Test',
        'caption': 'Testing with real data',
        'order': '2',
        'is_active': 'true'
    }
    
    print(f"\n🧪 Posting to /api/cms/admin/carousels/")
    print(f"   Headers: Authorization: Bearer {access_token[:20]}...")
    print(f"   Data: {data}")
    print(f"   File: test_real.jpg")
    
    response = client.post(
        '/api/cms/admin/carousels/',
        data=data,
        files={'image_file': img_file},
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        content_type='multipart/form-data'
    )

print(f"\n✅ Status: {response.status_code}")
response_data = response.json()
print(f"\nResponse:")
print(json.dumps(response_data, indent=2))

if response.status_code == 201:
    carousel_id = response_data.get('id')
    image_url = response_data.get('image')
    
    if image_url:
        print(f"\n✅ Image URL: {image_url}")
        print(f"   Accessible: {image_url.startswith('https://')}")
    else:
        print(f"\n❌ Image URL is empty")

os.remove('test_real.jpg')
