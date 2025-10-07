#!/usr/bin/env python3
"""
Create test users for system testing
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import User

def create_test_users():
    """Create test users for testing"""
    print("🔧 Creating test users...")
    
    # Create regular test user
    test_user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'customer',
            'medixmall_mode': False,
            'is_active': True
        }
    )
    
    if created:
        test_user.set_password('testpassword123')
        test_user.save()
        print("✅ Created test user: test@example.com / testpassword123")
    else:
        print("✅ Test user already exists: test@example.com")
    
    # Create admin test user
    admin_user, created = User.objects.get_or_create(
        email='admin@example.com',
        defaults={
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    
    if created:
        admin_user.set_password('adminpassword123')
        admin_user.save()
        print("✅ Created admin user: admin@example.com / adminpassword123")
    else:
        print("✅ Admin user already exists: admin@example.com")
    
    # Create supplier test user
    supplier_user, created = User.objects.get_or_create(
        email='supplier@example.com',
        defaults={
            'username': 'supplier',
            'first_name': 'Supplier',
            'last_name': 'User',
            'role': 'supplier',
            'is_active': True
        }
    )
    
    if created:
        supplier_user.set_password('supplierpassword123')
        supplier_user.save()
        print("✅ Created supplier user: supplier@example.com / supplierpassword123")
    else:
        print("✅ Supplier user already exists: supplier@example.com")
    
    print("\n📋 Test Users Created:")
    print("  Regular User: test@example.com / testpassword123")
    print("  Admin User: admin@example.com / adminpassword123")
    print("  Supplier User: supplier@example.com / supplierpassword123")

if __name__ == "__main__":
    create_test_users()