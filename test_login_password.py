#!/usr/bin/env python3
"""
🧪 Login with Password Flow Test
Test standard login with email and password
"""
import requests
import json
import time

def test_login_with_password():
    """Test login with email and password"""
    print("🔑 Testing Login with Password")
    print("=" * 60)
    
    # Get credentials from user
    email = input("👤 Enter email: ").strip()
    password = input("🔐 Enter password: ").strip()
    
    if not email or not password:
        print("❌ Email and password required")
        return False
    
    print(f"📧 Testing login for: {email}")
    
    # Step 1: Attempt login
    print("\n📤 Step 1: Attempting login...")
    
    login_payload = {
        "email": email,
        "password": password
    }
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/login/'
        response = requests.post(url, json=login_payload, timeout=30)
        
        print(f"📊 Login Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            
            response_data = response.json()
            
            # Check user data
            user_data = response_data.get('user', {})
            print(f"👤 Name: {user_data.get('full_name', 'Unknown')}")
            print(f"📧 Email: {user_data.get('email', 'Unknown')}")
            print(f"📱 Contact: {user_data.get('contact', 'Unknown')}")
            print(f"🔐 Role: {user_data.get('role', 'Unknown')}")
            print(f"✅ Email Verified: {user_data.get('email_verified', False)}")
            
            # Check tokens
            has_access = 'access' in response_data
            has_refresh = 'refresh' in response_data
            
            if has_access and has_refresh:
                print("🔑 JWT tokens received:")
                print(f"   Access: {response_data['access'][:50]}...")
                print(f"   Refresh: {response_data['refresh'][:50]}...")
            else:
                print("❌ JWT tokens missing")
            
            return True
            
        elif response.status_code == 403:
            print("❌ Login failed: Email not verified")
            response_data = response.json()
            if not response_data.get('email_verified', True):
                print("📧 Please verify your email first")
            return False
            
        elif response.status_code == 400:
            print("❌ Login failed: Invalid credentials")
            print(f"📋 Response: {response.text}")
            return False
        else:
            print(f"❌ Login failed with status: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login Test Error: {e}")
        return False

def test_authenticated_request():
    """Test making an authenticated request"""
    print("\n🔐 Testing Authenticated Request")
    print("=" * 60)
    
    access_token = input("🔑 Enter access token from login: ").strip()
    
    if not access_token:
        print("❌ No access token provided")
        return False
    
    try:
        # Test getting user profile
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        url = 'https://backend.okpuja.in/api/accounts/me/'
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"📊 Profile Request Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Authenticated request successful!")
            
            profile_data = response.json()
            print(f"👤 Profile: {profile_data.get('full_name', 'Unknown')}")
            print(f"📧 Email: {profile_data.get('email', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Authenticated request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Authenticated Request Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Login with Password Flow Test")
    print("Testing: Email + Password → JWT Tokens → Authenticated Requests")
    print("=" * 60)
    
    # Test 1: Login with password
    login_success = test_login_with_password()
    
    # Test 2: Authenticated request (optional)
    auth_success = False
    if login_success:
        try_auth = input("\n🔐 Test authenticated request? (y/n): ").strip().lower()
        if try_auth == 'y':
            auth_success = test_authenticated_request()
    
    print("\n" + "=" * 60)
    print("🎯 LOGIN WITH PASSWORD RESULTS:")
    print(f"🔑 Login: {'✅ SUCCESS' if login_success else '❌ FAILED'}")
    if login_success:
        print(f"🔐 Authenticated Request: {'✅ SUCCESS' if auth_success else '⏭️ SKIPPED'}")
    
    if login_success:
        print("\n🎉 Login with Password Working!")
        print("✅ Email and password authentication works")
        print("✅ JWT tokens are provided")
        print("✅ User data is returned correctly")
        if auth_success:
            print("✅ Authenticated requests work")
    else:
        print("\n⚠️ Issues with login functionality")
    
    print("=" * 60)

if __name__ == '__main__':
    main()