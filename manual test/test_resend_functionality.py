#!/usr/bin/env python3
"""
🧪 Resend OTP Functionality Test
Test that our unique constraint doesn't break resend functionality
"""
import requests
import json
import time

def test_resend_functionality():
    """Test that resend OTP works with our unique constraint"""
    print("🧪 Testing Resend OTP Functionality")
    print("=" * 60)
    
    # Use a unique email for testing
    test_email = f"resend_test_{int(time.time())}@example.com"
    
    # Step 1: Register a user
    print("📝 Step 1: Registering new user...")
    registration_payload = {
        "email": test_email,
        "full_name": "Resend Test User",
        "contact": "9876543210",
        "password": "Test@123",
        "password2": "Test@123"
    }
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/register/'
        response = requests.post(url, json=registration_payload, timeout=30)
        
        if response.status_code != 201:
            print(f"❌ Registration failed: {response.text}")
            return False
        
        print("✅ Registration successful!")
        
        # Step 2: Test resend verification
        print("\n📧 Step 2: Testing resend verification...")
        
        resend_payload = {
            "email": test_email,
            "otp_type": "email_verification"
        }
        
        resend_url = 'https://backend.okpuja.in/api/accounts/resend-verification/'
        resend_response = requests.post(resend_url, json=resend_payload, timeout=30)
        
        print(f"📊 Resend Response Status: {resend_response.status_code}")
        
        if resend_response.status_code == 200:
            print("✅ Resend verification successful!")
            print("🔐 Our unique constraint allows resend functionality")
            return True
        else:
            print(f"❌ Resend failed: {resend_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

def test_multiple_resends():
    """Test multiple consecutive resends"""
    print("\n🔄 Testing Multiple Consecutive Resends")
    print("=" * 60)
    
    test_email = f"multi_resend_{int(time.time())}@example.com"
    
    # Register user
    registration_payload = {
        "email": test_email,
        "full_name": "Multi Resend Test",
        "contact": "9876543210",
        "password": "Test@123",
        "password2": "Test@123"
    }
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/register/'
        response = requests.post(url, json=registration_payload, timeout=30)
        
        if response.status_code != 201:
            print(f"❌ Registration failed: {response.text}")
            return False
        
        print("✅ Registration successful!")
        
        # Test multiple resends
        resend_payload = {
            "email": test_email,
            "otp_type": "email_verification"
        }
        
        resend_url = 'https://backend.okpuja.in/api/accounts/resend-verification/'
        
        print("\n🔄 Testing 3 consecutive resends...")
        success_count = 0
        
        for i in range(1, 4):
            print(f"\n   Resend #{i}:")
            
            # Wait a bit between resends
            if i > 1:
                time.sleep(2)
            
            resend_response = requests.post(resend_url, json=resend_payload, timeout=30)
            print(f"   Status: {resend_response.status_code}")
            
            if resend_response.status_code == 200:
                print("   ✅ Success")
                success_count += 1
            else:
                print(f"   ❌ Failed: {resend_response.text}")
        
        print(f"\n📊 Successful resends: {success_count}/3")
        
        if success_count >= 2:  # Allow for rate limiting
            print("✅ Multiple resends work correctly!")
            return True
        else:
            print("❌ Multiple resends failed")
            return False
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Resend OTP Functionality Test")
    print("Ensuring our unique constraint doesn't break resend")
    print("=" * 60)
    
    # Test 1: Basic resend functionality
    test1_success = test_resend_functionality()
    
    # Test 2: Multiple resends
    test2_success = test_multiple_resends()
    
    print("\n" + "=" * 60)
    print("🎯 RESEND FUNCTIONALITY RESULTS:")
    print(f"📧 Basic Resend: {'✅ WORKS' if test1_success else '❌ BROKEN'}")
    print(f"🔄 Multiple Resends: {'✅ WORKS' if test2_success else '❌ BROKEN'}")
    
    if test1_success and test2_success:
        print("\n🎉 EXCELLENT!")
        print("✅ Our unique constraint doesn't break resend functionality")
        print("✅ The constraint only prevents simultaneous duplicate OTPs")
        print("✅ Resend works by: Delete old OTP → Create new OTP")
        print("✅ This is exactly what our constraint is designed to allow")
    else:
        print("\n⚠️ Issues detected with resend functionality")
        print("Need to review the unique constraint implementation")
    
    print("=" * 60)

if __name__ == '__main__':
    main()