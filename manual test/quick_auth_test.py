#!/usr/bin/env python
"""
Simple Registration Test for Production
Tests registration without email dependencies
"""

import requests
import json
import time
from datetime import datetime

# Production base URL
BASE_URL = "https://backend.okpuja.in"

def test_registration():
    """Test user registration"""
    try:
        test_email = f"testuser_{int(time.time())}@example.com"
        
        payload = {
            "email": test_email,
            "full_name": "Test User Production",
            "contact": "9876543210",
            "password": "TestPassword123!",
            "password2": "TestPassword123!",
            "role": "user"
        }
        
        print(f"🧪 Testing registration for: {test_email}")
        print(f"📡 Sending request to: {BASE_URL}/api/accounts/register/user/")
        
        response = requests.post(f"{BASE_URL}/api/accounts/register/user/", json=payload)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Registration successful!")
            print(f"📧 User Email: {data.get('user', {}).get('email', 'N/A')}")
            print(f"👤 Full Name: {data.get('user', {}).get('full_name', 'N/A')}")
            print(f"🔑 Has Access Token: {bool(data.get('access'))}")
            print(f"🔄 Has Refresh Token: {bool(data.get('refresh'))}")
            return True
        else:
            print("❌ Registration failed!")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        return False

def test_login():
    """Test user login"""
    try:
        # Use a known user for login test
        payload = {
            "email": "asliprinceraj@gmail.com",
            "password": "Prince@123"
        }
        
        print(f"\n🔐 Testing login for: {payload['email']}")
        
        response = requests.post(f"{BASE_URL}/api/accounts/login/", json=payload)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"👤 User: {data.get('user', {}).get('email', 'N/A')}")
            print(f"🔑 Has Access Token: {bool(data.get('access'))}")
            print(f"🔄 Has Refresh Token: {bool(data.get('refresh'))}")
            return data
        else:
            print("❌ Login failed!")
            print(f"📄 Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        return None

def test_token_refresh(tokens):
    """Test token refresh"""
    try:
        if not tokens or not tokens.get('refresh'):
            print("\n⚠️ No refresh token available for testing")
            return False
            
        payload = {
            "refresh": tokens['refresh']
        }
        
        print(f"\n🔄 Testing token refresh...")
        
        response = requests.post(f"{BASE_URL}/api/token/refresh/", json=payload)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Token refresh successful!")
            print(f"🔑 New Access Token: {bool(data.get('access'))}")
            return True
        else:
            print("❌ Token refresh failed!")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        return False

def main():
    print("🚀 Starting Simple Authentication Production Test")
    print(f"📍 Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Test 1: Registration
    registration_success = test_registration()
    
    # Test 2: Login
    login_data = test_login()
    
    # Test 3: Token Refresh
    refresh_success = test_token_refresh(login_data)
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"✅ Registration: {'PASS' if registration_success else 'FAIL'}")
    print(f"✅ Login: {'PASS' if login_data else 'FAIL'}")
    print(f"✅ Token Refresh: {'PASS' if refresh_success else 'FAIL'}")
    
    if registration_success and login_data and refresh_success:
        print("\n🎉 Core authentication system is working correctly!")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
