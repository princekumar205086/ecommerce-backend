#!/usr/bin/env python
"""
Create admin user for testing
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import User

def create_admin_user():
    """Create admin user if doesn't exist"""
    admin_email = 'admin@example.com'
    admin_password = 'admin123'
    
    try:
        admin_user = User.objects.get(email=admin_email)
        print(f"✅ Admin user already exists: {admin_email}")
    except User.DoesNotExist:
        admin_user = User.objects.create_user(
            email=admin_email,
            password=admin_password,
            full_name='Test Admin',
            contact='9999999999'
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        print(f"✅ Created admin user: {admin_email}")
    
    print(f"✅ Admin credentials: {admin_email} / {admin_password}")
    print(f"✅ Is staff: {admin_user.is_staff}")
    print(f"✅ Is superuser: {admin_user.is_superuser}")

if __name__ == "__main__":
    create_admin_user()