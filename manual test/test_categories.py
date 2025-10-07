#!/usr/bin/env python3
"""
Test script to verify category seeder functionality
Run this before and after seeding to see the results
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import ProductCategory


def main():
    print("🔍 Category Database Status")
    print("=" * 50)
    
    # Count categories
    total_categories = ProductCategory.objects.count()
    parent_categories = ProductCategory.objects.filter(parent=None).count()
    child_categories = ProductCategory.objects.exclude(parent=None).count()
    
    print(f"📊 Current Statistics:")
    print(f"   - Total categories: {total_categories}")
    print(f"   - Parent categories: {parent_categories}")
    print(f"   - Child categories: {child_categories}")
    
    if total_categories == 0:
        print("\n❌ No categories found in database")
        print("💡 Run the seeder to populate categories:")
        print("   python manage.py seed_categories")
        print("   or")
        print("   python seed_categories_simple.py")
        return
    
    print(f"\n📋 Parent Categories:")
    parents = ProductCategory.objects.filter(parent=None).order_by('name')
    for parent in parents:
        child_count = parent.productcategory_set.count()
        print(f"   • {parent.name} ({child_count} subcategories)")
        print(f"     Image: {parent.icon or 'No image'}")
        print(f"     Status: {parent.status} | Published: {parent.is_publish}")
    
    print(f"\n📂 Sample Child Categories:")
    children = ProductCategory.objects.exclude(parent=None)[:10]
    for child in children:
        print(f"   • {child.name} (parent: {child.parent.name if child.parent else 'None'})")
        print(f"     Image: {child.icon or 'No image'}")
    
    if child_categories > 10:
        print(f"   ... and {child_categories - 10} more")
    
    print(f"\n🖼️  Image Path Analysis:")
    categories_with_images = ProductCategory.objects.exclude(icon__isnull=True).exclude(icon='').count()
    categories_without_images = total_categories - categories_with_images
    
    print(f"   - Categories with images: {categories_with_images}")
    print(f"   - Categories without images: {categories_without_images}")
    
    # Check image paths
    unique_image_paths = ProductCategory.objects.exclude(icon__isnull=True).exclude(icon='').values_list('icon', flat=True).distinct()
    print(f"   - Unique image paths: {len(unique_image_paths)}")
    
    for path in unique_image_paths:
        count = ProductCategory.objects.filter(icon=path).count()
        print(f"     '{path}' used by {count} categories")


if __name__ == '__main__':
    main()
