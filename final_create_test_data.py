import os
import django
import random
import decimal
from django.utils.text import slugify

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductVariant, ProductCategory
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
    
    # Get or create an admin user for product creation
    admin_user, created = User.objects.get_or_create(
        email='admin@example.com',
        defaults={
            'password': 'adminpassword123',
            'role': 'admin',
            'full_name': 'Admin User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('adminpassword123')
        admin_user.save()
        print(f"Created admin user: {admin_user.email}")
    else:
        print(f"Admin user exists: {admin_user.email}")
    
    # Create a category if needed
    category, created = ProductCategory.objects.get_or_create(
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
        try:
            product = Product.objects.get(name=data['name'])
            print(f"Product exists: {product.name}")
        except Product.DoesNotExist:
            # Create new product
            product = Product.objects.create(
                name=data['name'],
                description=data['description'],
                price=data['price'],
                stock=data['stock'],
                slug=slugify(data['name']),
                created_by=admin_user  # Set the creator
            )
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
    
    print("Test data creation complete!")

if __name__ == "__main__":
    create_test_data()