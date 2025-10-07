#!/usr/bin/env python3
"""
🔧 LOCAL ENDPOINT TEST - Verify Rate Limit Status Fix
====================================================
Testing the new rate-limit/status endpoint locally
"""

import requests
import json

def test_local_endpoint():
    """Test the new rate-limit/status endpoint locally"""
    local_rate_limit_url = "http://127.0.0.1:8000/api/accounts/rate-limit/status/"
    
    print("🧪 Testing Local Rate Limit Status Endpoint")
    print("=" * 50)
    
    try:
        # Test without authentication (should get 401)
        print(f"📡 GET {local_rate_limit_url}")
        response = requests.get(local_rate_limit_url, timeout=5)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ SUCCESS! Endpoint exists and requires authentication")
            print("✅ This means the fix is working locally")
            
            try:
                error_data = response.json()
                print(f"📄 Response: {error_data}")
            except:
                print("📄 Response: Authentication required")
                
            return True
        elif response.status_code == 404:
            print("❌ Endpoint still missing locally")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            try:
                data = response.json()
                print(f"📄 Response: {data}")
            except:
                print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_oauth_endpoint_locally():
    """Test OAuth endpoint locally"""
    local_oauth_url = "http://127.0.0.1:8000/api/accounts/login/google/"
    
    print(f"\n🧪 Testing Local OAuth Endpoint")
    print("=" * 50)
    
    try:
        # Test with invalid token
        response = requests.post(
            local_oauth_url,
            json={"id_token": "test_invalid_token"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"📡 POST {local_oauth_url}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ OAuth endpoint working locally")
            try:
                error_data = response.json()
                print(f"📄 Error Response: {error_data}")
            except:
                print("📄 Error response received")
            return True
        else:
            print(f"⚠️  Unexpected OAuth status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OAuth test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧" * 60)
    print("🎯 LOCAL ENDPOINT VERIFICATION TEST")
    print("🔧" * 60)
    
    success_count = 0
    
    if test_local_endpoint():
        success_count += 1
        
    if test_oauth_endpoint_locally():
        success_count += 1
    
    print("\n" + "📊" * 50)
    print(f"✅ Tests Passed: {success_count}/2")
    
    if success_count == 2:
        print("🎉 ALL LOCAL TESTS PASSED!")
        print("✅ Rate limit status endpoint working locally")
        print("✅ Ready for production deployment")
    else:
        print("⚠️  Some tests failed - check implementation")
        
    print("📊" * 50)