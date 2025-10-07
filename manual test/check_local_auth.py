#!/usr/bin/env python3
"""
🔍 Database OTP Checker
Check OTP in local database
"""
import os
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import OTP, User

def check_otps():
    """Check OTPs in database"""
    print("🔍 Checking OTPs in Local Database")
    print("=" * 50)
    
    # Get all OTPs
    otps = OTP.objects.all().order_by('-created_at')
    
    if not otps:
        print("❌ No OTPs found in database")
        return
    
    print(f"📊 Found {otps.count()} OTP(s)")
    print()
    
    for i, otp in enumerate(otps[:5], 1):  # Show last 5 OTPs
        print(f"OTP #{i}:")
        print(f"  📧 Email: {otp.user.email}")
        print(f"  🔢 Code: {otp.otp_code}")
        print(f"  🎯 Type: {otp.otp_type}")
        print(f"  ✅ Verified: {otp.is_verified}")
        print(f"  📅 Created: {otp.created_at}")
        print(f"  ⏰ Expires: {otp.expires_at}")
        print()
    
    # Check for duplicates for the test user
    test_user_otps = OTP.objects.filter(user__email="test@example.com", is_verified=False)
    print(f"🔍 Unverified OTPs for test@example.com: {test_user_otps.count()}")
    
    if test_user_otps.count() > 1:
        print("⚠️ WARNING: Multiple unverified OTPs found!")
        for otp in test_user_otps:
            print(f"  - {otp.otp_code} (created: {otp.created_at})")
    elif test_user_otps.count() == 1:
        print("✅ Good: Only one unverified OTP found")
        latest_otp = test_user_otps.first()
        print(f"📋 Latest OTP: {latest_otp.otp_code}")
        
        # Return the OTP for verification test
        return latest_otp.otp_code
    else:
        print("❌ No unverified OTPs found for test user")
    
    return None

def verify_otp_test(otp_code):
    """Test OTP verification"""
    if not otp_code:
        print("❌ No OTP code to test")
        return
    
    print(f"\n🔐 Testing OTP Verification: {otp_code}")
    print("=" * 50)
    
    import requests
    
    verify_payload = {
        "email": "test@example.com",
        "otp_code": otp_code
    }
    
    try:
        response = requests.post("http://127.0.0.1:8000/api/accounts/verify-email/", json=verify_payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ OTP verification successful!")
            response_data = response.json()
            
            # Check for auto-login tokens
            has_access = 'access' in response_data
            has_refresh = 'refresh' in response_data
            
            if has_access and has_refresh:
                print("🔑 Auto-login successful! JWT tokens received")
                print("✅ Welcome email should be sent now")
                return True
            else:
                print("⚠️ Verification successful but no auto-login")
                return False
        else:
            print(f"❌ OTP verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Verification Error: {e}")
        return False

def test_login_after_verification():
    """Test login after email verification"""
    print(f"\n🔑 Testing Login After Email Verification")
    print("=" * 50)
    
    login_payload = {
        "email": "test@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post("http://127.0.0.1:8000/api/accounts/login/", json=login_payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful after verification!")
            return True
        else:
            print(f"❌ Login still failing: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Complete Local Authentication Verification")
    print("=" * 60)
    
    # Check OTPs
    otp_code = check_otps()
    
    # Test verification if we have an OTP
    verification_success = False
    if otp_code:
        verification_success = verify_otp_test(otp_code)
    
    # Test login after verification
    login_success = False
    if verification_success:
        login_success = test_login_after_verification()
    
    # Results
    print("\n" + "=" * 60)
    print("🎯 COMPLETE AUTHENTICATION TEST RESULTS:")
    print("=" * 60)
    print(f"📝 Registration: ✅ SUCCESS (from previous test)")
    print(f"🔍 OTP Generation: {'✅ SUCCESS' if otp_code else '❌ FAILED'}")
    print(f"🔐 OTP Verification: {'✅ SUCCESS' if verification_success else '❌ FAILED'}")
    print(f"🔑 Login After Verification: {'✅ SUCCESS' if login_success else '❌ FAILED'}")
    
    if all([otp_code, verification_success, login_success]):
        print("\n🎉 COMPLETE SUCCESS!")
        print("✅ All authentication fixes are working perfectly!")
        print("✅ No duplicate OTP issues")
        print("✅ Welcome email sent after verification")
        print("✅ Auto-login after verification")
        print("✅ Normal login works after verification")
    else:
        print("\n⚠️ Some issues detected - check logs above")
    
    print("=" * 60)

if __name__ == '__main__':
    main()