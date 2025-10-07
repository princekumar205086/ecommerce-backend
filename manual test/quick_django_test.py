#!/usr/bin/env python3
"""
Quick Django Model Test
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

print("✅ Django setup successful")

from accounts.models import User, OTP

print("✅ Models imported successfully")

# Count users
user_count = User.objects.count()
print(f"📊 Total users: {user_count}")

# Count OTPs
otp_count = OTP.objects.count()
print(f"📊 Total OTPs: {otp_count}")

# Check for your email
try:
    user = User.objects.get(email='princekumar205086@gmail.com')
    print(f"✅ Found your user: {user.email}")
    print(f"   Email verified: {user.email_verified}")
    
    # Check OTPs for this user
    user_otps = OTP.objects.filter(user=user, otp_type='email_verification')
    print(f"   Total OTPs: {user_otps.count()}")
    
    unverified_otps = user_otps.filter(is_verified=False)
    print(f"   Unverified OTPs: {unverified_otps.count()}")
    
    if unverified_otps.exists():
        print("   Unverified OTP codes:")
        for otp in unverified_otps:
            print(f"     - {otp.otp_code} (Created: {otp.created_at})")
    
except User.DoesNotExist:
    print("❌ Your user not found")

print("\n🎯 Recent registrations (last 5 users):")
recent_users = User.objects.order_by('-date_joined')[:5]
for user in recent_users:
    print(f"   - {user.email} (Joined: {user.date_joined})")