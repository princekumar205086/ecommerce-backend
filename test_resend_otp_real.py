#!/usr/bin/env python3
"""
Test Resend OTP functionality with real email
"""

import requests
import json
import sqlite3
import os

# Configuration
BASE_URL = "http://127.0.0.1:8000"
DB_PATH = "db.sqlite3"
REAL_EMAIL = "princekumar205086@gmail.com"

def get_otp_count(email, otp_type='email_verification'):
    """Get count of OTPs for email"""
    try:
        if not os.path.exists(DB_PATH):
            return 0
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute("SELECT id FROM accounts_user WHERE email = ?", (email,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return 0
            
        user_id = user_result[0]
        
        # Count unverified OTPs
        cursor.execute("""
            SELECT COUNT(*) 
            FROM accounts_otp 
            WHERE user_id = ? AND is_verified = 0 AND otp_type = ?
        """, (user_id, otp_type))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return 0

def get_latest_otp(email, otp_type='email_verification'):
    """Get the latest OTP for an email"""
    try:
        if not os.path.exists(DB_PATH):
            return None
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute("SELECT id FROM accounts_user WHERE email = ?", (email,))
        user_result = cursor.fetchone()
        
        if not user_result:
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
            return otp_result[0], otp_result[1]
        return None, None
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return None, None

def create_unverified_account():
    """Create unverified account for testing resend OTP"""
    print("📝 Creating fresh unverified account for resend OTP test...")
    
    # Use a slightly different email for this test
    test_email = "princekumar205086+resend@gmail.com"
    
    try:
        # Register user
        register_data = {
            "email": test_email,
            "password": "Prince@123",
            "password2": "Prince@123",
            "full_name": "Prince Kumar Resend Test",
            "contact": "9876543210"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/register/",
            json=register_data,
            timeout=30
        )
        
        if response.status_code == 201:
            print(f"✅ Created unverified account: {test_email}")
            return test_email
        else:
            print(f"❌ Failed to create account: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_resend_otp():
    """Test resend OTP functionality"""
    print("🔄 Testing Resend OTP Functionality")
    print("=" * 50)
    
    # Create fresh unverified account
    test_email = create_unverified_account()
    if not test_email:
        print("❌ Cannot create test account")
        return False
    
    try:
        # Check initial OTP count
        initial_count = get_otp_count(test_email)
        initial_otp, initial_time = get_latest_otp(test_email)
        
        print(f"📊 Initial OTP count: {initial_count}")
        print(f"🔐 Initial OTP: {initial_otp}")
        print(f"⏰ Initial time: {initial_time}")
        
        # Test resend OTP
        print("\n🔄 Testing resend OTP...")
        resend_data = {"email": test_email}
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/resend-verification/",
            json=resend_data,
            timeout=30
        )
        
        print(f"📊 Resend Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Resend OTP request successful!")
            print(f"📧 Message: {result.get('message', 'No message')}")
            
            # Check new OTP count and details
            new_count = get_otp_count(test_email)
            new_otp, new_time = get_latest_otp(test_email)
            
            print(f"\n📊 New OTP count: {new_count}")
            print(f"🔐 New OTP: {new_otp}")
            print(f"⏰ New time: {new_time}")
            
            # Verify that only one OTP exists (old one should be deleted)
            if new_count == 1:
                print("✅ Good: Only 1 unverified OTP exists (old one was cleaned up)")
            else:
                print(f"⚠️ Warning: {new_count} unverified OTPs exist")
            
            # Verify new OTP is different from old one
            if new_otp != initial_otp:
                print("✅ Good: New OTP is different from initial OTP")
                return True
            else:
                print("⚠️ Warning: New OTP is same as initial OTP")
                return False
        else:
            print(f"❌ Resend OTP failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_resend_with_verified_account():
    """Test resend OTP with already verified account (should fail)"""
    print("\n🚫 Testing Resend OTP with Verified Account (Should Fail)")
    print("=" * 50)
    
    try:
        # Try to resend OTP for already verified account
        resend_data = {"email": REAL_EMAIL}
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/resend-verification/",
            json=resend_data,
            timeout=30
        )
        
        print(f"📊 Resend Status: {response.status_code}")
        
        if response.status_code != 200:
            print("✅ Good: Resend OTP correctly failed for verified account")
            print(f"📧 Response: {response.text}")
            return True
        else:
            print("⚠️ Warning: Resend OTP worked for verified account (might be unexpected)")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Run resend OTP tests"""
    print("🚀 Resend OTP Functionality Test")
    print("=" * 60)
    
    # Test 1: Resend OTP with unverified account
    test1_result = test_resend_otp()
    
    # Test 2: Resend OTP with verified account (should fail)
    test2_result = test_resend_with_verified_account()
    
    print("\n" + "=" * 60)
    print("🎯 RESEND OTP TEST RESULTS:")
    print("=" * 60)
    
    if test1_result:
        print("✅ Resend OTP (Unverified Account): PASSED")
    else:
        print("❌ Resend OTP (Unverified Account): FAILED")
    
    if test2_result:
        print("✅ Resend OTP (Verified Account): PASSED (Correctly Failed)")
    else:
        print("❌ Resend OTP (Verified Account): FAILED")
    
    if test1_result and test2_result:
        print("\n🎉 ALL RESEND OTP TESTS PASSED!")
        print("🚀 Resend OTP functionality is working correctly!")
    else:
        print("\n⚠️ SOME RESEND OTP TESTS FAILED!")
    
    print("=" * 60)

if __name__ == "__main__":
    main()