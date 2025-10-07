#!/usr/bin/env python3
"""
🧪 Simple Duplicate OTP Test
Tests that registration now creates only one OTP
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

def test_single_registration():
    """Test that registration creates only one OTP"""
    print("🧪 Testing Single OTP Creation During Registration")
    print("=" * 60)
    
    test_email = "test_single_otp@example.com"
    
    # Clean up existing test user
    try:
        existing_user = User.objects.filter(email=test_email)
        if existing_user.exists():
            existing_user.delete()
            print("🗑️ Cleaned up existing test user")
    except:
        pass
    
    # Test registration
    registration_payload = {
        "email": test_email,
        "full_name": "Test Single OTP User",
        "contact": "7777777777",
        "password": "Test@123",
        "password2": "Test@123"
    }
    
    print(f"📤 Registering user: {test_email}")
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/register/'
        response = requests.post(url, json=registration_payload, timeout=30)
        
        print(f"📊 Registration Response: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            
            # Check OTP count immediately
            try:
                test_user = User.objects.get(email=test_email)
                otps = OTP.objects.filter(
                    user=test_user,
                    otp_type='email_verification'
                ).order_by('-created_at')
                
                print(f"📊 Total OTPs created: {otps.count()}")
                
                for i, otp in enumerate(otps, 1):
                    print(f"   {i}. OTP: {otp.otp_code}")
                    print(f"      Created: {otp.created_at}")
                    print(f"      Verified: {otp.is_verified}")
                    print(f"      Email: {otp.email}")
                    print("")
                
                # Test verification with the OTP
                if otps.exists():
                    latest_otp = otps.first()
                    print(f"🔐 Testing verification with OTP: {latest_otp.otp_code}")
                    
                    verification_payload = {
                        "email": test_email,
                        "otp": latest_otp.otp_code,
                        "purpose": "email_verification"
                    }
                    
                    verify_url = 'https://backend.okpuja.in/api/accounts/verify-email/'
                    verify_response = requests.post(verify_url, json=verification_payload, timeout=30)
                    
                    print(f"📊 Verification Response: {verify_response.status_code}")
                    if verify_response.status_code == 200:
                        print("✅ OTP verification successful!")
                        verification_success = True
                    else:
                        print(f"❌ Verification failed: {verify_response.text}")
                        verification_success = False
                else:
                    verification_success = False
                
                # Clean up test user
                test_user.delete()
                print("🗑️ Test user cleaned up")
                
                return otps.count(), verification_success
                
            except User.DoesNotExist:
                print("❌ Test user not found after registration")
                return 0, False
                
        else:
            print(f"❌ Registration failed: {response.text}")
            return 0, False
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return 0, False

def check_your_real_account():
    """Check the real account that was having issues"""
    print("\n🔍 Checking Your Real Account Status")
    print("=" * 60)
    
    real_email = "princekumar205086@gmail.com"
    
    try:
        user = User.objects.get(email=real_email)
        print(f"📧 User: {user.email}")
        print(f"📧 Email Verified: {user.email_verified}")
        
        # Check current OTPs
        otps = OTP.objects.filter(
            user=user,
            otp_type='email_verification'
        ).order_by('-created_at')
        
        print(f"📊 Total OTPs in database: {otps.count()}")
        
        unverified_otps = otps.filter(is_verified=False)
        print(f"📊 Unverified OTPs: {unverified_otps.count()}")
        
        if unverified_otps.exists():
            print("\n🔢 Unverified OTPs:")
            for i, otp in enumerate(unverified_otps, 1):
                print(f"   {i}. {otp.otp_code} (Created: {otp.created_at})")
                
            # If there are multiple unverified OTPs, clean them up
            if unverified_otps.count() > 1:
                print(f"\n🧹 Cleaning up {unverified_otps.count() - 1} duplicate OTPs")
                latest_otp = unverified_otps.first()
                old_otps = unverified_otps[1:]
                
                for otp in old_otps:
                    print(f"   🗑️ Deleting: {otp.otp_code}")
                    otp.delete()
                
                print(f"✅ Kept latest OTP: {latest_otp.otp_code}")
                return latest_otp.otp_code
            else:
                return unverified_otps.first().otp_code
        else:
            print("ℹ️ No unverified OTPs found")
            return None
            
    except User.DoesNotExist:
        print("❌ User not found")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 Simple Duplicate OTP Fix Verification")
    print("=" * 60)
    
    # Test 1: Registration creates only one OTP
    otp_count, verification_works = test_single_registration()
    
    # Test 2: Check your real account
    real_otp = check_your_real_account()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"📝 Registration OTP Count: {otp_count} ({'✅ GOOD' if otp_count == 1 else '❌ BAD - Should be 1'})")
    print(f"🔐 Verification Works: {'✅ YES' if verification_works else '❌ NO'}")
    print(f"📧 Your Account OTP: {real_otp if real_otp else 'None available'}")
    
    if otp_count == 1 and verification_works:
        print("\n🎉 SUCCESS! The duplicate OTP issue is FIXED!")
        print("✅ Registration now creates exactly 1 OTP")
        print("✅ OTP verification works properly")
        if real_otp:
            print(f"✅ Your account has clean OTP: {real_otp}")
    else:
        print("\n⚠️ There may still be issues to resolve")
    
    print("=" * 60)

if __name__ == '__main__':
    main()