#!/usr/bin/env python3
"""
🧪 Forgot Password Flow Test
Test complete forgot password functionality end-to-end
"""
import requests
import json
import time

def test_forgot_password_flow():
    """Test complete forgot password flow"""
    print("🔐 Testing Forgot Password Flow")
    print("=" * 60)
    
    # Use existing email for testing
    test_email = input("👤 Enter email to test forgot password: ").strip()
    
    if not test_email:
        print("❌ No email provided")
        return False
    
    print(f"📧 Testing forgot password for: {test_email}")
    
    # Step 1: Request password reset
    print("\n📤 Step 1: Requesting password reset...")
    
    reset_request_payload = {
        "email": test_email
    }
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/password/reset/'
        response = requests.post(url, json=reset_request_payload, timeout=30)
        
        print(f"📊 Reset Request Status: {response.status_code}")
        print(f"📋 Response: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ Password reset request failed")
            return False
        
        print("✅ Password reset request successful")
        print("📧 Check your email for reset OTP")
        
        # Step 2: Get OTP from user
        print("\n🔍 Step 2: Getting reset OTP...")
        reset_otp = input("👤 Enter the password reset OTP from email: ").strip()
        
        if not reset_otp:
            print("❌ No OTP provided")
            return False
        
        # Step 3: Reset password with OTP
        print(f"\n🔑 Step 3: Resetting password with OTP: {reset_otp}")
        
        new_password = "NewTest@123"
        
        reset_confirm_payload = {
            "email": test_email,
            "otp_code": reset_otp,
            "new_password": new_password,
            "confirm_password": new_password
        }
        
        confirm_url = 'https://backend.okpuja.in/api/accounts/password/reset/confirm/'
        confirm_response = requests.post(confirm_url, json=reset_confirm_payload, timeout=30)
        
        print(f"📊 Password Reset Status: {confirm_response.status_code}")
        print(f"📋 Response: {confirm_response.text}")
        
        if confirm_response.status_code == 200:
            print("✅ Password reset successful!")
            
            # Step 4: Test login with new password
            print("\n🔐 Step 4: Testing login with new password...")
            
            login_payload = {
                "email": test_email,
                "password": new_password
            }
            
            login_url = 'https://backend.okpuja.in/api/accounts/login/'
            login_response = requests.post(login_url, json=login_payload, timeout=30)
            
            print(f"📊 Login Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                print("✅ Login with new password successful!")
                login_data = login_response.json()
                user_data = login_data.get('user', {})
                print(f"👤 Logged in as: {user_data.get('full_name', 'Unknown')}")
                return True
            else:
                print(f"❌ Login with new password failed: {login_response.text}")
                return False
        else:
            print(f"❌ Password reset failed")
            return False
            
    except Exception as e:
        print(f"❌ Forgot Password Test Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Forgot Password Flow Test")
    print("Testing: Request Reset → Get OTP → Reset Password → Login")
    print("=" * 60)
    
    success = test_forgot_password_flow()
    
    print("\n" + "=" * 60)
    print("🎯 FORGOT PASSWORD FLOW RESULTS:")
    print(f"🔐 Complete Flow: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("\n🎉 Forgot Password Flow Working Perfectly!")
        print("✅ Password reset request works")
        print("✅ OTP verification works")
        print("✅ Password update works")
        print("✅ Login with new password works")
    else:
        print("\n⚠️ Issues detected in forgot password flow")
    
    print("=" * 60)

if __name__ == '__main__':
    main()