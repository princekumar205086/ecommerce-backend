#!/usr/bin/env python3
"""
Test OTP-Based Forgot Password functionality with real email
"""

import requests
import json
import sqlite3
import os

# Configuration
BASE_URL = "http://127.0.0.1:8000"
DB_PATH = "db.sqlite3"
REAL_EMAIL = "princekumar205086@gmail.com"
ORIGINAL_PASSWORD = "Prince@789"  # Current password after previous test
NEW_PASSWORD = "Prince@999"

def get_latest_password_reset_otp(email):
    """Get the latest password reset OTP for an email"""
    try:
        if not os.path.exists(DB_PATH):
            return None, None
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute("SELECT id FROM accounts_user WHERE email = ?", (email,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return None, None
            
        user_id = user_result[0]
        
        # Get latest unverified password reset OTP
        cursor.execute("""
            SELECT otp_code, created_at, otp_type
            FROM accounts_otp 
            WHERE user_id = ? AND is_verified = 0 AND otp_type = 'password_reset'
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        otp_result = cursor.fetchone()
        conn.close()
        
        if otp_result:
            return otp_result[0], otp_result[1]
        return None, None
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return None, None

def test_otp_forgot_password_request():
    """Test OTP-based forgot password request"""
    print("📤 Step 1: Testing OTP-Based Forgot Password Request")
    print("=" * 50)
    
    try:
        # Request password reset
        reset_data = {"email": REAL_EMAIL}
        
        print(f"🔄 Requesting password reset OTP for: {REAL_EMAIL}")
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/password/reset-request/",
            json=reset_data,
            timeout=30
        )
        
        print(f"📊 Reset Request Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Password reset OTP request successful!")
            print(f"📧 Message: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Password reset OTP request failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_get_password_reset_otp():
    """Get password reset OTP"""
    print("\n🔍 Step 2: Getting Password Reset OTP")
    print("=" * 50)
    
    # Try to get OTP from database
    otp_code, otp_time = get_latest_password_reset_otp(REAL_EMAIL)
    
    if otp_code:
        print(f"✅ Found password reset OTP: {otp_code}")
        print(f"⏰ Created at: {otp_time}")
        return otp_code
    else:
        print("❌ No password reset OTP found in database")
        print("ℹ️ Please check your email for the password reset OTP")
        
        # Allow manual input
        manual_otp = input("📱 Enter password reset OTP from email: ").strip()
        if manual_otp:
            print(f"📝 Using manually entered OTP: {manual_otp}")
            return manual_otp
        else:
            print("❌ No OTP provided")
            return None

def test_otp_password_reset_confirm(reset_otp):
    """Test OTP password reset confirmation"""
    print("\n🔐 Step 3: Testing OTP Password Reset Confirmation")
    print("=" * 50)
    
    if not reset_otp:
        print("❌ No reset OTP available")
        return False
    
    try:
        # Confirm password reset with OTP
        confirm_data = {
            "email": REAL_EMAIL,
            "otp_code": reset_otp,
            "new_password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD
        }
        
        print(f"🔐 Confirming password reset with OTP: {reset_otp}")
        print(f"🔑 New password: {NEW_PASSWORD}")
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/password/reset-confirm/",
            json=confirm_data,
            timeout=30
        )
        
        print(f"📊 Reset Confirmation Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Password reset confirmation successful!")
            print(f"📧 Message: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Password reset confirmation failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_login_with_old_password():
    """Test login with old password (should fail)"""
    print("\n🚫 Step 4: Testing Login with Old Password (Should Fail)")
    print("=" * 50)
    
    try:
        login_data = {
            "email": REAL_EMAIL,
            "password": ORIGINAL_PASSWORD
        }
        
        print(f"🔐 Testing login with old password: {ORIGINAL_PASSWORD}")
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/login/",
            json=login_data,
            timeout=30
        )
        
        print(f"📊 Old Password Login Status: {response.status_code}")
        
        if response.status_code in [400, 401]:
            print("✅ Good: Login with old password correctly failed")
            return True
        else:
            print(f"⚠️ Unexpected: Login with old password succeeded")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_login_with_new_password():
    """Test login with new password (should succeed)"""
    print("\n✅ Step 5: Testing Login with New Password")
    print("=" * 50)
    
    try:
        login_data = {
            "email": REAL_EMAIL,
            "password": NEW_PASSWORD
        }
        
        print(f"🔐 Testing login with new password: {NEW_PASSWORD}")
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/login/",
            json=login_data,
            timeout=30
        )
        
        print(f"📊 New Password Login Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login with new password successful!")
            print(f"👤 User: {result['user']['email']}")
            print(f"🔑 Access Token: {result['access'][:50]}...")
            return True, result['access']
        else:
            print(f"❌ Login with new password failed: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False, None

def test_profile_access_with_new_password(access_token):
    """Test profile access with new password token"""
    print("\n👤 Step 6: Testing Profile Access with New Password")
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
            return True
        else:
            print(f"❌ Profile access failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Run complete OTP-based forgot password test"""
    print("🚀 OTP-Based Forgot Password Flow Test with Real Email")
    print("=" * 60)
    print(f"📧 Testing with: {REAL_EMAIL}")
    print(f"🔑 Current password: {ORIGINAL_PASSWORD}")
    print(f"🔑 New password: {NEW_PASSWORD}")
    print("📱 Note: This system now uses OTP-based password reset")
    print("=" * 60)
    
    results = {}
    
    # Step 1: Request password reset
    results['request'] = test_otp_forgot_password_request()
    
    if not results['request']:
        print("❌ Cannot proceed without successful reset request")
        return
    
    # Step 2: Get reset OTP
    reset_otp = test_get_password_reset_otp()
    
    if not reset_otp:
        print("❌ Cannot proceed without reset OTP")
        return
    
    # Step 3: Confirm password reset
    results['confirm'] = test_otp_password_reset_confirm(reset_otp)
    
    if not results['confirm']:
        print("❌ Cannot proceed without successful reset confirmation")
        return
    
    # Step 4: Test old password (should fail)
    results['old_password'] = test_login_with_old_password()
    
    # Step 5: Test new password (should succeed)
    new_login_success, new_token = test_login_with_new_password()
    results['new_password'] = new_login_success
    
    # Step 6: Test profile access with new password
    if new_login_success:
        results['profile_access'] = test_profile_access_with_new_password(new_token)
    else:
        results['profile_access'] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 OTP-BASED FORGOT PASSWORD TEST RESULTS:")
    print("=" * 60)
    
    test_items = [
        ("Password Reset OTP Request", results['request']),
        ("Password Reset OTP Confirmation", results['confirm']),
        ("Old Password Rejection", results['old_password']),
        ("New Password Login", results['new_password']),
        ("Profile Access", results['profile_access'])
    ]
    
    all_passed = True
    for item_name, passed in test_items:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{item_name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALL OTP-BASED FORGOT PASSWORD TESTS PASSED!")
        print("🚀 OTP-based forgot password functionality is working perfectly!")
        print("✅ Password has been successfully changed")
        print(f"🔑 Current password is now: {NEW_PASSWORD}")
        print("📱 System successfully uses OTP-based password reset instead of tokens")
    else:
        print("⚠️ SOME FORGOT PASSWORD TESTS FAILED!")
        print("❌ Check the results above for details")
    
    print("=" * 60)

if __name__ == "__main__":
    main()