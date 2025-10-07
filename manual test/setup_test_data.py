#!/usr/bin/env python3
"""
Data Setup Script
Creates test data for comprehensive API testing
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import ProductCategory, Brand, Product
from cms.models import Page, Banner, BlogPost, BlogCategory, BlogTag, FAQ, Testimonial

User = get_user_model()

def create_test_data():
    print("🚀 Creating Test Data...")
    print("=" * 50)
    
    # Create admin user if not exists
    admin_user, created = User.objects.get_or_create(
        email='admin@example.com',
        defaults={
            'full_name': 'Admin User',
            'role': 'admin',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('adminpass123')
        admin_user.save()
        print("✅ Admin user created")
    else:
        print("✅ Admin user already exists")
    
    # Create categories
    categories_data = [
        {'name': 'Medicines', 'description': 'All types of medicines'},
        {'name': 'Medical Equipment', 'description': 'Doctor and medical equipment'},
        {'name': 'Pathology Products', 'description': 'Pathology and lab products'},
        {'name': 'Emergency Medicine', 'description': 'Emergency medical supplies'},
    ]
    
    created_categories = []
    for cat_data in categories_data:
        category, created = ProductCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'created_by': admin_user,
                'status': 'published',
                'is_publish': True
            }
        )
        if created:
            print(f"✅ Category created: {category.name}")
        else:
            # Update existing category to be published
            category.status = 'published'
            category.is_publish = True
            category.save()
            print(f"✅ Category updated: {category.name}")
        created_categories.append(category)
    
    # Create brands (brands don't have status/is_publish)
    brands_data = [
        {'name': 'MediCorp'},
        {'name': 'HealthTech'},
        {'name': 'PharmaPlus'},
        {'name': 'LabEquip'},
    ]
    
    created_brands = []
    for brand_data in brands_data:
        brand, created = Brand.objects.get_or_create(
            name=brand_data['name'],
            defaults={'created_by': admin_user}
        )
        if created:
            print(f"✅ Brand created: {brand.name}")
        else:
            print(f"✅ Brand already exists: {brand.name}")
        created_brands.append(brand)
    
    # Create products
    products_data = [
        {
            'name': 'Paracetamol 500mg',
            'description': 'Pain relief medication',
            'price': Decimal('25.00'),
            'stock': 100,
            'product_type': 'medicine',
            'category': created_categories[0],
            'brand': created_brands[0],
        },
        {
            'name': 'Digital Thermometer',
            'description': 'Accurate digital thermometer',
            'price': Decimal('150.00'),
            'stock': 50,
            'product_type': 'equipment',
            'category': created_categories[1],
            'brand': created_brands[1],
        },
        {
            'name': 'Blood Test Kit',
            'description': 'Complete blood test kit',
            'price': Decimal('200.00'),
            'stock': 25,
            'product_type': 'pathology',
            'category': created_categories[2],
            'brand': created_brands[2],
        },
        {
            'name': 'First Aid Kit',
            'description': 'Emergency first aid supplies',
            'price': Decimal('75.00'),
            'stock': 30,
            'product_type': 'medicine',
            'category': created_categories[3],
            'brand': created_brands[3],
        },
    ]
    
    for prod_data in products_data:
        product, created = Product.objects.get_or_create(
            name=prod_data['name'],
            defaults={
                'description': prod_data['description'],
                'price': prod_data['price'],
                'stock': prod_data['stock'],
                'product_type': prod_data['product_type'],
                'category': prod_data['category'],
                'brand': prod_data['brand'],
                'created_by': admin_user,
                'status': 'published',
                'is_publish': True,
            }
        )
        if created:
            print(f"✅ Product created: {product.name}")
        else:
            # Update existing product to be published
            product.status = 'published'
            product.is_publish = True
            product.save()
            print(f"✅ Product updated: {product.name}")
    
    # Create CMS content
    # Pages
    pages_data = [
        {'title': 'About Us', 'content': 'About our medical ecommerce platform'},
        {'title': 'Privacy Policy', 'content': 'Our privacy policy'},
        {'title': 'Terms of Service', 'content': 'Terms and conditions'},
        {'title': 'Contact Us', 'content': 'Contact information'},
    ]
    
    for page_data in pages_data:
        page, created = Page.objects.get_or_create(
            title=page_data['title'],
            defaults={
                'content': page_data['content'],
                'status': 'published',
                'created_by': admin_user,
            }
        )
        if created:
            print(f"✅ Page created: {page.title}")
        else:
            print(f"✅ Page already exists: {page.title}")
    
    # Blog Categories
    blog_categories_data = [
        {'name': 'Health Tips'},
        {'name': 'Medical News'},
        {'name': 'Product Reviews'},
        {'name': 'Emergency Care'},
    ]
    
    created_blog_categories = []
    for cat_data in blog_categories_data:
        blog_cat, created = BlogCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': f"Articles about {cat_data['name'].lower()}"}
        )
        if created:
            print(f"✅ Blog category created: {blog_cat.name}")
        else:
            print(f"✅ Blog category already exists: {blog_cat.name}")
        created_blog_categories.append(blog_cat)
    
    # Blog Tags
    blog_tags_data = [
        {'name': 'Health'},
        {'name': 'Medicine'},
        {'name': 'Emergency'},
        {'name': 'Tips'},
    ]
    
    created_blog_tags = []
    for tag_data in blog_tags_data:
        blog_tag, created = BlogTag.objects.get_or_create(
            name=tag_data['name']
        )
        if created:
            print(f"✅ Blog tag created: {blog_tag.name}")
        else:
            print(f"✅ Blog tag already exists: {blog_tag.name}")
        created_blog_tags.append(blog_tag)
    
    # Blog Posts
    blog_posts_data = [
        {
            'title': '10 Essential Health Tips',
            'content': 'Important health tips for daily life',
            'excerpt': 'Learn about essential health practices',
        },
        {
            'title': 'Understanding Medical Equipment',
            'content': 'Guide to common medical equipment',
            'excerpt': 'Everything you need to know about medical equipment',
        },
    ]
    
    for post_data in blog_posts_data:
        blog_post, created = BlogPost.objects.get_or_create(
            title=post_data['title'],
            defaults={
                'content': post_data['content'],
                'excerpt': post_data['excerpt'],
                'status': 'published',
                'author': admin_user,
            }
        )
        if created:
            blog_post.categories.set(created_blog_categories[:2])
            blog_post.tags.set(created_blog_tags[:2])
            print(f"✅ Blog post created: {blog_post.title}")
        else:
            print(f"✅ Blog post already exists: {blog_post.title}")
    
    # FAQs
    faqs_data = [
        {
            'question': 'How do I place an order?',
            'answer': 'You can place an order by adding items to cart and checking out.',
            'category': 'ordering',
        },
        {
            'question': 'What payment methods do you accept?',
            'answer': 'We accept credit cards, debit cards, and digital wallets.',
            'category': 'payments',
        },
        {
            'question': 'Do you deliver medicines?',
            'answer': 'Yes, we deliver medicines with proper prescription.',
            'category': 'products',
        },
    ]
    
    for faq_data in faqs_data:
        faq, created = FAQ.objects.get_or_create(
            question=faq_data['question'],
            defaults={
                'answer': faq_data['answer'],
                'category': faq_data['category'],
                'is_active': True,
            }
        )
        if created:
            print(f"✅ FAQ created: {faq.question[:50]}...")
        else:
            print(f"✅ FAQ already exists: {faq.question[:50]}...")
    
    # Testimonials
    testimonials_data = [
        {
            'author_name': 'Dr. John Smith',
            'author_title': 'General Physician',
            'content': 'Excellent service and quality products.',
            'rating': 5,
            'is_featured': True,
        },
        {
            'author_name': 'Sarah Johnson',
            'author_title': 'Patient',
            'content': 'Fast delivery and authentic medicines.',
            'rating': 5,
            'is_featured': False,
        },
    ]
    
    for test_data in testimonials_data:
        testimonial, created = Testimonial.objects.get_or_create(
            author_name=test_data['author_name'],
            defaults={
                'author_title': test_data['author_title'],
                'content': test_data['content'],
                'rating': test_data['rating'],
                'is_featured': test_data['is_featured'],
                'is_active': True,
            }
        )
        if created:
            print(f"✅ Testimonial created: {testimonial.author_name}")
        else:
            print(f"✅ Testimonial already exists: {testimonial.author_name}")
    
    print("\n🎉 Test data creation completed!")
    print("=" * 50)
    print(f"📊 Summary:")
    print(f"   Categories: {ProductCategory.objects.filter(is_publish=True).count()}")
    print(f"   Brands: {Brand.objects.count()}")
    print(f"   Products: {Product.objects.filter(is_publish=True).count()}")
    print(f"   Pages: {Page.objects.filter(status='published').count()}")
    print(f"   Blog Categories: {BlogCategory.objects.count()}")
    print(f"   Blog Tags: {BlogTag.objects.count()}")
    print(f"   Blog Posts: {BlogPost.objects.filter(status='published').count()}")
    print(f"   FAQs: {FAQ.objects.filter(is_active=True).count()}")
    print(f"   Testimonials: {Testimonial.objects.filter(is_active=True).count()}")

if __name__ == "__main__":
    create_test_data()