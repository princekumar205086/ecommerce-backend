#!/usr/bin/env python3
"""
🧪 Live Registration Test
Test actual registration flow to verify single OTP creation
"""
import requests
import json
import time

def test_live_registration():
    """Test registration with a real API call"""
    print("🧪 Testing Live Registration Flow")
    print("=" * 60)
    
    # Use a unique email for testing
    test_email = f"test_fix_{int(time.time())}@example.com"
    
    registration_payload = {
        "email": test_email,
        "full_name": "Test Fix User",
        "contact": "9876543210",
        "password": "Test@123",
        "password2": "Test@123"
    }
    
    print(f"📧 Test Email: {test_email}")
    print("📤 Sending registration request...")
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/register/'
        response = requests.post(url, json=registration_payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            
            # Parse response
            try:
                response_data = response.json()
                print(f"📋 Response keys: {list(response_data.keys())}")
                
                if 'message' in response_data:
                    print(f"💬 Message: {response_data['message']}")
                    
                return True
                
            except json.JSONDecodeError:
                print("⚠️ Could not parse JSON response")
                print(f"Raw response: {response.text[:200]}")
                return True
                
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return False

def check_email_received():
    """Instructions for manual email check"""
    print("\n📧 Manual Email Check Instructions")
    print("=" * 60)
    print("1. Check your email inbox for the test email above")
    print("2. Look for 'Verify Your Email - MedixMall' subject")
    print("3. Count how many verification emails you received")
    print("4. Note the OTP codes in each email")
    print("")
    print("✅ EXPECTED: You should receive exactly 1 email with 1 OTP code")
    print("❌ PROBLEM: If you receive 2 emails with different OTP codes")

def main():
    """Main test function"""
    print("🚀 Live Registration OTP Test")
    print("Testing if registration creates duplicate OTPs")
    print("=" * 60)
    
    # Test registration
    registration_success = test_live_registration()
    
    # Manual check instructions
    check_email_received()
    
    print("\n" + "=" * 60)
    print("🎯 RESULTS:")
    print(f"📝 Registration API: {'✅ SUCCESS' if registration_success else '❌ FAILED'}")
    print("")
    print("🔍 Next Steps:")
    if registration_success:
        print("1. Check your email inbox for the verification email")
        print("2. If you receive only 1 email → Fix is working! ✅")
        print("3. If you receive 2 emails → Issue still exists ❌")
    else:
        print("1. Registration failed - check server logs")
        print("2. Try again or contact support")
    
    print("=" * 60)

if __name__ == '__main__':
    main()