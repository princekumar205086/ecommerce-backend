import os
import django
import random
import decimal
from django.utils.text import slugify

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductVariant, Category
from accounts.models import User

def create_test_data():
    """Create test data for checkout flow testing"""
    print("Creating test data for checkout flow testing...")
    
    # Ensure we have a test user
    try:
        test_user = User.objects.get(email='testuser@example.com')
        print(f"Test user exists: {test_user.email}")
    except User.DoesNotExist:
        test_user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123',
            role='user',
            full_name='Test User'
        )
        print(f"Created test user: {test_user.email}")
    
    # Create a category if needed
    category, created = Category.objects.get_or_create(
        name='Test Category',
        defaults={
            'description': 'Test category for checkout flow testing',
            'slug': 'test-category'
        }
    )
    if created:
        print(f"Created category: {category.name}")
    else:
        print(f"Category exists: {category.name}")
    
    # Create test products with variants
    product_data = [
        {
            'name': 'Test Product 1',
            'description': 'A test product for checkout flow testing',
            'price': decimal.Decimal('199.99'),
            'stock': 100,
            'variants': [
                {'size': 'Small', 'additional_price': decimal.Decimal('0.00'), 'stock': 50},
                {'size': 'Medium', 'additional_price': decimal.Decimal('50.00'), 'stock': 30},
                {'size': 'Large', 'additional_price': decimal.Decimal('100.00'), 'stock': 20}
            ]
        },
        {
            'name': 'Test Product 2',
            'description': 'Another test product for checkout flow testing',
            'price': decimal.Decimal('299.99'),
            'stock': 50,
            'variants': [
                {'size': '100mg', 'additional_price': decimal.Decimal('0.00'), 'stock': 25},
                {'size': '200mg', 'additional_price': decimal.Decimal('75.00'), 'stock': 25}
            ]
        }
    ]
    
    for data in product_data:
        product, created = Product.objects.get_or_create(
            name=data['name'],
            defaults={
                'description': data['description'],
                'price': data['price'],
                'stock': data['stock'],
                'slug': slugify(data['name'])
            }
        )
        
        if created:
            print(f"Created product: {product.name}")
            # Add category
            product.categories.add(category)
            
            # Create variants
            for variant_data in data['variants']:
                variant = ProductVariant.objects.create(
                    product=product,
                    size=variant_data['size'],
                    additional_price=variant_data['additional_price'],
                    stock=variant_data['stock']
                )
                print(f"  - Added variant: {variant.size}")
        else:
            print(f"Product exists: {product.name}")
    
    print("Test data creation complete!")

if __name__ == "__main__":
    create_test_data()