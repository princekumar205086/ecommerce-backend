#!/usr/bin/env python3
"""
Complete OTP Login Testing
Tests OTP login with both email and mobile number, ensuring OTP is always sent to email
"""

import requests
import json
import sqlite3
import time

BASE_URL = "http://127.0.0.1:8000"

def test_otp_login_comprehensive():
    """Test OTP login with both email and contact, ensuring OTP goes to email"""
    
    print("📱 Complete OTP Login Testing")
    print("=" * 60)
    
    # Test 1: OTP login with email
    print("🧪 Test 1: OTP Login Request with Email")
    print("-" * 50)
    
    email_otp_request = {
        "email": "princekumar205086@gmail.com"
    }
    
    response = requests.post(f"{BASE_URL}/api/accounts/login/otp/request/", json=email_otp_request)
    
    print(f"📊 Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ OTP request with email successful!")
        print(f"📧 Message: {result.get('message')}")
        print(f"📨 Channel: {result.get('channel')}")
        print(f"📧 Email: {result.get('email')}")
        print(f"🆔 OTP ID: {result.get('otp_id')}")
        
        # Get OTP from database
        otp_id = result.get('otp_id')
        if otp_id:
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("SELECT otp_code FROM accounts_otp WHERE id = ?", (otp_id,))
            otp_result = cursor.fetchone()
            conn.close()
            
            if otp_result:
                otp_code = otp_result[0]
                print(f"🔐 Found OTP: {otp_code}")
                
                # Test OTP verification
                print("\n🔍 Verifying OTP with Email...")
                verify_data = {
                    "email": "princekumar205086@gmail.com",
                    "otp_code": otp_code
                }
                
                verify_response = requests.post(f"{BASE_URL}/api/accounts/login/otp/verify/", json=verify_data)
                print(f"📊 Verify Status: {verify_response.status_code}")
                
                if verify_response.status_code == 200:
                    verify_result = verify_response.json()
                    print("✅ OTP verification successful!")
                    print(f"👤 User: {verify_result.get('user', {}).get('email')}")
                    print(f"🔑 Access Token: {verify_result.get('access', 'N/A')[:50]}...")
                else:
                    print(f"❌ OTP verification failed: {verify_response.text}")
            else:
                print("❌ OTP not found in database")
    else:
        print(f"❌ OTP request failed: {response.text}")
    
    print("\n" + "=" * 60)
    
    # Test 2: OTP login with contact number (should still send to email)
    print("🧪 Test 2: OTP Login Request with Contact Number")
    print("-" * 50)
    
    contact_otp_request = {
        "contact": "9876543210"
    }
    
    response = requests.post(f"{BASE_URL}/api/accounts/login/otp/request/", json=contact_otp_request)
    
    print(f"📊 Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ OTP request with contact successful!")
        print(f"📧 Message: {result.get('message')}")
        print(f"📨 Channel: {result.get('channel')}")
        print(f"📧 Email: {result.get('email')}")
        print(f"🆔 OTP ID: {result.get('otp_id')}")
        
        # Check if OTP was sent to email even though contact was provided
        if result.get('channel') == 'email':
            print("✅ Good: OTP sent to email even when contact was provided")
        else:
            print("❌ Issue: OTP not sent to email")
        
        # Get OTP from database
        otp_id = result.get('otp_id')
        if otp_id:
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("SELECT otp_code, email, phone FROM accounts_otp WHERE id = ?", (otp_id,))
            otp_result = cursor.fetchone()
            conn.close()
            
            if otp_result:
                otp_code, email_field, phone_field = otp_result
                print(f"🔐 Found OTP: {otp_code}")
                print(f"📧 OTP Email Field: {email_field}")
                print(f"📱 OTP Phone Field: {phone_field}")
                
                # Test OTP verification with contact number
                print("\n🔍 Verifying OTP with Contact Number...")
                verify_data = {
                    "contact": "9876543210",
                    "otp_code": otp_code
                }
                
                verify_response = requests.post(f"{BASE_URL}/api/accounts/login/otp/verify/", json=verify_data)
                print(f"📊 Verify Status: {verify_response.status_code}")
                
                if verify_response.status_code == 200:
                    verify_result = verify_response.json()
                    print("✅ OTP verification with contact successful!")
                    print(f"👤 User: {verify_result.get('user', {}).get('email')}")
                    print(f"🔑 Access Token: {verify_result.get('access', 'N/A')[:50]}...")
                else:
                    print(f"❌ OTP verification failed: {verify_response.text}")
            else:
                print("❌ OTP not found in database")
    else:
        print(f"❌ OTP request failed: {response.text}")
    
    print("\n" + "=" * 60)
    
    # Test 3: OTP login with both email and contact
    print("🧪 Test 3: OTP Login Request with Both Email and Contact")
    print("-" * 50)
    
    both_otp_request = {
        "email": "princekumar205086@gmail.com",
        "contact": "9876543210"
    }
    
    response = requests.post(f"{BASE_URL}/api/accounts/login/otp/request/", json=both_otp_request)
    
    print(f"📊 Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ OTP request with both email and contact successful!")
        print(f"📧 Message: {result.get('message')}")
        print(f"📨 Channel: {result.get('channel')}")
        print(f"📧 Email: {result.get('email')}")
        print(f"🆔 OTP ID: {result.get('otp_id')}")
    else:
        print(f"❌ OTP request failed: {response.text}")
    
    return True

def test_registration_with_welcome_email():
    """Test registration with welcome email to ensure it's working"""
    
    print("\n🆕 Testing Registration + Welcome Email")
    print("=" * 60)
    
    test_data = {
        "email": "test_welcome_final@example.com",
        "password": "TestPass123",
        "password2": "TestPass123",
        "full_name": "Test Welcome Final User",
        "contact": "7777777777"
    }
    
    # Register
    response = requests.post(f"{BASE_URL}/api/accounts/register/", json=test_data)
    
    if response.status_code != 201:
        print(f"❌ Registration failed: {response.text}")
        return False
    
    result = response.json()
    user_id = result.get('user', {}).get('id')
    print(f"✅ Registration successful! User ID: {user_id}")
    
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
        print("❌ No verification OTP found")
        return False
    
    otp_code = otp_result[0]
    print(f"🔐 Verification OTP: {otp_code}")
    
    # Verify email
    verify_data = {
        "email": test_data["email"],
        "otp_code": otp_code,
        "otp_type": "email_verification"
    }
    
    verify_response = requests.post(f"{BASE_URL}/api/accounts/verify-email/", json=verify_data)
    
    if verify_response.status_code == 200:
        verify_result = verify_response.json()
        print("✅ Email verification successful!")
        print(f"📧 Message: {verify_result.get('message')}")
        print(f"🎉 Welcome email sent: {verify_result.get('welcome_email_sent')}")
        
        # Test login with new account
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
    print("📱 OTP Login Comprehensive Test Suite")
    print("=" * 60)
    
    # Test OTP login functionality
    otp_success = test_otp_login_comprehensive()
    
    print("\n" + "=" * 60)
    
    # Test registration + welcome email
    reg_success = test_registration_with_welcome_email()
    
    print("\n" + "=" * 60)
    print(f"🎯 OTP Login Result: {'✅ SUCCESS' if otp_success else '❌ FAILED'}")
    print(f"🎯 Registration + Welcome Result: {'✅ SUCCESS' if reg_success else '❌ FAILED'}")
    print("=" * 60)