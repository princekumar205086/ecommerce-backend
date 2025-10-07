#!/usr/bin/env python3
"""
Create test users for testing product endpoints
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import User

def create_test_users():
    """Create test users with different roles"""
    
    # Admin user
    if not User.objects.filter(email='admin@example.com').exists():
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='Admin@123',
            full_name='Admin User',
            contact='1234567890'
        )
        admin.role = 'admin'
        admin.save()
        print("✅ Admin user created: admin@example.com / Admin@123")
    else:
        print("ℹ️ Admin user already exists")
    
    # Supplier user
    if not User.objects.filter(email='supplier@example.com').exists():
        supplier = User.objects.create_user(
            email='supplier@example.com',
            password='testpass123',
            full_name='Test Supplier',
            contact='9876543210'
        )
        supplier.role = 'supplier'
        supplier.save()
        print("✅ Supplier user created: supplier@example.com / testpass123")
    else:
        print("ℹ️ Supplier user already exists")
    
    # Regular user
    if not User.objects.filter(email='user@example.com').exists():
        user = User.objects.create_user(
            email='user@example.com',
            password='User@123',
            full_name='Test User',
            contact='5555555555'
        )
        user.role = 'user'
        user.save()
        print("✅ Regular user created: user@example.com / User@123")
    else:
        print("ℹ️ Regular user already exists")

if __name__ == '__main__':
    print("🚀 Creating test users...")
    create_test_users()
    print("✅ Test users setup complete!")