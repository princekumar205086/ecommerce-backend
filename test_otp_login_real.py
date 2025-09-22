#!/usr/bin/env python3
"""
Test OTP Login functionality with real email
"""

import requests
import json
import sqlite3
import os

# Configuration
BASE_URL = "http://127.0.0.1:8000"
DB_PATH = "db.sqlite3"
REAL_EMAIL = "princekumar205086@gmail.com"
CURRENT_PASSWORD = "Prince@999"  # Current password after forgot password test

def get_latest_login_otp(email):
    """Get the latest login OTP for an email"""
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
        
        # Get latest unverified login OTP
        cursor.execute("""
            SELECT otp_code, created_at, otp_type
            FROM accounts_otp 
            WHERE user_id = ? AND is_verified = 0 AND otp_type IN ('login_verification', 'login')
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

def test_otp_login_request():
    """Test OTP login request"""
    print("📱 Step 1: Testing OTP Login Request")
    print("=" * 50)
    
    try:
        # Request OTP for login
        login_otp_data = {"email": REAL_EMAIL}
        
        print(f"🔄 Requesting login OTP for: {REAL_EMAIL}")
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/login/otp/request/",
            json=login_otp_data,
            timeout=30
        )
        
        print(f"📊 OTP Login Request Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OTP login request successful!")
            print(f"📧 Message: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ OTP login request failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_get_login_otp():
    """Get login OTP"""
    print("\n🔍 Step 2: Getting Login OTP")
    print("=" * 50)
    
    # Try to get OTP from database
    otp_code, otp_time = get_latest_login_otp(REAL_EMAIL)
    
    if otp_code:
        print(f"✅ Found login OTP: {otp_code}")
        print(f"⏰ Created at: {otp_time}")
        return otp_code
    else:
        print("❌ No login OTP found in database")
        print("ℹ️ Please check your email for the login OTP")
        
        # Allow manual input
        manual_otp = input("📱 Enter login OTP from email: ").strip()
        if manual_otp:
            print(f"📝 Using manually entered OTP: {manual_otp}")
            return manual_otp
        else:
            print("❌ No OTP provided")
            return None

def test_otp_login_verify(login_otp):
    """Test OTP login verification"""
    print("\n🔐 Step 3: Testing OTP Login Verification")
    print("=" * 50)
    
    if not login_otp:
        print("❌ No login OTP available")
        return False, None
    
    try:
        # Verify OTP for login
        verify_data = {
            "email": REAL_EMAIL,
            "otp_code": login_otp
        }
        
        print(f"🔐 Verifying login with OTP: {login_otp}")
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/login/otp/verify/",
            json=verify_data,
            timeout=30
        )
        
        print(f"📊 OTP Login Verification Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OTP login verification successful!")
            print(f"📧 Message: {result.get('message', 'No message')}")
            
            # Check for login tokens
            if 'access' in result and 'refresh' in result:
                print("🔑 Login tokens received!")
                print(f"   Access Token: {result['access'][:50]}...")
                print(f"   Refresh Token: {result['refresh'][:50]}...")
                return True, result['access']
            else:
                print("⚠️ Login successful but no tokens provided")
                return True, None
        else:
            print(f"❌ OTP login verification failed: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False, None

def test_profile_access_with_otp_login(access_token):
    """Test profile access with OTP login token"""
    print("\n👤 Step 4: Testing Profile Access with OTP Login Token")
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

def test_password_login_still_works():
    """Test that password login still works after OTP login"""
    print("\n🔑 Step 5: Testing Password Login Still Works")
    print("=" * 50)
    
    try:
        login_data = {
            "email": REAL_EMAIL,
            "password": CURRENT_PASSWORD
        }
        
        print(f"🔐 Testing password login: {CURRENT_PASSWORD}")
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/login/",
            json=login_data,
            timeout=30
        )
        
        print(f"📊 Password Login Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Password login still works!")
            print(f"👤 User: {result['user']['email']}")
            return True
        else:
            print(f"❌ Password login failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Run complete OTP login test"""
    print("🚀 OTP Login Flow Test with Real Email")
    print("=" * 60)
    print(f"📧 Testing with: {REAL_EMAIL}")
    print(f"🔑 Current password: {CURRENT_PASSWORD}")
    print("📱 Note: Testing OTP-based login functionality")
    print("=" * 60)
    
    results = {}
    
    # Step 1: Request OTP for login
    results['otp_request'] = test_otp_login_request()
    
    if not results['otp_request']:
        print("❌ Cannot proceed without successful OTP request")
        return
    
    # Step 2: Get login OTP
    login_otp = test_get_login_otp()
    
    if not login_otp:
        print("❌ Cannot proceed without login OTP")
        return
    
    # Step 3: Verify OTP and login
    verify_success, access_token = test_otp_login_verify(login_otp)
    results['otp_verify'] = verify_success
    
    # Step 4: Test profile access with OTP login token
    if access_token:
        results['profile_access'] = test_profile_access_with_otp_login(access_token)
    else:
        results['profile_access'] = False
    
    # Step 5: Test that password login still works
    results['password_login'] = test_password_login_still_works()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 OTP LOGIN TEST RESULTS:")
    print("=" * 60)
    
    test_items = [
        ("OTP Login Request", results['otp_request']),
        ("OTP Login Verification", results['otp_verify']),
        ("Profile Access with OTP Token", results['profile_access']),
        ("Password Login Still Works", results['password_login'])
    ]
    
    all_passed = True
    for item_name, passed in test_items:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{item_name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALL OTP LOGIN TESTS PASSED!")
        print("🚀 OTP login functionality is working perfectly!")
        print("✅ Users can login with both password and OTP")
        print("📱 OTP-based authentication is fully functional")
    else:
        print("⚠️ SOME OTP LOGIN TESTS FAILED!")
        print("❌ Check the results above for details")
    
    print("=" * 60)

if __name__ == "__main__":
    main()