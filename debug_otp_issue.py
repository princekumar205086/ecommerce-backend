#!/usr/bin/env python3
"""
🔍 OTP Investigation Script
Debug exactly which OTP model is created and what fields exist
"""

import os
import sys
import django

# Setup Django
sys.path.append('/srv/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings
from accounts.models import User, OTP
from django.db import models

def check_otp_models():
    """Check all OTP-related models in the database"""
    print("🔍 Investigating OTP Models and Data")
    print("=" * 60)
    
    # Check User model fields
    print("👤 User model fields related to OTP:")
    user_fields = [f.name for f in User._meta.fields]
    otp_related_fields = [f for f in user_fields if 'otp' in f.lower() or 'verification' in f.lower()]
    print(f"📋 OTP-related User fields: {otp_related_fields}")
    
    # Check OTP model structure
    print("\n📋 OTP Model Structure:")
    otp_fields = [(f.name, f.__class__.__name__, f.help_text) for f in OTP._meta.fields]
    for field_name, field_type, help_text in otp_fields:
        print(f"  • {field_name}: {field_type} - {help_text}")
    
    # Check for any other OTP models
    print("\n🔍 Checking all models for OTP references:")
    from django.apps import apps
    all_models = apps.get_models()
    for model in all_models:
        model_name = model.__name__
        if 'otp' in model_name.lower() or 'verification' in model_name.lower():
            print(f"  • Found model: {model_name} in {model._meta.app_label}")
    
    return True

def check_recent_otp_data():
    """Check the most recent OTP data for the test email"""
    print("\n📧 Recent OTP Data for princekumar205086@gmail.com:")
    print("=" * 60)
    
    try:
        # Get user
        user = User.objects.get(email='princekumar205086@gmail.com')
        print(f"👤 User found: {user.full_name} (ID: {user.id})")
        
        # Check OTP records
        recent_otps = OTP.objects.filter(user=user).order_by('-created_at')[:5]
        
        print(f"\n📊 Found {recent_otps.count()} OTP records:")
        for i, otp in enumerate(recent_otps, 1):
            print(f"\n🔢 OTP Record {i}:")
            print(f"  • ID: {otp.id}")
            print(f"  • Type: {otp.otp_type}")
            print(f"  • Code: {otp.otp_code}")
            print(f"  • Email: {otp.email}")
            print(f"  • Verified: {otp.is_verified}")
            print(f"  • Created: {otp.created_at}")
            print(f"  • Expires: {otp.expires_at}")
            print(f"  • Attempts: {otp.attempts}")
            print(f"  • Expired: {otp.is_expired()}")
        
        return True
    except User.DoesNotExist:
        print("❌ User not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_database_tables():
    """Check what OTP tables exist in database"""
    print("\n🗄️ Database Table Investigation:")
    print("=" * 60)
    
    from django.db import connection
    cursor = connection.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    otp_tables = [table[0] for table in tables if 'otp' in table[0].lower()]
    print(f"📋 OTP-related tables: {otp_tables}")
    
    # Check each OTP table structure
    for table in otp_tables:
        print(f"\n📋 Table: {table}")
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  • {col[1]}: {col[2]} (NULL: {bool(col[3])}, DEFAULT: {col[4]})")
    
    return True

def test_otp_verification_payload():
    """Test what the current OTP verification expects"""
    print("\n🧪 Testing OTP Verification Requirements:")
    print("=" * 60)
    
    from accounts.serializers import OTPVerificationSerializer
    
    # Test frontend payload (what they're sending)
    frontend_payload = {
        "email": "princekumar205086@gmail.com",
        "otp": "869506",
        "purpose": "email_verification"
    }
    
    print("📤 Frontend Payload:")
    for key, value in frontend_payload.items():
        print(f"  • {key}: {value}")
    
    # Test with frontend payload
    serializer = OTPVerificationSerializer(data=frontend_payload)
    print(f"\n📋 Frontend payload valid: {serializer.is_valid()}")
    if not serializer.is_valid():
        print(f"❌ Errors: {serializer.errors}")
    
    # Test correct payload
    correct_payload = {
        "email": "princekumar205086@gmail.com",
        "otp_code": "869506",
        "otp_type": "email_verification"
    }
    
    print("\n📥 Correct Payload:")
    for key, value in correct_payload.items():
        print(f"  • {key}: {value}")
    
    serializer2 = OTPVerificationSerializer(data=correct_payload)
    print(f"\n📋 Correct payload valid: {serializer2.is_valid()}")
    if not serializer2.is_valid():
        print(f"❌ Errors: {serializer2.errors}")
    
    return True

def main():
    """Main investigation function"""
    print("🚀 OTP System Investigation")
    print("Debugging the OTP verification payload issue")
    print("=" * 60)
    
    # Run all checks
    check_otp_models()
    check_recent_otp_data()
    check_database_tables()
    test_otp_verification_payload()
    
    print("\n" + "=" * 60)
    print("🎯 INVESTIGATION COMPLETE")
    print("Check the output above to understand the OTP structure")
    print("=" * 60)

if __name__ == '__main__':
    main()
