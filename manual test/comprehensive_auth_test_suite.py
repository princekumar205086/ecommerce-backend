#!/usr/bin/env python3
"""
Comprehensive Authentication Test Suite
Tests all authentication flows:
1. Welcome Email
2. Resend OTP
3. Forgot Password
4. Login with Password
5. Login with OTP
"""

import requests
import json
import random
import string
import sqlite3
import os

# Configuration
BASE_URL = "http://127.0.0.1:8000"
DB_PATH = "db.sqlite3"

def generate_test_email():
    """Generate a unique test email"""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"authtest_{random_suffix}@example.com"

def get_latest_otp(email, otp_type='email_verification'):
    """Get the latest OTP for an email from database"""
    try:
        if not os.path.exists(DB_PATH):
            print(f"❌ Database file not found: {DB_PATH}")
            return None
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute("SELECT id FROM accounts_user WHERE email = ?", (email,))
        user_result = cursor.fetchone()
        
        if not user_result:
            print(f"❌ User not found: {email}")
            return None
            
        user_id = user_result[0]
        
        # Get latest unverified OTP
        cursor.execute("""
            SELECT otp_code, created_at 
            FROM accounts_otp 
            WHERE user_id = ? AND is_verified = 0 AND otp_type = ?
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id, otp_type))
        
        otp_result = cursor.fetchone()
        conn.close()
        
        if otp_result:
            return otp_result[0]
        return None
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return None

def test_welcome_email_flow():
    """Test welcome email after OTP verification"""
    print("🎉 Testing Welcome Email Flow")
    print("-" * 40)
    
    test_email = generate_test_email()
    test_password = "TestPass123!"
    
    try:
        # Register user
        register_data = {
            "email": test_email,
            "password": test_password,
            "password2": test_password,
            "full_name": "Welcome Test User",
            "contact": "9876543210"
        }
        
        response = requests.post(f"{BASE_URL}/api/accounts/register/", json=register_data, timeout=30)
        
        if response.status_code != 201:
            print(f"❌ Registration failed: {response.status_code}")
            return False
        
        print("✅ User registered successfully")
        
        # Get OTP
        otp_code = get_latest_otp(test_email)
        if not otp_code:
            print("❌ No OTP found")
            return False
        
        print(f"✅ OTP found: {otp_code}")
        
        # Verify OTP
        verify_data = {"email": test_email, "otp_code": otp_code}
        response = requests.post(f"{BASE_URL}/api/accounts/verify-email/", json=verify_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('welcome_email_sent', False):
                print("✅ Welcome email sent after verification")
                return True
            else:
                print("❌ Welcome email not sent")
                return False
        else:
            print(f"❌ OTP verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_resend_otp_flow():
    """Test resend OTP functionality"""
    print("🔄 Testing Resend OTP Flow")
    print("-" * 40)
    
    test_email = generate_test_email()
    test_password = "TestPass123!"
    
    try:
        # Register user
        register_data = {
            "email": test_email,
            "password": test_password,
            "password2": test_password,
            "full_name": "Resend Test User",
            "contact": "9876543210"
        }
        
        response = requests.post(f"{BASE_URL}/api/accounts/register/", json=register_data, timeout=30)
        
        if response.status_code != 201:
            print(f"❌ Registration failed: {response.status_code}")
            return False
        
        print("✅ User registered successfully")
        
        # Test resend OTP
        resend_data = {"email": test_email}
        response = requests.post(f"{BASE_URL}/api/accounts/resend-verification/", json=resend_data, timeout=30)
        
        if response.status_code == 200:
            print("✅ Resend OTP successful")
            
            # Check if new OTP was generated
            new_otp = get_latest_otp(test_email)
            if new_otp:
                print(f"✅ New OTP generated: {new_otp}")
                return True
            else:
                print("❌ No new OTP found")
                return False
        else:
            print(f"❌ Resend OTP failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def create_verified_user(email, password, name, contact):
    """Create and verify a user"""
    try:
        # Register
        register_data = {
            "email": email,
            "password": password,
            "password2": password,
            "full_name": name,
            "contact": contact
        }
        
        response = requests.post(f"{BASE_URL}/api/accounts/register/", json=register_data, timeout=30)
        if response.status_code != 201:
            return False
        
        # Get OTP and verify
        otp_code = get_latest_otp(email)
        if not otp_code:
            return False
        
        verify_data = {"email": email, "otp_code": otp_code}
        response = requests.post(f"{BASE_URL}/api/accounts/verify-email/", json=verify_data, timeout=30)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return False

def test_forgot_password_flow():
    """Test forgot password functionality"""
    print("🔐 Testing Forgot Password Flow")
    print("-" * 40)
    
    test_email = generate_test_email()
    original_password = "OriginalPass123!"
    new_password = "NewPass456!"
    
    try:
        # Create verified user
        if not create_verified_user(test_email, original_password, "Forgot Test User", "9876543210"):
            print("❌ Failed to create verified user")
            return False
        
        print("✅ Verified user created")
        
        # Request password reset
        reset_data = {"email": test_email}
        response = requests.post(f"{BASE_URL}/api/accounts/password/reset-request/", json=reset_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Password reset request failed: {response.status_code}")
            return False
        
        print("✅ Password reset request successful")
        
        # Get reset OTP
        reset_otp = get_latest_otp(test_email, 'password_reset')
        if not reset_otp:
            print("❌ No password reset OTP found")
            return False
        
        print(f"✅ Reset OTP found: {reset_otp}")
        
        # Confirm password reset
        confirm_data = {
            "email": test_email,
            "otp_code": reset_otp,
            "new_password": new_password,
            "confirm_password": new_password
        }
        
        response = requests.post(f"{BASE_URL}/api/accounts/password/reset-confirm/", json=confirm_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Password reset confirmation failed: {response.status_code}")
            return False
        
        print("✅ Password reset successful")
        
        # Test login with new password
        login_data = {"email": test_email, "password": new_password}
        response = requests.post(f"{BASE_URL}/api/accounts/login/", json=login_data, timeout=30)
        
        if response.status_code == 200:
            print("✅ Login with new password successful")
            return True
        else:
            print(f"❌ Login with new password failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_password_login_flow():
    """Test normal password login"""
    print("🔑 Testing Password Login Flow")
    print("-" * 40)
    
    test_email = generate_test_email()
    test_password = "LoginPass123!"
    
    try:
        # Create verified user
        if not create_verified_user(test_email, test_password, "Login Test User", "9876543210"):
            print("❌ Failed to create verified user")
            return False
        
        print("✅ Verified user created")
        
        # Test login
        login_data = {"email": test_email, "password": test_password}
        response = requests.post(f"{BASE_URL}/api/accounts/login/", json=login_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'access' in result and 'refresh' in result:
                print("✅ Password login successful with JWT tokens")
                return True
            else:
                print("❌ Login successful but no JWT tokens")
                return False
        else:
            print(f"❌ Password login failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_otp_login_flow():
    """Test OTP-based login"""
    print("📱 Testing OTP Login Flow")
    print("-" * 40)
    
    test_email = generate_test_email()
    test_password = "OTPLoginPass123!"
    
    try:
        # Create verified user
        if not create_verified_user(test_email, test_password, "OTP Login Test User", "9876543210"):
            print("❌ Failed to create verified user")
            return False
        
        print("✅ Verified user created")
        
        # Request OTP login
        otp_request_data = {"email": test_email}
        response = requests.post(f"{BASE_URL}/api/accounts/login/otp/request/", json=otp_request_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ OTP login request failed: {response.status_code}")
            return False
        
        print("✅ OTP login request successful")
        
        # Get login OTP
        login_otp = get_latest_otp(test_email, 'login')
        if not login_otp:
            print("❌ No login OTP found")
            return False
        
        print(f"✅ Login OTP found: {login_otp}")
        
        # Verify OTP login
        verify_data = {"email": test_email, "otp_code": login_otp}
        response = requests.post(f"{BASE_URL}/api/accounts/login/otp/verify/", json=verify_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'access' in result and 'refresh' in result:
                print("✅ OTP login successful with JWT tokens")
                return True
            else:
                print("❌ OTP login successful but no JWT tokens")
                return False
        else:
            print(f"❌ OTP login verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Run all authentication tests"""
    print("🚀 Comprehensive Authentication Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Welcome Email", test_welcome_email_flow),
        ("Resend OTP", test_resend_otp_flow),
        ("Forgot Password", test_forgot_password_flow),
        ("Password Login", test_password_login_flow),
        ("OTP Login", test_otp_login_flow)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"🧪 Running {test_name} Test...")
        results[test_name] = test_func()
        print()
    
    # Summary
    print("=" * 60)
    print("🎯 COMPREHENSIVE TEST RESULTS:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALL AUTHENTICATION TESTS PASSED!")
        print("✅ Your authentication system is fully functional!")
    else:
        print("⚠️ SOME TESTS FAILED!")
        print("❌ Please check the failed tests above")
    
    print("=" * 60)

if __name__ == "__main__":
    main()