#!/usr/bin/env python
"""
Setup test data for payment verification
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import User
from products.models import Product, ProductCategory
from cart.models import Cart, CartItem

def setup_test_data():
    """Create test products and cart items"""
    
    # Get test user
    try:
        user = User.objects.get(email='user@example.com')
        print(f"✅ Found test user: {user.email}")
    except User.DoesNotExist:
        print("❌ Test user not found. Please run create_test_users.py first")
        return False
    
    # Get admin user for creating category and products
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        print("❌ Admin user not found. Cannot create test data.")
        return False
    
    # Create or get a test category
    category, created = ProductCategory.objects.get_or_create(
        name="Test Category",
        defaults={
            "slug": "test-category",
            "created_by": admin_user,
            "is_publish": True
        }
    )
    if created:
        print("✅ Created test category")
    else:
        print("ℹ️ Test category already exists")
    
    # Create test products
    products_data = [
        {
            "name": "Test Product 1",
            "description": "First test product for payment verification",
            "price": Decimal("299.99"),
            "stock": 100,
            "sku": "TEST001"
        },
        {
            "name": "Test Product 2", 
            "description": "Second test product for payment verification",
            "price": Decimal("699.99"),
            "stock": 50,
            "sku": "TEST002"
        }
    ]
    
    products = []
    for product_data in products_data:
        product, created = Product.objects.get_or_create(
            sku=product_data["sku"],
            defaults={
                **product_data,
                "category": category,
                "created_by": admin_user,
                "is_publish": True,
                "status": "published"
            }
        )
        products.append(product)
        if created:
            print(f"✅ Created product: {product.name}")
        else:
            print(f"ℹ️ Product already exists: {product.name}")
    
    # Create or get user's cart
    cart, created = Cart.objects.get_or_create(
        user=user,
        defaults={}
    )
    if created:
        print("✅ Created new cart for user")
    else:
        print("ℹ️ Using existing cart")
    
    # Add products to cart
    for i, product in enumerate(products):
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                "quantity": i + 1  # 1 for first product, 2 for second
            }
        )
        if created:
            print(f"✅ Added {cart_item.quantity}x {product.name} to cart")
        else:
            print(f"ℹ️ Cart item already exists: {product.name}")
    
    # Calculate cart total
    cart_total = sum(item.total_price for item in cart.items.all())
    print(f"🛒 Cart total: ₹{cart_total}")
    
    return True

if __name__ == "__main__":
    print("🛒 Setting up test data for payment verification...")
    if setup_test_data():
        print("✅ Test data setup complete!")
    else:
        print("❌ Test data setup failed!")