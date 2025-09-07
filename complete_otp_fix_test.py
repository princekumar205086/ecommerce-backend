#!/usr/bin/env python3
"""
🔧 Complete OTP Fix Script
Fixes both duplicate OTP issue and payload format issue
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

def clean_duplicate_otps():
    """Clean up duplicate OTPs for the test user"""
    print("🧹 Cleaning Duplicate OTPs")
    print("=" * 60)
    
    try:
        user = User.objects.get(email='princekumar205086@gmail.com')
        
        # Get all unverified email OTPs
        duplicate_otps = OTP.objects.filter(
            user=user,
            otp_type='email_verification',
            is_verified=False
        ).order_by('-created_at')
        
        print(f"📊 Found {duplicate_otps.count()} unverified email OTPs")
        
        if duplicate_otps.count() > 1:
            # Keep only the latest OTP, delete the rest
            latest_otp = duplicate_otps.first()
            old_otps = duplicate_otps[1:]
            
            print(f"✅ Keeping latest OTP: {latest_otp.otp_code} (Created: {latest_otp.created_at})")
            
            for otp in old_otps:
                print(f"🗑️ Deleting old OTP: {otp.otp_code} (Created: {otp.created_at})")
                otp.delete()
            
            print(f"✅ Cleaned up {len(old_otps)} duplicate OTPs")
            return latest_otp.otp_code
        elif duplicate_otps.count() == 1:
            otp = duplicate_otps.first()
            print(f"✅ Single OTP found: {otp.otp_code}")
            return otp.otp_code
        else:
            print("❌ No OTPs found")
            return None
            
    except User.DoesNotExist:
        print("❌ User not found")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_otp_verification_with_frontend_payload(otp_code):
    """Test OTP verification with frontend payload format"""
    print(f"\n🧪 Testing OTP Verification with Frontend Payload")
    print("=" * 60)
    
    if not otp_code:
        print("❌ No OTP code provided")
        return False
    
    # Frontend payload format
    frontend_payload = {
        "email": "princekumar205086@gmail.com",
        "otp": otp_code,  # Frontend uses 'otp'
        "purpose": "email_verification"  # Frontend uses 'purpose'
    }
    
    print(f"📤 Frontend Payload:")
    print(json.dumps(frontend_payload, indent=2))
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/verify-email/'
        response = requests.post(url, json=frontend_payload, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("✅ Frontend payload verification SUCCESSFUL!")
            return True
        else:
            print("❌ Frontend payload verification FAILED")
            return False
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

def create_fresh_registration_test():
    """Test complete registration flow to see if duplicates are created"""
    print(f"\n🧪 Testing Fresh Registration for Duplicate Detection")
    print("=" * 60)
    
    # Clean up existing user first
    try:
        User.objects.filter(email='test_duplicate@gmail.com').delete()
        print("🗑️ Cleaned up existing test user")
    except:
        pass
    
    # Test registration
    registration_payload = {
        "email": "test_duplicate@gmail.com",
        "full_name": "Test Duplicate User",
        "contact": "9999999999",
        "password": "Test@123",
        "password2": "Test@123"
    }
    
    print(f"📤 Registration Payload:")
    print(json.dumps(registration_payload, indent=2))
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/register/'
        response = requests.post(url, json=registration_payload, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            
            # Check how many OTPs were created
            test_user = User.objects.get(email='test_duplicate@gmail.com')
            otps = OTP.objects.filter(
                user=test_user,
                otp_type='email_verification'
            ).order_by('-created_at')
            
            print(f"📊 OTPs created for test user: {otps.count()}")
            for i, otp in enumerate(otps, 1):
                print(f"  {i}. {otp.otp_code} (Created: {otp.created_at})")
            
            if otps.count() > 1:
                print("⚠️ DUPLICATE OTP ISSUE CONFIRMED in registration")
            else:
                print("✅ Single OTP created - no duplicates")
            
            # Clean up test user
            test_user.delete()
            
            return otps.count() == 1
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration Error: {e}")
        return False

def main():
    """Main fix and test function"""
    print("🚀 Complete OTP Fix and Test")
    print("Fixing duplicate OTPs and testing frontend payload")
    print("=" * 60)
    
    # Step 1: Clean duplicate OTPs
    latest_otp_code = clean_duplicate_otps()
    
    # Step 2: Test frontend payload with cleaned OTP
    if latest_otp_code:
        verification_success = test_otp_verification_with_frontend_payload(latest_otp_code)
    else:
        verification_success = False
    
    # Step 3: Test registration flow for duplicates
    registration_clean = create_fresh_registration_test()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"🧹 Duplicate Cleanup: {'✅ DONE' if latest_otp_code else '❌ FAILED'}")
    print(f"📱 Frontend Verification: {'✅ PASS' if verification_success else '❌ FAIL'}")
    print(f"🔄 Registration Clean: {'✅ PASS' if registration_clean else '❌ FAIL (Creates duplicates)'}")
    
    if verification_success:
        print("\n🎉 SUCCESS! OTP verification now works with frontend payload!")
    else:
        print("\n❌ OTP verification still failing - check the logs above")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
