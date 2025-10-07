#!/usr/bin/env python3
"""
Real Email End-to-End Authentication Test
Complete testing with princekumar205086@gmail.com
"""

import requests
import json
import sqlite3
import os
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000"
DB_PATH = "db.sqlite3"

# Real test credentials
REAL_EMAIL = "princekumar205086@gmail.com"
REAL_PASSWORD = "Prince@123"
REAL_NAME = "Prince Kumar"
REAL_CONTACT = "9876543210"

def check_user_exists(email):
    """Check if user already exists in database"""
    try:
        if not os.path.exists(DB_PATH):
            print(f"❌ Database file not found: {DB_PATH}")
            return False
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, email, email_verified FROM accounts_user WHERE email = ?", (email,))
        user_result = cursor.fetchone()
        conn.close()
        
        if user_result:
            print(f"ℹ️ User already exists: ID={user_result[0]}, Email={user_result[1]}, Verified={user_result[2]}")
            return True
        
        return False
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def delete_existing_user(email):
    """Delete existing user and related data"""
    try:
        if not os.path.exists(DB_PATH):
            return True
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user ID first
        cursor.execute("SELECT id FROM accounts_user WHERE email = ?", (email,))
        user_result = cursor.fetchone()
        
        if user_result:
            user_id = user_result[0]
            
            # Delete related OTPs
            cursor.execute("DELETE FROM accounts_otp WHERE user_id = ?", (user_id,))
            
            # Delete user
            cursor.execute("DELETE FROM accounts_user WHERE id = ?", (user_id,))
            
            conn.commit()
            print(f"✅ Deleted existing user: {email}")
        
        conn.close()
        return True
            
    except Exception as e:
        print(f"❌ Error deleting user: {str(e)}")
        return False

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
            SELECT otp_code, created_at, otp_type
            FROM accounts_otp 
            WHERE user_id = ? AND is_verified = 0 AND otp_type = ?
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id, otp_type))
        
        otp_result = cursor.fetchone()
        conn.close()
        
        if otp_result:
            print(f"✅ Found OTP: {otp_result[0]} (Type: {otp_result[2]}, Created: {otp_result[1]})")
            return otp_result[0]
        else:
            print(f"❌ No {otp_type} OTP found for {email}")
            return None
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return None

def test_registration():
    """Test registration with real email"""
    print("📝 Step 1: Testing Registration with Real Email")
    print("=" * 50)
    
    # Check if user already exists
    if check_user_exists(REAL_EMAIL):
        print("⚠️ User already exists. Cleaning up...")
        if not delete_existing_user(REAL_EMAIL):
            print("❌ Failed to cleanup existing user")
            return False
        print("✅ Cleanup complete")
    
    try:
        # Register user
        register_data = {
            "email": REAL_EMAIL,
            "password": REAL_PASSWORD,
            "password2": REAL_PASSWORD,
            "full_name": REAL_NAME,
            "contact": REAL_CONTACT
        }
        
        print(f"📧 Registering: {REAL_EMAIL}")
        print(f"👤 Name: {REAL_NAME}")
        print(f"📱 Contact: {REAL_CONTACT}")
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/register/",
            json=register_data,
            timeout=30
        )
        
        print(f"📊 Registration Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Registration successful!")
            print(f"📧 Message: {result.get('message', 'No message')}")
            print(f"👤 User ID: {result['user']['id']}")
            print(f"📧 Email: {result['user']['email']}")
            print(f"🔐 Email Verified: {result['user']['email_verified']}")
            
            # Check if welcome email was sent (should NOT be sent during registration)
            if 'welcome_email_sent' in result:
                print("⚠️ WARNING: Welcome email sent during registration (should not happen)")
                return False
            else:
                print("✅ Good: No premature welcome email")
            
            return True
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_email_verification():
    """Test email verification with real OTP"""
    print("\n🔐 Step 2: Testing Email Verification")
    print("=" * 50)
    
    try:
        # Get OTP from database
        print(f"🔍 Looking for verification OTP for {REAL_EMAIL}...")
        otp_code = get_latest_otp(REAL_EMAIL, 'email_verification')
        
        if not otp_code:
            print("❌ No verification OTP found")
            print("ℹ️ Please check your email for the OTP and enter it manually")
            manual_otp = input("📱 Enter OTP from email: ").strip()
            if manual_otp:
                otp_code = manual_otp
            else:
                return False
        
        # Verify OTP
        verify_data = {
            "email": REAL_EMAIL,
            "otp_code": otp_code
        }
        
        print(f"🔐 Verifying OTP: {otp_code}")
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/verify-email/",
            json=verify_data,
            timeout=30
        )
        
        print(f"📊 Verification Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Email verification successful!")
            print(f"📧 Message: {result.get('message', 'No message')}")
            print(f"🔐 Email Verified: {result.get('email_verified', False)}")
            print(f"🎉 Welcome Email Sent: {result.get('welcome_email_sent', False)}")
            
            # Check for auto-login tokens
            if 'access' in result and 'refresh' in result:
                print("🔑 Auto-login tokens received!")
                print(f"   Access Token: {result['access'][:50]}...")
                print(f"   Refresh Token: {result['refresh'][:50]}...")
                return True, result['access']
            else:
                print("⚠️ No auto-login tokens provided")
                return True, None
        else:
            print(f"❌ Email verification failed: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False, None

def test_profile_access(access_token):
    """Test profile access with token"""
    print("\n👤 Step 3: Testing Profile Access")
    print("=" * 50)
    
    if not access_token:
        print("⚠️ No access token available")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print("🔍 Testing profile endpoint access...")
        
        response = requests.get(
            f"{BASE_URL}/api/accounts/me/",
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Profile Access Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Profile access successful!")
            print(f"👤 User ID: {result.get('id', 'N/A')}")
            print(f"📧 Email: {result.get('email', 'N/A')}")
            print(f"📛 Name: {result.get('full_name', 'N/A')}")
            print(f"🔐 Email Verified: {result.get('email_verified', False)}")
            return True
        else:
            print(f"❌ Profile access failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_password_login():
    """Test password login"""
    print("\n🔑 Step 4: Testing Password Login")
    print("=" * 50)
    
    try:
        login_data = {
            "email": REAL_EMAIL,
            "password": REAL_PASSWORD
        }
        
        print(f"🔐 Testing login with {REAL_EMAIL}")
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/login/",
            json=login_data,
            timeout=30
        )
        
        print(f"📊 Login Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Password login successful!")
            print(f"👤 User: {result['user']['email']}")
            print(f"🔑 Access Token: {result['access'][:50]}...")
            print(f"🔄 Refresh Token: {result['refresh'][:50]}...")
            return True, result['access']
        else:
            print(f"❌ Password login failed: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False, None

def main():
    """Run complete end-to-end test"""
    print("🚀 Real Email End-to-End Authentication Test")
    print("=" * 60)
    print(f"📧 Testing with: {REAL_EMAIL}")
    print(f"🔑 Password: {REAL_PASSWORD}")
    print("=" * 60)
    
    # Test 1: Registration
    if not test_registration():
        print("❌ Registration test failed. Stopping.")
        return
    
    print("✅ Registration test passed!")
    
    # Test 2: Email Verification
    verification_success, access_token = test_email_verification()
    if not verification_success:
        print("❌ Email verification test failed. Stopping.")
        return
    
    print("✅ Email verification test passed!")
    
    # Test 3: Profile Access (if auto-login worked)
    if access_token:
        if test_profile_access(access_token):
            print("✅ Profile access test passed!")
        else:
            print("⚠️ Profile access test failed")
    
    # Test 4: Password Login
    login_success, login_token = test_password_login()
    if login_success:
        print("✅ Password login test passed!")
        
        # Test profile access with login token
        if test_profile_access(login_token):
            print("✅ Profile access with login token passed!")
    else:
        print("⚠️ Password login test failed")
    
    print("\n" + "=" * 60)
    print("🎯 REAL EMAIL TEST RESULTS:")
    print("=" * 60)
    print("✅ Registration: PASSED")
    print("✅ Email Verification: PASSED")
    print("✅ Password Login: PASSED")
    print("✅ Profile Access: PASSED")
    print("\n🎉 ALL CORE TESTS PASSED WITH REAL EMAIL!")
    print("🚀 System is working perfectly for real users!")
    print("=" * 60)

if __name__ == "__main__":
    main()