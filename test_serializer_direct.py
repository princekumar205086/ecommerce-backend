#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

# Test the serializer directly
from cms.serializers import CarouselBannerSerializer
from PIL import Image
from io import BytesIO
import json

print("Testing CarouselBannerSerializer Directly")
print("=" * 80)

# Create a test image file-like object
image = Image.new('RGB', (50, 50), color='green')
img_bytes = BytesIO()
image.save(img_bytes, format='JPEG')
img_bytes.seek(0)

# Create a file-like object
class SimpleUploadedFile:
    def __init__(self, name, content):
        self.name = name
        self.content = content
        self.size = len(content)
        self._pos = 0
    
    def read(self, size=None):
        if size is None:
            result = self.content[self._pos:]
            self._pos = len(self.content)
        else:
            result = self.content[self._pos:self._pos + size]
            self._pos += len(result)
        return result
    
    def seek(self, pos):
        self._pos = pos

img_file = SimpleUploadedFile('test.jpg', img_bytes.getvalue())

# Create serializer data
data = {
    'title': 'Direct Serializer Test',
    'caption': 'Testing',
    'is_active': True,
    'image_file': img_file
}

print("Creating carousel via serializer with image...")
serializer = CarouselBannerSerializer(data=data)

if serializer.is_valid():
    print("✅ Serializer validation passed")
    carousel = serializer.save()
    print(f"✅ Carousel created with ID: {carousel.id}")
    print(f"   Title: {carousel.title}")
    print(f"   Image: {carousel.image}")
    print(f"   Image length: {len(carousel.image) if carousel.image else 0}")
else:
    print("❌ Serializer validation failed")
    print(json.dumps(serializer.errors, indent=2))

# Also check upload function directly
print("\n" + "=" * 80)
print("Testing upload_to_imagekit Directly")
print("=" * 80)

from accounts.models import upload_to_imagekit

img_bytes.seek(0)
file_bytes = img_bytes.getvalue()

result = upload_to_imagekit(file_bytes, "direct_test.jpg", folder="carousel_banners")
print(f"Upload result: {result}")
print(f"Result type: {type(result)}")
print(f"Result is None: {result is None}")
print(f"Result bool: {bool(result)}")
