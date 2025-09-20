#!/usr/bin/env python3
"""
Script to approve all pending variants and create test data for comprehensive testing
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant, ProductImage, ProductReview, ProductAttribute, ProductAttributeValue
from django.utils import timezone
import random

User = get_user_model()

def approve_all_variants():
    """Approve all pending variants"""
    print("=== APPROVING ALL PENDING VARIANTS ===\n")
    
    # Get admin user for approval
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        print("❌ No admin user found. Creating one...")
        admin_user = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            full_name='Admin User',
            contact='1234567890',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        print("✅ Admin user created")
    
    # Approve all pending variants
    pending_variants = ProductVariant.objects.filter(status='pending')
    print(f"Found {pending_variants.count()} pending variants")
    
    for variant in pending_variants:
        variant.approve(admin_user)
    
    print(f"✅ Approved {pending_variants.count()} variants")

def create_sample_attributes_and_variants():
    """Create sample attributes and variants for testing"""
    print("\n=== CREATING SAMPLE ATTRIBUTES AND VARIANTS ===\n")
    
    # Create attributes if they don't exist
    attributes_data = [
        ('Size', ['Small', 'Medium', 'Large', 'XL']),
        ('Color', ['Red', 'Blue', 'Green', 'Black', 'White']),
        ('Dosage', ['5mg', '10mg', '20mg', '50mg']),
        ('Pack Size', ['10 tablets', '30 tablets', '60 tablets']),
    ]
    
    created_attrs = {}
    for attr_name, values in attributes_data:
        attr, created = ProductAttribute.objects.get_or_create(name=attr_name)
        created_attrs[attr_name] = attr
        
        for value in values:
            ProductAttributeValue.objects.get_or_create(
                attribute=attr,
                value=value
            )
    
    print("✅ Attributes created")
    
    # Get some published products
    products = Product.objects.filter(status='published', is_publish=True)[:10]
    
    for product in products:
        # Create 2-3 variants per product with attributes
        existing_variants = product.variants.count()
        
        if existing_variants < 3:
            needed_variants = 3 - existing_variants
            
            for i in range(needed_variants):
                # Create variant with attributes
                variant = ProductVariant.objects.create(
                    product=product,
                    price=Decimal(str(random.randint(100, 1000))),
                    additional_price=Decimal(str(random.randint(0, 100))),
                    stock=random.randint(10, 100),
                    status='approved',  # Create as approved
                    is_active=True
                )
                
                # Add random attributes
                if product.product_type == 'medicine':
                    # Add dosage and pack size
                    dosage_values = ProductAttributeValue.objects.filter(
                        attribute=created_attrs['Dosage']
                    )
                    pack_values = ProductAttributeValue.objects.filter(
                        attribute=created_attrs['Pack Size']
                    )
                    
                    if dosage_values.exists():
                        variant.attributes.add(random.choice(dosage_values))
                    if pack_values.exists():
                        variant.attributes.add(random.choice(pack_values))
                
                elif product.product_type == 'equipment':
                    # Add size and color
                    size_values = ProductAttributeValue.objects.filter(
                        attribute=created_attrs['Size']
                    )
                    color_values = ProductAttributeValue.objects.filter(
                        attribute=created_attrs['Color']
                    )
                    
                    if size_values.exists():
                        variant.attributes.add(random.choice(size_values))
                    if color_values.exists():
                        variant.attributes.add(random.choice(color_values))
                
                print(f"✅ Created variant for {product.name}")

def create_sample_images():
    """Create sample images for products"""
    print("\n=== CREATING SAMPLE PRODUCT IMAGES ===\n")
    
    products = Product.objects.filter(status='published', is_publish=True)[:10]
    
    for product in products:
        # Create 2-3 images per product
        for i in range(random.randint(2, 4)):
            ProductImage.objects.get_or_create(
                product=product,
                image=f"https://picsum.photos/400/400?random={product.id}{i}",
                alt_text=f"{product.name} - Image {i+1}",
                order=i
            )
        
        # Also create variant-specific images
        for variant in product.variants.all()[:2]:  # First 2 variants
            ProductImage.objects.get_or_create(
                product=product,
                variant=variant,
                image=f"https://picsum.photos/400/400?random={product.id}{variant.id}",
                alt_text=f"{product.name} - Variant {variant.id}",
                order=0
            )
        
        print(f"✅ Created images for {product.name}")

def create_sample_reviews():
    """Create sample reviews for products"""
    print("\n=== CREATING SAMPLE PRODUCT REVIEWS ===\n")
    
    # Get some users for reviews
    users = User.objects.filter(role='buyer')[:5]
    if not users.exists():
        print("❌ No buyer users found. Creating test users...")
        for i in range(5):
            User.objects.create_user(
                email=f'buyer{i}@test.com',
                password='test123',
                full_name=f'Buyer{i} User',
                contact=f'98765432{i}0',
                role='buyer'
            )
        users = User.objects.filter(role='buyer')[:5]
    
    products = Product.objects.filter(status='published', is_publish=True)[:10]
    
    review_comments = [
        "Great product! Very satisfied with the quality.",
        "Good value for money. Fast delivery.",
        "Average product. Could be better.",
        "Excellent quality and packaging.",
        "Not bad, but expected better quality.",
        "Amazing product! Highly recommended.",
        "Good product but delivery was slow.",
        "Perfect for my needs. Will buy again.",
    ]
    
    for product in products:
        # Create 2-5 reviews per product
        for i in range(random.randint(2, 5)):
            if users.exists():
                user = random.choice(users)
                rating = random.randint(3, 5)  # Mostly positive reviews
                
                ProductReview.objects.get_or_create(
                    product=product,
                    user=user,
                    defaults={
                        'rating': rating,
                        'comment': random.choice(review_comments),
                        'is_published': True
                    }
                )
        
        print(f"✅ Created reviews for {product.name}")

def test_api_response():
    """Test the API response to see if variants show up"""
    print("\n=== TESTING API RESPONSE ===\n")
    
    # Get a product with variants
    product_with_variants = Product.objects.filter(
        status='published',
        is_publish=True,
        variants__isnull=False
    ).first()
    
    if product_with_variants:
        print(f"Testing product: {product_with_variants.name} (ID: {product_with_variants.id})")
        
        # Count variants
        total_variants = product_with_variants.variants.count()
        approved_variants = product_with_variants.variants.filter(
            status__in=['approved', 'published'],
            is_active=True
        ).count()
        
        print(f"Total variants: {total_variants}")
        print(f"Approved variants: {approved_variants}")
        
        # Count images
        total_images = product_with_variants.images.count()
        variant_images = product_with_variants.images.filter(variant__isnull=False).count()
        
        print(f"Total images: {total_images}")
        print(f"Variant-specific images: {variant_images}")
        
        # Count reviews
        total_reviews = product_with_variants.reviews.count()
        published_reviews = product_with_variants.reviews.filter(is_published=True).count()
        
        print(f"Total reviews: {total_reviews}")
        print(f"Published reviews: {published_reviews}")
        
        print(f"\n🧪 Test this product with: https://backend.okpuja.in/api/public/products/products/{product_with_variants.id}/")
        
        return product_with_variants.id
    else:
        print("❌ No products with variants found")
        return None

if __name__ == "__main__":
    print("🚀 Starting comprehensive variant fix and test data creation...\n")
    
    # Step 1: Approve all pending variants
    approve_all_variants()
    
    # Step 2: Create sample attributes and variants
    create_sample_attributes_and_variants()
    
    # Step 3: Create sample images
    create_sample_images()
    
    # Step 4: Create sample reviews
    create_sample_reviews()
    
    # Step 5: Test API response
    test_product_id = test_api_response()
    
    print(f"\n✅ COMPLETED! All variants have been approved and test data created.")
    print(f"🧪 You can now test the API with a product that has variants, images, and reviews!")
    
    if test_product_id:
        print(f"\n🌐 Test URLs:")
        print(f"   Production: https://backend.okpuja.in/api/public/products/products/{test_product_id}/")
        print(f"   Local: http://localhost:8000/api/public/products/products/{test_product_id}/")