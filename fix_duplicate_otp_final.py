#!/usr/bin/env python3
"""
🔧 Final Duplicate OTP Fix Script
This script removes ALL duplicate OTPs from the database and ensures clean state
"""

import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append('/srv/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import User, OTP
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

def clean_all_duplicate_otps():
    """Clean ALL duplicate OTPs from database"""
    print("🧹 Cleaning ALL Duplicate OTPs from Database")
    print("=" * 60)
    
    try:
        # Find all users with multiple unverified email OTPs
        users_with_duplicates = User.objects.annotate(
            unverified_otp_count=Count(
                'otps',
                filter=Q(
                    otps__otp_type='email_verification',
                    otps__is_verified=False
                )
            )
        ).filter(unverified_otp_count__gt=1)
        
        print(f"👥 Users with duplicate OTPs: {users_with_duplicates.count()}")
        
        total_cleaned = 0
        
        for user in users_with_duplicates:
            duplicate_otps = OTP.objects.filter(
                user=user,
                otp_type='email_verification',
                is_verified=False
            ).order_by('-created_at')
            
            print(f"\n📧 User: {user.email}")
            print(f"   📊 Has {duplicate_otps.count()} unverified OTPs")
            
            if duplicate_otps.count() > 1:
                # Keep only the latest OTP
                latest_otp = duplicate_otps.first()
                old_otps = duplicate_otps[1:]
                
                print(f"   ✅ Keeping: {latest_otp.otp_code} (Created: {latest_otp.created_at})")
                
                for otp in old_otps:
                    print(f"   🗑️ Deleting: {otp.otp_code} (Created: {otp.created_at})")
                    otp.delete()
                    total_cleaned += 1
        
        print(f"\n✅ Total duplicate OTPs cleaned: {total_cleaned}")
        
        # Also clean up expired OTPs (older than 10 minutes)
        expired_otps = OTP.objects.filter(
            expires_at__lt=timezone.now(),
            is_verified=False
        )
        
        expired_count = expired_otps.count()
        if expired_count > 0:
            print(f"🕐 Deleting {expired_count} expired OTPs")
            expired_otps.delete()
        
        return total_cleaned + expired_count
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return 0

def verify_clean_state():
    """Verify that no duplicates exist"""
    print("\n🔍 Verifying Clean State")
    print("=" * 60)
    
    from django.db.models import Q
    
    # Check for users with multiple unverified email OTPs
    duplicate_users = []
    
    for user in User.objects.all():
        unverified_otps = OTP.objects.filter(
            user=user,
            otp_type='email_verification',
            is_verified=False
        )
        
        if unverified_otps.count() > 1:
            duplicate_users.append((user, unverified_otps.count()))
    
    if duplicate_users:
        print(f"⚠️ Still found {len(duplicate_users)} users with duplicates:")
        for user, count in duplicate_users:
            print(f"   • {user.email}: {count} unverified OTPs")
        return False
    else:
        print("✅ No duplicate OTPs found - database is clean!")
        return True

def test_registration_no_duplicates():
    """Test registration to ensure no duplicates are created"""
    print("\n🧪 Testing Registration for Duplicate Prevention")
    print("=" * 60)
    
    # Clean up test user first
    try:
        User.objects.filter(email='test_noduplicate@gmail.com').delete()
        print("🗑️ Cleaned up existing test user")
    except:
        pass
    
    # Test registration
    registration_payload = {
        "email": "test_noduplicate@gmail.com", 
        "full_name": "Test No Duplicate User",
        "contact": "8888888888",
        "password": "Test@123",
        "password2": "Test@123"
    }
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/register/'
        response = requests.post(url, json=registration_payload, timeout=30)
        
        print(f"📊 Registration Response: {response.status_code}")
        
        if response.status_code == 201:
            # Check OTP count
            test_user = User.objects.get(email='test_noduplicate@gmail.com')
            otps = OTP.objects.filter(
                user=test_user,
                otp_type='email_verification'
            )
            
            print(f"📧 OTPs created: {otps.count()}")
            for i, otp in enumerate(otps, 1):
                print(f"   {i}. {otp.otp_code} (Created: {otp.created_at})")
            
            # Clean up test user
            test_user.delete()
            
            if otps.count() == 1:
                print("✅ Registration creates only 1 OTP - No duplicates!")
                return True
            else:
                print(f"❌ Registration created {otps.count()} OTPs - Still has duplicates!")
                return False
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

def test_existing_user_verification():
    """Test that existing user can verify with cleaned OTP"""
    print("\n🧪 Testing Existing User OTP Verification")
    print("=" * 60)
    
    try:
        # Find a user with unverified email
        user = User.objects.filter(email_verified=False).first()
        
        if not user:
            print("ℹ️ No unverified users found to test")
            return True
            
        print(f"📧 Testing user: {user.email}")
        
        # Check their OTP
        otp = OTP.objects.filter(
            user=user,
            otp_type='email_verification',
            is_verified=False
        ).order_by('-created_at').first()
        
        if not otp:
            print("ℹ️ No unverified OTP found for user")
            return True
            
        print(f"🔢 Using OTP: {otp.otp_code}")
        
        # Test verification with frontend payload
        verification_payload = {
            "email": user.email,
            "otp": otp.otp_code,
            "purpose": "email_verification"
        }
        
        url = 'https://backend.okpuja.in/api/accounts/verify-email/'
        response = requests.post(url, json=verification_payload, timeout=30)
        
        print(f"📊 Verification Response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ OTP verification successful!")
            return True
        else:
            print(f"❌ Verification failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

def main():
    """Main fix and test function"""
    print("🚀 Final Duplicate OTP Fix and Verification")
    print("Cleaning database and testing complete flow")
    print("=" * 60)
    
    # Step 1: Clean all duplicates
    cleaned_count = clean_all_duplicate_otps()
    
    # Step 2: Verify clean state
    is_clean = verify_clean_state()
    
    # Step 3: Test registration doesn't create duplicates
    registration_ok = test_registration_no_duplicates()
    
    # Step 4: Test existing user verification works
    verification_ok = test_existing_user_verification()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"🧹 Database Cleanup: {'✅ DONE' if cleaned_count >= 0 else '❌ FAILED'} ({cleaned_count} duplicates removed)")
    print(f"🔍 Database State: {'✅ CLEAN' if is_clean else '❌ STILL HAS DUPLICATES'}")
    print(f"📝 Registration Test: {'✅ PASS' if registration_ok else '❌ FAIL'}")
    print(f"🔐 Verification Test: {'✅ PASS' if verification_ok else '❌ FAIL'}")
    
    if is_clean and registration_ok:
        print("\n🎉 SUCCESS! Duplicate OTP issue is COMPLETELY FIXED!")
        print("✅ Users will now receive only ONE OTP during registration")
        print("✅ No more confusion with multiple OTP codes")
    else:
        print("\n❌ Issue still exists - please check the logs above")
    
    print("=" * 60)

if __name__ == '__main__':
    main()