#!/usr/bin/env python3
"""
Complete Password Login Testing
Tests password login with both email and mobile number
"""

import requests
import json
import sqlite3

BASE_URL = "http://127.0.0.1:8000"

def test_password_login_comprehensive():
    """Test password login with both email and contact number"""
    
    print("🔑 Complete Password Login Testing")
    print("=" * 60)
    
    # Get existing user from database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Find a verified user
    cursor.execute("""
        SELECT id, email, full_name, contact, password 
        FROM accounts_user 
        WHERE email_verified = 1 
        ORDER BY id DESC 
        LIMIT 1
    """)
    
    user_result = cursor.fetchone()
    conn.close()
    
    if not user_result:
        print("❌ No verified users found. Creating test account first...")
        return create_test_account_and_verify()
    
    user_id, email, full_name, contact, password_hash = user_result
    print(f"👤 Testing with user: {email}")
    print(f"📱 Contact: {contact}")
    print(f"🆔 User ID: {user_id}")
    
    # We'll use the known password from our previous tests
    test_password = "Prince@999"  # From our last test
    
    # Test 1: Login with email + password
    print("\n🧪 Test 1: Login with Email + Password")
    print("-" * 40)
    
    email_login_data = {
        "email": email,
        "password": test_password
    }
    
    response = requests.post(f"{BASE_URL}/api/accounts/login/", json=email_login_data)
    
    print(f"📊 Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Email login successful!")
        print(f"👤 User: {result.get('user', {}).get('full_name')}")
        print(f"🔑 Access Token: {result.get('access', 'N/A')[:50]}...")
        print(f"🔄 Refresh Token: {result.get('refresh', 'N/A')[:50]}...")
    else:
        print(f"❌ Email login failed: {response.text}")
    
    # Test 2: Login with contact + password
    print("\n🧪 Test 2: Login with Contact + Password")
    print("-" * 40)
    
    contact_login_data = {
        "contact": contact,
        "password": test_password
    }
    
    response = requests.post(f"{BASE_URL}/api/accounts/login/", json=contact_login_data)
    
    print(f"📊 Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Contact login successful!")
        print(f"👤 User: {result.get('user', {}).get('full_name')}")
        print(f"🔑 Access Token: {result.get('access', 'N/A')[:50]}...")
        print(f"🔄 Refresh Token: {result.get('refresh', 'N/A')[:50]}...")
    else:
        print(f"❌ Contact login failed: {response.text}")
    
    # Test 3: Login with both email and contact + password
    print("\n🧪 Test 3: Login with Both Email and Contact + Password")
    print("-" * 40)
    
    both_login_data = {
        "email": email,
        "contact": contact,
        "password": test_password
    }
    
    response = requests.post(f"{BASE_URL}/api/accounts/login/", json=both_login_data)
    
    print(f"📊 Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Both email+contact login successful!")
        print(f"👤 User: {result.get('user', {}).get('full_name')}")
        print(f"🔑 Access Token: {result.get('access', 'N/A')[:50]}...")
        print(f"🔄 Refresh Token: {result.get('refresh', 'N/A')[:50]}...")
    else:
        print(f"❌ Both email+contact login failed: {response.text}")
    
    # Test 4: Profile access with token
    print("\n🧪 Test 4: Profile Access with Token")
    print("-" * 40)
    
    if response.status_code == 200:
        result = response.json()
        access_token = result.get('access')
        
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = requests.get(f"{BASE_URL}/api/accounts/profile/", headers=headers)
        
        print(f"📊 Status Code: {profile_response.status_code}")
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print("✅ Profile access successful!")
            print(f"👤 Name: {profile_data.get('full_name')}")
            print(f"📧 Email: {profile_data.get('email')}")
            print(f"📱 Contact: {profile_data.get('contact')}")
            print(f"✅ Email Verified: {profile_data.get('email_verified')}")
        else:
            print(f"❌ Profile access failed: {profile_response.text}")
    
    return True

def create_test_account_and_verify():
    """Create a new test account and verify it"""
    print("\n🆕 Creating New Test Account")
    print("=" * 40)
    
    test_data = {
        "email": "test_password_login@example.com",
        "password": "TestPass123",
        "password2": "TestPass123",
        "full_name": "Test Password User",
        "contact": "8888888888"
    }
    
    # Register
    response = requests.post(f"{BASE_URL}/api/accounts/register/", json=test_data)
    
    if response.status_code != 201:
        print(f"❌ Registration failed: {response.text}")
        return False
    
    result = response.json()
    user_id = result.get('user', {}).get('id')
    print(f"✅ Account created! User ID: {user_id}")
    
    # Get OTP
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT otp_code FROM accounts_otp 
        WHERE user_id = ? AND otp_type = 'email_verification' AND is_verified = 0
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    
    otp_result = cursor.fetchone()
    conn.close()
    
    if not otp_result:
        print("❌ No OTP found")
        return False
    
    otp_code = otp_result[0]
    print(f"🔐 OTP: {otp_code}")
    
    # Verify
    verify_data = {
        "email": test_data["email"],
        "otp_code": otp_code,
        "otp_type": "email_verification"
    }
    
    verify_response = requests.post(f"{BASE_URL}/api/accounts/verify-email/", json=verify_data)
    
    if verify_response.status_code == 200:
        print("✅ Account verified!")
        print("🔄 Retesting password login with new account...")
        
        # Test password login with new account
        login_data = {
            "email": test_data["email"],
            "password": test_data["password"]
        }
        
        login_response = requests.post(f"{BASE_URL}/api/accounts/login/", json=login_data)
        
        if login_response.status_code == 200:
            print("✅ Password login with new account successful!")
            return True
        else:
            print(f"❌ Password login failed: {login_response.text}")
            return False
    else:
        print(f"❌ Verification failed: {verify_response.text}")
        return False

if __name__ == "__main__":
    print("🔑 Password Login Comprehensive Test")
    print("=" * 60)
    
    success = test_password_login_comprehensive()
    
    print("\n" + "=" * 60)
    print(f"🎯 Final Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("=" * 60)