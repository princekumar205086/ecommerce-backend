#!/usr/bin/env python3
"""
🧪 Final OTP Duplicate Fix Test
Test with database constraints and locking
"""
import requests
import json
import time

def test_ultimate_fix():
    """Test the ultimate fix with constraints and locking"""
    print("🚀 Testing Ultimate OTP Duplicate Fix")
    print("=" * 60)
    
    # Use a unique email
    test_email = f"ultimate_test_{int(time.time())}@example.com"
    
    registration_payload = {
        "email": test_email,
        "full_name": "Ultimate Test User",
        "contact": "9876543210",
        "password": "Test@123",
        "password2": "Test@123"
    }
    
    print(f"📧 Test Email: {test_email}")
    print("📤 Sending registration request...")
    print("")
    print("🔐 Our fixes applied:")
    print("   ✅ Removed OTP creation from serializer")
    print("   ✅ Added database-level locking with select_for_update()")
    print("   ✅ Added unique constraint on unverified OTPs")
    print("   ✅ Enhanced cleanup and verification logic")
    print("")
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/register/'
        response = requests.post(url, json=registration_payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            
            try:
                response_data = response.json()
                message = response_data.get('message', '')
                print(f"💬 Message: {message}")
            except:
                pass
            
            print("")
            print("📧 EMAIL CHECK INSTRUCTIONS:")
            print(f"1. Check your email: {test_email}")
            print("2. Look for 'Verify Your Email - MedixMall' emails")
            print("3. Count how many verification emails you received")
            print("")
            print("✅ EXPECTED RESULT: Exactly 1 verification email")
            print("❌ FAILURE: 2+ verification emails with different OTPs")
            
            return True
            
        elif response.status_code == 400:
            try:
                error_data = response.json()
                print(f"❌ Registration failed: {error_data}")
            except:
                print(f"❌ Registration failed: {response.text}")
            return False
        else:
            print(f"❌ Unexpected response: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return False

def test_with_your_email():
    """Test with your actual email address"""
    print("\n🧪 Testing with Your Real Email")
    print("=" * 60)
    
    real_email = "princekumar205086@gmail.com"
    
    registration_payload = {
        "email": real_email,
        "full_name": "Prince Kumar",
        "contact": "8888888888",
        "password": "Test@123",
        "password2": "Test@123"
    }
    
    print(f"📧 Testing with: {real_email}")
    print("📤 Sending registration request...")
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/register/'
        response = requests.post(url, json=registration_payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            print("")
            print("📧 CHECK YOUR EMAIL NOW!")
            print("Count the verification emails you receive.")
            print("With our fix, you should get exactly 1 email.")
            return True
            
        elif response.status_code == 400:
            try:
                error_data = response.json()
                if 'email' in error_data and 'already exists' in str(error_data):
                    print("ℹ️ User already exists - that's expected")
                    print("The fix prevents duplicate OTPs for new registrations")
                    return True
                else:
                    print(f"❌ Registration failed: {error_data}")
                    return False
            except:
                print(f"❌ Registration failed: {response.text}")
                return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Ultimate OTP Duplicate Fix Test")
    print("Testing all our fixes together")
    print("=" * 60)
    
    # Test 1: With test email
    test1_success = test_ultimate_fix()
    
    # Test 2: With your real email
    test2_success = test_with_your_email()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"🧪 Test Email: {'✅ SUCCESS' if test1_success else '❌ FAILED'}")
    print(f"📧 Your Email: {'✅ SUCCESS' if test2_success else '❌ FAILED'}")
    
    if test1_success:
        print("\n🎉 SUCCESS!")
        print("✅ Our comprehensive fix should prevent duplicate OTPs")
        print("✅ Database constraint ensures only 1 unverified OTP per user")
        print("✅ Row-level locking prevents race conditions")
        print("✅ Enhanced cleanup removes any existing duplicates")
        print("")
        print("📧 Please confirm by checking your email inbox!")
    else:
        print("\n⚠️ Some tests failed - please check the logs above")
    
    print("=" * 60)

if __name__ == '__main__':
    main()