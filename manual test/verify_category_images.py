#!/usr/bin/env python3
"""
Category Image Verification Script
Tests all category images to ensure they are accessible and not broken
"""

import os
import sys
import django
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import ProductCategory


def test_image_url(category_id, category_name, image_url, is_parent):
    """Test if a single image URL is accessible"""
    try:
        if not image_url:
            return {
                'id': category_id,
                'name': category_name,
                'url': 'No URL',
                'status': 'NO_URL',
                'is_parent': is_parent,
                'error': 'No image URL provided'
            }
        
        # Make a HEAD request to check if image exists
        response = requests.head(image_url, timeout=10)
        
        status_code = response.status_code
        content_type = response.headers.get('content-type', '')
        content_length = response.headers.get('content-length', '0')
        
        if status_code == 200:
            if 'image' in content_type:
                return {
                    'id': category_id,
                    'name': category_name,
                    'url': image_url,
                    'status': 'OK',
                    'is_parent': is_parent,
                    'content_type': content_type,
                    'size': content_length
                }
            else:
                return {
                    'id': category_id,
                    'name': category_name,
                    'url': image_url,
                    'status': 'NOT_IMAGE',
                    'is_parent': is_parent,
                    'error': f'Content-Type: {content_type}'
                }
        else:
            return {
                'id': category_id,
                'name': category_name,
                'url': image_url,
                'status': 'HTTP_ERROR',
                'is_parent': is_parent,
                'error': f'HTTP {status_code}'
            }
            
    except Exception as e:
        return {
            'id': category_id,
            'name': category_name,
            'url': image_url,
            'status': 'ERROR',
            'is_parent': is_parent,
            'error': str(e)
        }


def main():
    print("🔍 Category Image Verification Test")
    print("=" * 60)
    
    # Get all categories
    categories = ProductCategory.objects.all().order_by('parent_id', 'name')
    
    if not categories.exists():
        print("❌ No categories found in database")
        return
    
    print(f"📊 Found {categories.count()} categories to test")
    
    # Prepare test data
    test_data = []
    for category in categories:
        test_data.append((
            category.id,
            category.name,
            category.icon,
            category.parent is None
        ))
    
    print("🚀 Testing image URLs (this may take a moment)...")
    
    # Test images concurrently for faster execution
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_category = {
            executor.submit(test_image_url, cat_id, name, url, is_parent): (cat_id, name)
            for cat_id, name, url, is_parent in test_data
        }
        
        for future in as_completed(future_to_category):
            result = future.result()
            results.append(result)
    
    # Sort results
    results.sort(key=lambda x: (not x['is_parent'], x['name']))
    
    # Analyze results
    total_categories = len(results)
    ok_images = len([r for r in results if r['status'] == 'OK'])
    broken_images = len([r for r in results if r['status'] != 'OK'])
    parent_ok = len([r for r in results if r['is_parent'] and r['status'] == 'OK'])
    child_ok = len([r for r in results if not r['is_parent'] and r['status'] == 'OK'])
    
    # Print summary
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"✅ Working images: {ok_images}/{total_categories}")
    print(f"❌ Broken images: {broken_images}/{total_categories}")
    print(f"🌟 Parent categories OK: {parent_ok}/7")
    print(f"👶 Child categories OK: {child_ok}/73")
    
    # Print detailed results
    print(f"\n📋 DETAILED RESULTS")
    print("=" * 60)
    
    # Parent categories first
    print("\n🌟 PARENT CATEGORIES:")
    parent_results = [r for r in results if r['is_parent']]
    for result in parent_results:
        status_icon = "✅" if result['status'] == 'OK' else "❌"
        print(f"{status_icon} {result['name']}")
        print(f"   URL: {result['url'][:80]}{'...' if len(result['url']) > 80 else ''}")
        if result['status'] == 'OK':
            print(f"   Type: {result['content_type']}, Size: {result['size']} bytes")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        print()
    
    # Child categories (only show broken ones to save space)
    print("\n👶 CHILD CATEGORIES:")
    child_results = [r for r in results if not r['is_parent']]
    broken_children = [r for r in child_results if r['status'] != 'OK']
    
    if broken_children:
        print(f"❌ Found {len(broken_children)} broken child category images:")
        for result in broken_children[:10]:  # Show first 10
            print(f"   • {result['name']}: {result.get('error', 'Unknown error')}")
        if len(broken_children) > 10:
            print(f"   ... and {len(broken_children) - 10} more")
    else:
        print("✅ All child category images are working!")
        # Show a few examples
        print("📸 Sample working child images:")
        for result in child_results[:5]:
            print(f"   ✅ {result['name']}")
    
    # Final assessment
    print(f"\n🎯 FINAL ASSESSMENT")
    print("=" * 60)
    
    if broken_images == 0:
        print("🎉 PERFECT! All category images are working correctly!")
        print("✅ Your ImageKit integration is working flawlessly")
        print("✅ All parent and child categories have accessible images")
    elif broken_images <= 5:
        print("👍 GOOD! Most images are working with only minor issues")
        print(f"🔧 Fix {broken_images} broken image(s) for perfect results")
    else:
        print("⚠️  NEEDS ATTENTION! Multiple broken images found")
        print("🔧 Check ImageKit configuration and image uploads")
    
    # Test specific URLs in browser
    if parent_ok > 0:
        working_parent = next(r for r in parent_results if r['status'] == 'OK')
        print(f"\n💡 Test this working parent image in browser:")
        print(f"   {working_parent['url']}")
    
    if child_ok > 0:
        working_child = next(r for r in child_results if r['status'] == 'OK')
        print(f"\n💡 Test this working child image in browser:")
        print(f"   {working_child['url']}")


if __name__ == '__main__':
    main()
