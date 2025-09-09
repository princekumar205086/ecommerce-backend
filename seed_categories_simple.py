#!/usr/bin/env python3
"""
Simple Category Seeder Script
Run this script from the Django project root directory
"""

import os
import sys
import django
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.conf import settings
from products.models import ProductCategory

User = get_user_model()


def process_image_path(icon_file, is_parent_category):
    """Process the image path to use correct directory structure for ImageKit paths"""
    
    # For child categories, always use default path
    if not is_parent_category:
        return '/categories/default.png'
    
    # For parent categories, process the icon_file
    if not icon_file:
        return '/categories/default.png'

    # Extract filename from icon_file path
    filename = extract_filename(icon_file)
    
    # Return path that matches your ImageKit structure
    return f'/categories/{filename}'


def extract_filename(icon_file):
    """Extract filename from various path formats"""
    if not icon_file:
        return 'default.png'
        
    # Clean the path - remove leading slash if present
    clean_path = icon_file.lstrip('/')
    
    # Extract just the filename
    if '/' in clean_path:
        filename = clean_path.split('/')[-1]
    else:
        filename = clean_path
        
    return filename


def create_category(category_data, admin_user, parent_category=None):
    """Create a single category from the data"""
    try:
        # Check if category already exists
        existing_category = ProductCategory.objects.filter(
            name=category_data['name']
        ).first()
        
        if existing_category:
            print(f'⚠️  Category "{category_data["name"]}" already exists, skipping...')
            return existing_category

        # Process icon/image path
        icon_url = process_image_path(category_data.get('icon_file', ''), parent_category is None)

        # Create the category
        category = ProductCategory.objects.create(
            name=category_data['name'],
            icon=icon_url,
            parent=parent_category,
            created_by=admin_user,
            is_publish=category_data.get('is_publish', True),
            status=category_data.get('status', 'pending')
        )

        return category

    except Exception as e:
        print(f'❌ Error creating category "{category_data["name"]}": {str(e)}')
        return None


def main():
    print("🏪 Category Seeder Script")
    print("=" * 50)
    
    # Get admin user
    admin_email = 'admin@example.com'  # Use existing admin user
    try:
        admin_user = User.objects.get(email=admin_email)
        print(f'✅ Found admin user: {admin_user.email}')
    except User.DoesNotExist:
        print(f'❌ Admin user with email {admin_email} not found.')
        print('Please create an admin user first or update the admin_email in the script.')
        return

    # Load category data
    json_file_path = project_root / 'products' / 'data' / 'category.json'
    
    if not json_file_path.exists():
        print(f'❌ Category JSON file not found at: {json_file_path}')
        return

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
    except Exception as e:
        print(f'❌ Error reading JSON file: {str(e)}')
        return

    print(f'📁 Found {len(categories_data)} categories to process...')

    # Track created categories to handle parent relationships
    created_categories = {}
    parent_categories = []
    child_categories = []

    # Separate parent and child categories
    for category_data in categories_data:
        if category_data.get('parent') is None:
            parent_categories.append(category_data)
        else:
            child_categories.append(category_data)

    # Create parent categories first
    print('\n📋 Creating parent categories...')
    for category_data in parent_categories:
        category = create_category(category_data, admin_user, None)
        if category:
            created_categories[category_data['id']] = category
            print(f'✅ Created parent category: {category.name}')

    # Create child categories
    print('\n📂 Creating child categories...')
    for category_data in child_categories:
        parent_id = category_data.get('parent')
        parent_category = created_categories.get(parent_id)
        
        if not parent_category:
            print(f'⚠️  Parent category with ID {parent_id} not found for {category_data["name"]}')
            continue

        category = create_category(category_data, admin_user, parent_category)
        if category:
            created_categories[category_data['id']] = category
            print(f'✅ Created child category: {category.name} (parent: {parent_category.name})')

    print(f'\n🎉 Successfully created {len(created_categories)} categories!')

    # Summary
    total_parent = len(parent_categories)
    total_child = len(child_categories)
    print(f'\n📊 Summary:')
    print(f'   - Parent categories: {total_parent}')
    print(f'   - Child categories: {total_child}')
    print(f'   - Total categories: {len(created_categories)}')
    
    print(f'\n📝 Notes:')
    print(f'   - Parent categories use their specified images from media/categories/')
    print(f'   - Child categories use default.png (update manually later)')
    print(f'   - All image paths are configured for media/categories/ directory')


if __name__ == '__main__':
    main()
