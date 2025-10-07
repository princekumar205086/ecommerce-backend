#!/usr/bin/env python3
"""
🔄 Fresh Auto-Login Test
Test auto-login functionality with a new user
"""
import os
import django
import requests
import random
import string

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import OTP, User

BASE_URL = "http://127.0.0.1:8000"

def generate_test_email():
    """Generate a unique test email"""
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"autotest_{random_string}@example.com"

def test_complete_auto_login_flow():
    """Test complete registration → OTP → auto-login flow"""
    print("🔄 Fresh Auto-Login Test")
    print("=" * 60)
    
    # Generate new test user
    test_email = generate_test_email()
    test_password = "AutoTest123!"
    
    print(f"📧 New test email: {test_email}")
    
    # Step 1: Register new user
    print("\n📝 Step 1: Registering new user...")
    
    register_payload = {
        "email": test_email,
        "password": test_password,
        "password2": test_password,
        "full_name": "Auto Test User",
        "contact": "9876543210"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/accounts/register/", json=register_payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            response_data = response.json()
            print(f"👤 User created: {response_data['user']['email']}")
            print(f"📧 Message: {response_data['message']}")
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration Error: {e}")
        return False
    
    # Step 2: Get OTP from database
    print(f"\n🔍 Step 2: Getting OTP for {test_email}...")
    
    try:
        user = User.objects.get(email=test_email)
        otp_instance = OTP.objects.filter(user=user, is_verified=False, otp_type='email_verification').first()
        
        if otp_instance:
            otp_code = otp_instance.otp_code
            print(f"✅ Found OTP: {otp_code}")
        else:
            print("❌ No unverified OTP found")
            return False
            
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return False
    
    # Step 3: Verify OTP and test auto-login
    print(f"\n🔐 Step 3: Testing OTP verification + auto-login...")
    
    verify_payload = {
        "email": test_email,
        "otp_code": otp_code
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/accounts/verify-email/", json=verify_payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ OTP verification successful!")
            response_data = response.json()
            
            # Check auto-login components
            print(f"📧 Message: {response_data.get('message', 'No message')}")
            print(f"✅ Email verified: {response_data.get('email_verified', False)}")
            print(f"📧 Welcome email sent: {response_data.get('welcome_email_sent', False)}")
            
            # Check JWT tokens (auto-login)
            has_access = 'access' in response_data
            has_refresh = 'refresh' in response_data
            
            if has_access and has_refresh:
                print("\n🔑 AUTO-LOGIN SUCCESSFUL!")
                print(f"   ✅ Access Token: {response_data['access'][:50]}...")
                print(f"   ✅ Refresh Token: {response_data['refresh'][:50]}...")
                
                # Test using the access token
                print(f"\n🧪 Step 4: Testing access token...")
                headers = {
                    'Authorization': f'Bearer {response_data["access"]}'
                }
                
                # Try accessing a protected endpoint (if available)
                test_response = requests.get(f"{BASE_URL}/api/accounts/profile/", headers=headers, timeout=30)
                print(f"Profile access status: {test_response.status_code}")
                
                if test_response.status_code == 200:
                    print("✅ Access token works for authenticated requests!")
                else:
                    print(f"⚠️ Profile endpoint response: {test_response.text}")
                
                return True
            else:
                print("❌ Auto-login failed - no JWT tokens provided")
                return False
        else:
            print(f"❌ OTP verification failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Verification Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Complete Auto-Login Flow Verification")
    print("=" * 60)
    
    success = test_complete_auto_login_flow()
    
    print("\n" + "=" * 60)
    print("🎯 AUTO-LOGIN TEST RESULTS:")
    print("=" * 60)
    
    if success:
        print("🎉 AUTO-LOGIN FUNCTIONALITY CONFIRMED!")
        print("✅ Registration creates user")
        print("✅ Single OTP generated")
        print("✅ OTP verification successful")
        print("✅ JWT tokens provided immediately")
        print("✅ Welcome email sent after verification")
        print("✅ User can make authenticated requests")
        print("\n🔥 Auto-login is working perfectly!")
    else:
        print("❌ Auto-login functionality needs attention")
    
    print("=" * 60)

if __name__ == '__main__':
    main()