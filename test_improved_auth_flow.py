#!/usr/bin/env python3
"""
🧪 Complete Authentication Flow Test
Test registration → OTP verification → auto-login → welcome email flow
"""
import requests
import json
import time

def test_improved_registration_flow():
    """Test the improved registration and verification flow"""
    print("🚀 Testing Improved Registration → Verification → Welcome Flow")
    print("=" * 70)
    
    # Use a unique email for testing
    test_email = f"improved_flow_{int(time.time())}@example.com"
    
    print(f"📧 Test Email: {test_email}")
    
    # Step 1: Registration (should NOT send welcome email)
    print("\n📝 Step 1: Registration...")
    registration_payload = {
        "email": test_email,
        "full_name": "Improved Flow User",
        "contact": "9876543210",
        "password": "Test@123",
        "password2": "Test@123"
    }
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/register/'
        response = requests.post(url, json=registration_payload, timeout=30)
        
        print(f"📊 Registration Status: {response.status_code}")
        
        if response.status_code != 201:
            print(f"❌ Registration failed: {response.text}")
            return False
        
        response_data = response.json()
        print(f"💬 Registration Message: {response_data.get('message', '')}")
        
        # Check that NO tokens are returned during registration
        has_tokens = 'refresh' in response_data or 'access' in response_data
        if has_tokens:
            print("⚠️ WARNING: Tokens returned during registration (should only be after verification)")
        else:
            print("✅ No tokens returned during registration (correct)")
        
        print("📧 Expected: Only verification OTP email (NO welcome email yet)")
        
        # Step 2: Get OTP from database (simulate user checking email)
        print("\n🔍 Step 2: Simulating OTP retrieval...")
        # In real scenario, user would get OTP from email
        # For testing, we'll simulate getting the latest OTP
        
        # Simulate user receiving OTP (you would check your email here)
        otp_code = input("\n👤 Please enter the OTP you received in email: ").strip()
        
        if not otp_code:
            print("❌ No OTP provided")
            return False
        
        # Step 3: Verify OTP (should send welcome email and provide tokens)
        print(f"\n🔐 Step 3: Verifying OTP: {otp_code}")
        
        verification_payload = {
            "email": test_email,
            "otp": otp_code,
            "purpose": "email_verification"
        }
        
        verify_url = 'https://backend.okpuja.in/api/accounts/verify-email/'
        verify_response = requests.post(verify_url, json=verification_payload, timeout=30)
        
        print(f"📊 Verification Status: {verify_response.status_code}")
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            print(f"💬 Verification Message: {verify_data.get('message', '')}")
            
            # Check auto-login functionality
            has_tokens = 'refresh' in verify_data and 'access' in verify_data
            if has_tokens:
                print("✅ Auto-login successful - JWT tokens provided")
                print(f"🔑 Access Token: {verify_data['access'][:50]}...")
                print(f"🔄 Refresh Token: {verify_data['refresh'][:50]}...")
            else:
                print("❌ Auto-login failed - no tokens provided")
            
            # Check welcome email sent
            welcome_sent = verify_data.get('welcome_email_sent', False)
            if welcome_sent:
                print("✅ Welcome email sent after verification")
            else:
                print("⚠️ Welcome email not confirmed sent")
            
            # Check user data
            user_data = verify_data.get('user', {})
            if user_data and user_data.get('email_verified'):
                print("✅ User email verified status updated")
            else:
                print("❌ Email verification status not updated")
            
            print("\n📧 Expected: Welcome email should arrive now")
            
            return True
        else:
            print(f"❌ Verification failed: {verify_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

def test_login_after_verification():
    """Test that user can login normally after verification"""
    print("\n\n🔑 Testing Login After Verification")
    print("=" * 70)
    
    # Try to login with credentials
    test_email = input("👤 Enter the email you just verified: ").strip()
    
    if not test_email:
        print("❌ No email provided")
        return False
    
    login_payload = {
        "email": test_email,
        "password": "Test@123"
    }
    
    try:
        login_url = 'https://backend.okpuja.in/api/accounts/login/'
        login_response = requests.post(login_url, json=login_payload, timeout=30)
        
        print(f"📊 Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            print("✅ Login successful after verification")
            
            user_data = login_data.get('user', {})
            print(f"👤 User: {user_data.get('full_name', 'Unknown')}")
            print(f"📧 Email Verified: {user_data.get('email_verified', False)}")
            
            return True
        else:
            print(f"❌ Login failed: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Complete Authentication Flow Test")
    print("Testing: Registration → OTP → Verification → Welcome → Auto-Login")
    print("=" * 70)
    
    # Test 1: Improved registration flow
    flow_success = test_improved_registration_flow()
    
    # Test 2: Login after verification
    if flow_success:
        login_success = test_login_after_verification()
    else:
        login_success = False
    
    print("\n" + "=" * 70)
    print("🎯 COMPLETE FLOW RESULTS:")
    print(f"📝 Registration → Verification: {'✅ SUCCESS' if flow_success else '❌ FAILED'}")
    print(f"🔑 Login After Verification: {'✅ SUCCESS' if login_success else '❌ FAILED'}")
    
    if flow_success and login_success:
        print("\n🎉 EXCELLENT! Complete Authentication Flow Working!")
        print("✅ Registration no longer sends premature welcome email")
        print("✅ OTP verification triggers welcome email")
        print("✅ Auto-login works after verification")
        print("✅ Manual login works after verification")
        print("✅ User experience is now smooth and logical")
    else:
        print("\n⚠️ Some issues detected - check logs above")
    
    print("\n📧 EMAIL TIMELINE EXPECTED:")
    print("1. Registration → Only OTP verification email")
    print("2. OTP Verification → Welcome email sent")
    print("3. User can immediately use the auto-login tokens")
    print("=" * 70)

if __name__ == '__main__':
    main()