#!/usr/bin/env python3
"""
🧪 Real Email Registration Test
Test registration with your real email to verify the fix
"""
import requests
import json

def test_real_email_registration():
    """Test registration with your real email"""
    print("🧪 Testing Registration with Your Real Email")
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
        print(f"📋 Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            print("📧 Check your email now - you should receive:")
            print("   1. Welcome email (without OTP)")
            print("   2. Verification email with OTP")
            print("   ⚠️ If you receive 2 verification emails, the issue still exists")
            print("   ✅ If you receive 1 verification email, the fix worked!")
            return True
            
        elif response.status_code == 400:
            # User might already exist
            try:
                error_data = response.json()
                if 'email' in error_data and 'already exists' in str(error_data['email']):
                    print("ℹ️ User already exists - testing OTP resend instead")
                    return test_otp_resend(real_email)
                else:
                    print(f"❌ Registration failed: {error_data}")
                    return False
            except:
                print(f"❌ Registration failed: {response.text}")
                return False
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return False

def test_otp_resend(email):
    """Test OTP resend for existing user"""
    print(f"\n🔄 Testing OTP Resend for: {email}")
    print("-" * 40)
    
    resend_payload = {
        "email": email,
        "otp_type": "email_verification"
    }
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/resend-verification/'
        response = requests.post(url, json=resend_payload, timeout=30)
        
        print(f"📊 Resend Response Status: {response.status_code}")
        print(f"📋 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ OTP resend successful!")
            print("📧 Check your email - you should receive only 1 verification email")
            return True
        else:
            print(f"❌ OTP resend failed")
            return False
            
    except Exception as e:
        print(f"❌ Resend Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Real Email Registration Test")
    print("Testing with your actual email to verify the fix")
    print("=" * 60)
    
    success = test_real_email_registration()
    
    print("\n" + "=" * 60)
    print("🎯 VERIFICATION STEPS:")
    print("1. Check your email inbox (princekumar205086@gmail.com)")
    print("2. Count the verification emails received")
    print("3. Note the OTP codes")
    print("")
    print("✅ SUCCESS CRITERIA:")
    print("   - You receive exactly 1 verification email")
    print("   - The email contains 1 OTP code")
    print("   - No duplicate emails with different OTPs")
    print("")
    print("❌ FAILURE CRITERIA:")
    print("   - You receive 2+ verification emails")
    print("   - Different OTP codes in multiple emails")
    
    if success:
        print("\n🎉 Please check your email and confirm the results!")
    else:
        print("\n⚠️ API test failed - check server logs")
    
    print("=" * 60)

if __name__ == '__main__':
    main()