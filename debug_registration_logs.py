#!/usr/bin/env python3
"""
🧪 Debug Registration with Server Logs
Test registration and monitor server logs for duplicate calls
"""
import requests
import json
import time

def test_registration_with_debug():
    """Test registration with detailed debugging"""
    print("🧪 Testing Registration with Debug Logging")
    print("=" * 60)
    
    # Use a unique email for testing
    test_email = f"debug_test_{int(time.time())}@example.com"
    
    registration_payload = {
        "email": test_email,
        "full_name": "Debug Test User",
        "contact": "9876543210", 
        "password": "Test@123",
        "password2": "Test@123"
    }
    
    print(f"📧 Test Email: {test_email}")
    print("📤 Sending registration request...")
    print("👀 Check server logs for debug output...")
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/register/'
        
        # Record time before request
        start_time = time.time()
        
        response = requests.post(url, json=registration_payload, timeout=30)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"⏱️ Request Duration: {duration:.2f} seconds")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            try:
                response_data = response.json()
                message = response_data.get('message', 'No message')
                print(f"💬 Response Message: {message}")
            except:
                pass
        else:
            print(f"❌ Registration failed: {response.text}")
        
        print("\n🔍 IMPORTANT:")
        print("Check the server logs on backend.okpuja.in for debug output")
        print("Look for these patterns:")
        print("   🚀 Starting registration for email:")
        print("   🔄 send_verification_email() called for")
        print("   ✨ Creating new OTP for")
        print("   🎯 Registration completed for:")
        
        print("\n📧 Also check your email to count verification emails received")
        
        return response.status_code == 201
        
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Debug Registration Test")
    print("=" * 60)
    
    success = test_registration_with_debug()
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS:")
    print("1. Check server logs for debug messages")
    print("2. Count how many times 'send_verification_email() called' appears")
    print("3. Check your email for verification messages")
    print("4. If you see 2 'send_verification_email() called' messages → Found the duplicate!")
    print("5. If you see 1 'send_verification_email() called' but 2 emails → Different issue")
    print("=" * 60)

if __name__ == '__main__':
    main()