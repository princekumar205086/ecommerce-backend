#!/usr/bin/env python3
"""
🧪 Login with OTP Flow Test
Test OTP-based login functionality
"""
import requests
import json
import time

def test_otp_login_flow():
    """Test complete OTP login flow"""
    print("📱 Testing OTP Login Flow")
    print("=" * 60)
    
    # Get email from user
    email = input("👤 Enter email for OTP login: ").strip()
    
    if not email:
        print("❌ Email required")
        return False
    
    print(f"📧 Testing OTP login for: {email}")
    
    # Step 1: Request OTP for login
    print("\n📤 Step 1: Requesting login OTP...")
    
    otp_request_payload = {
        "email": email,
        "otp_type": "login_verification"
    }
    
    try:
        # Try different endpoints that might handle OTP login
        endpoints_to_try = [
            'https://backend.okpuja.in/api/accounts/login/otp/request/',
            'https://backend.okpuja.in/api/accounts/otp/request/',
        ]
        
        otp_request_success = False
        
        for url in endpoints_to_try:
            print(f"   Trying: {url}")
            response = requests.post(url, json=otp_request_payload, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ OTP request successful!")
                otp_request_success = True
                break
            else:
                print(f"   Failed: {response.text}")
        
        if not otp_request_success:
            print("❌ OTP request failed on all endpoints")
            return False
        
        print("📧 Check your email for login OTP")
        
        # Step 2: Get OTP from user
        print("\n🔍 Step 2: Getting login OTP...")
        login_otp = input("👤 Enter the login OTP from email: ").strip()
        
        if not login_otp:
            print("❌ No OTP provided")
            return False
        
        # Step 3: Verify OTP and login
        print(f"\n🔐 Step 3: Verifying OTP and logging in: {login_otp}")
        
        otp_verify_payload = {
            "email": email,
            "otp_code": login_otp,
            "otp_type": "login_verification"
        }
        
        # Try different endpoints for OTP verification
        verify_endpoints = [
            'https://backend.okpuja.in/api/accounts/login/otp/verify/',
            'https://backend.okpuja.in/api/accounts/otp/verify/',
        ]
        
        verify_success = False
        
        for url in verify_endpoints:
            print(f"   Trying: {url}")
            response = requests.post(url, json=otp_verify_payload, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ OTP verification and login successful!")
                
                response_data = response.json()
                
                # Check user data
                user_data = response_data.get('user', {})
                if user_data:
                    print(f"👤 Logged in as: {user_data.get('full_name', 'Unknown')}")
                    print(f"📧 Email: {user_data.get('email', 'Unknown')}")
                
                # Check tokens
                has_access = 'access' in response_data
                has_refresh = 'refresh' in response_data
                
                if has_access and has_refresh:
                    print("🔑 JWT tokens received:")
                    print(f"   Access: {response_data['access'][:50]}...")
                    print(f"   Refresh: {response_data['refresh'][:50]}...")
                    verify_success = True
                    break
                else:
                    print("⚠️ Login successful but no tokens provided")
            else:
                print(f"   Failed: {response.text}")
        
        if not verify_success:
            print("❌ OTP verification failed on all endpoints")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ OTP Login Test Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 OTP Login Flow Test")
    print("Testing: Request OTP → Get OTP → Verify OTP → Login")
    print("=" * 60)
    
    success = test_otp_login_flow()
    
    print("\n" + "=" * 60)
    print("🎯 OTP LOGIN FLOW RESULTS:")
    print(f"📱 Complete Flow: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("\n🎉 OTP Login Flow Working!")
        print("✅ OTP request works")
        print("✅ OTP verification works")
        print("✅ Login via OTP works")
        print("✅ JWT tokens are provided")
    else:
        print("\n⚠️ Issues with OTP login flow")
        print("Note: OTP login might not be fully implemented")
    
    print("=" * 60)

if __name__ == '__main__':
    main()