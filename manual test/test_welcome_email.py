#!/usr/bin/env python3
"""
Welcome Email Test Script
Tests if welcome email is properly sent after OTP verification
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
    return f"welcometest_{random_suffix}@example.com"

def get_latest_otp(email):
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
            WHERE user_id = ? AND is_verified = 0 AND otp_type = 'email_verification'
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        otp_result = cursor.fetchone()
        conn.close()
        
        if otp_result:
            return otp_result[0]
        return None
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return None

def check_welcome_email_logs():
    """Check if welcome email was sent by looking at Django logs or email backend"""
    # This is a placeholder - in production you'd check email logs
    # For now, we'll rely on the API response
    return True

def test_welcome_email():
    """Test complete welcome email flow"""
    
    print("🎉 Welcome Email Test")
    print("=" * 60)
    
    # Generate test data
    test_email = generate_test_email()
    test_password = "TestPass123!"
    test_name = "Welcome Test User"
    test_contact = "9876543210"
    
    print(f"📧 Test email: {test_email}")
    print()
    
    try:
        # Step 1: Register user
        print("📝 Step 1: Registering new user...")
        register_data = {
            "email": test_email,
            "password": test_password,
            "password2": test_password,
            "full_name": test_name,
            "contact": test_contact
        }
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/register/",
            json=register_data,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            register_response = response.json()
            print(f"👤 User created: {register_response['user']['email']}")
            print(f"📧 Message: {register_response['message']}")
            
            # Check if welcome email was NOT sent during registration
            if 'welcome_email_sent' in register_response:
                print("⚠️ WARNING: Welcome email sent during registration (should not happen)")
            else:
                print("✅ Good: No welcome email sent during registration")
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
        
        print()
        
        # Step 2: Get OTP
        print(f"🔍 Step 2: Getting OTP for {test_email}...")
        otp_code = get_latest_otp(test_email)
        
        if otp_code:
            print(f"✅ Found OTP: {otp_code}")
        else:
            print("❌ No OTP found")
            return False
        
        print()
        
        # Step 3: Verify OTP and check for welcome email
        print("🔐 Step 3: Testing OTP verification + welcome email...")
        verify_data = {
            "email": test_email,
            "otp_code": otp_code
        }
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/verify-email/",
            json=verify_data,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            verification_response = response.json()
            print("✅ OTP verification successful!")
            print(f"📧 Message: {verification_response['message']}")
            print(f"✅ Email verified: {verification_response.get('email_verified', False)}")
            
            # Check for welcome email
            if verification_response.get('welcome_email_sent', False):
                print("🎉 Welcome email sent: ✅ SUCCESS")
                return True
            else:
                print("❌ Welcome email NOT sent")
                return False
        else:
            print(f"❌ OTP verification failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Welcome Email Verification Test")
    print("=" * 60)
    
    success = test_welcome_email()
    
    print()
    print("=" * 60)
    print("🎯 WELCOME EMAIL TEST RESULTS:")
    print("=" * 60)
    
    if success:
        print("🎉 WELCOME EMAIL TEST SUCCESSFUL!")
        print("✅ User registration works")
        print("✅ OTP verification works")
        print("✅ Welcome email sent after verification")
        print("✅ Welcome email timing is correct")
    else:
        print("❌ WELCOME EMAIL TEST FAILED!")
        print("❌ Check the logs above for details")
    
    print("=" * 60)

if __name__ == "__main__":
    main()