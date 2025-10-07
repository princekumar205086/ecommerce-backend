#!/usr/bin/env python3
"""
Simple Login Test Debug
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_simple_login():
    print("🔑 Simple Login Debug Test")
    print("=" * 40)
    
    # Test with our known working account
    login_data = {
        "email": "princekumar205086@gmail.com",
        "password": "Prince@999"
    }
    
    print(f"🧪 Testing login with: {login_data['email']}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/accounts/login/", json=login_data)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📋 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"👤 User: {result.get('user', {}).get('email')}")
            
            # Test profile access
            access_token = result.get('access')
            if access_token:
                headers = {"Authorization": f"Bearer {access_token}"}
                profile_response = requests.get(f"{BASE_URL}/api/accounts/me/", headers=headers)
                print(f"📊 Profile Status: {profile_response.status_code}")
                if profile_response.status_code == 200:
                    print("✅ Profile access successful!")
                else:
                    print(f"❌ Profile access failed: {profile_response.text}")
            
        else:
            print("❌ Login failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_contact_login():
    print("\n📱 Contact Login Debug Test")
    print("=" * 40)
    
    # Test with contact number  
    login_data = {
        "contact": "9876543210",
        "password": "Prince@999"
    }
    
    print(f"🧪 Testing login with contact: {login_data['contact']}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/accounts/login/", json=login_data)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📋 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Contact login successful!")
            print(f"👤 User: {result.get('user', {}).get('email')}")
        else:
            print("❌ Contact login failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_simple_login()
    test_contact_login()