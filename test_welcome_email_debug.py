#!/usr/bin/env python3
"""
Welcome Email Debug Test
Tests if welcome email is actually being triggered after OTP verification
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_welcome_email_flow():
    """Test complete registration + verification flow to check welcome email"""
    
    print("🧪 Testing Welcome Email Flow")
    print("=" * 50)
    
    # Test data for new account
    test_email = "test_welcome_debug@example.com"
    test_data = {
        "email": test_email,
        "password": "TestPass123",
        "password2": "TestPass123",
        "full_name": "Test Welcome User",
        "contact": "9999999999"
    }
    
    # Step 1: Register new account
    print("📝 Step 1: Registering new account...")
    register_response = requests.post(f"{BASE_URL}/api/accounts/register/", json=test_data)
    
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False
    
    print(f"✅ Registration successful: {register_response.status_code}")
    register_data = register_response.json()
    user_id = register_data.get('user', {}).get('id')
    print(f"👤 User ID: {user_id}")
    
    # Step 2: Get OTP from database
    print("\n🔍 Step 2: Getting verification OTP from database...")
    
    # Check database for OTP
    import sqlite3
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT otp_code, otp_type, is_verified, created_at
        FROM accounts_otp 
        WHERE user_id = ? AND otp_type = 'email_verification' AND is_verified = 0
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    
    otp_result = cursor.fetchone()
    conn.close()
    
    if not otp_result:
        print("❌ No verification OTP found in database")
        return False
    
    otp_code = otp_result[0]
    print(f"🔐 Found verification OTP: {otp_code}")
    
    # Step 3: Verify email with OTP
    print("\n✅ Step 3: Verifying email with OTP...")
    
    verify_data = {
        "email": test_email,
        "otp_code": otp_code,
        "otp_type": "email_verification"
    }
    
    verify_response = requests.post(f"{BASE_URL}/api/accounts/verify-email/", json=verify_data)
    
    print(f"📊 Verification Response Status: {verify_response.status_code}")
    
    if verify_response.status_code == 200:
        verify_result = verify_response.json()
        print(f"✅ Verification successful!")
        print(f"📧 Message: {verify_result.get('message')}")
        print(f"🔐 Email verified: {verify_result.get('email_verified')}")
        print(f"🎉 Welcome email sent: {verify_result.get('welcome_email_sent')}")
        
        # Check if user is email verified in database
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("SELECT email_verified FROM accounts_user WHERE id = ?", (user_id,))
        db_result = cursor.fetchone()
        conn.close()
        
        print(f"📊 Database email_verified status: {db_result[0] if db_result else 'Not found'}")
        
        return True
    else:
        print(f"❌ Verification failed: {verify_response.status_code}")
        print(f"Response: {verify_response.text}")
        return False

def check_email_verification_code():
    """Check the actual code in EmailVerificationView"""
    print("\n🔍 Checking EmailVerificationView implementation...")
    
    with open('accounts/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Look for welcome email sending code
    if 'send_welcome_email' in content:
        print("✅ Found send_welcome_email call in views.py")
        
        # Extract the relevant section
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'send_welcome_email' in line:
                start = max(0, i-5)
                end = min(len(lines), i+10)
                print("\n📋 Code context:")
                for j in range(start, end):
                    prefix = ">>> " if j == i else "    "
                    print(f"{prefix}{j+1}: {lines[j]}")
                break
    else:
        print("❌ send_welcome_email call not found in views.py")
    
    # Check if send_welcome_email method exists in models
    with open('accounts/models.py', 'r', encoding='utf-8') as f:
        models_content = f.read()
        
    if 'def send_welcome_email' in models_content:
        print("✅ send_welcome_email method found in models.py")
    else:
        print("❌ send_welcome_email method not found in models.py")

if __name__ == "__main__":
    print("🧪 Welcome Email Debug Test Suite")
    print("=" * 60)
    
    # First check the code implementation
    check_email_verification_code()
    
    print("\n" + "=" * 60)
    
    # Then test the actual flow
    success = test_welcome_email_flow()
    
    print("\n" + "=" * 60)
    print(f"🎯 Final Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if not success:
        print("\n🔧 Debugging suggestions:")
        print("1. Check if send_welcome_email method is being called")
        print("2. Check email settings configuration") 
        print("3. Check for any exceptions in the welcome email sending")
        print("4. Verify email verification endpoint is working correctly")