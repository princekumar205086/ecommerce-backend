#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE GOOGLE OAUTH REAL TEST SUITE
==============================================
This script performs exhaustive testing of the Google OAuth system
matching your JWT authentication system exactly.
"""

import requests
import json
import time
from datetime import datetime
import jwt
import base64

class ComprehensiveGoogleOAuthTester:
    def __init__(self):
        self.base_url = "https://backend.okpuja.in/api"
        self.oauth_endpoint = f"{self.base_url}/accounts/login/google/"
        self.login_endpoint = f"{self.base_url}/accounts/login/"
        self.success_tests = 0
        self.total_tests = 0
        self.test_results = []
        
    def print_banner(self):
        """Print comprehensive test banner"""
        print("🔥" * 80)
        print("🚀 COMPREHENSIVE GOOGLE OAUTH REAL TEST SUITE")
        print("🔥" * 80)
        print("✅ Testing live production endpoints")
        print("✅ Comparing with JWT authentication system")
        print("✅ Validating all payloads and responses")
        print("✅ Ensuring 100% consistency")
        print("=" * 80)
        
    def decode_jwt_payload(self, token):
        """Decode JWT token to inspect payload"""
        try:
            # JWT tokens have 3 parts separated by dots
            parts = token.split('.')
            if len(parts) != 3:
                return None
                
            # Decode the payload (middle part)
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded.decode('utf-8'))
        except Exception as e:
            print(f"❌ JWT decode error: {e}")
            return None
    
    def test_oauth_endpoint_structure(self):
        """Test 1: OAuth endpoint structure and error handling"""
        print("\n🧪 TEST 1: OAuth Endpoint Structure & Error Handling")
        print("-" * 60)
        self.total_tests += 1
        
        # Test 1a: Missing id_token
        try:
            response = requests.post(
                self.oauth_endpoint,
                json={},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"📡 Empty request - Status: {response.status_code}")
            if response.status_code == 400:
                error_data = response.json()
                print(f"✅ Error handling: {error_data}")
                self.success_tests += 1
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            
        # Test 1b: Invalid id_token
        try:
            response = requests.post(
                self.oauth_endpoint,
                json={"id_token": "invalid_token_test"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"📡 Invalid token - Status: {response.status_code}")
            if response.status_code in [400, 401]:
                error_data = response.json()
                print(f"✅ Invalid token handling: {error_data}")
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    def test_oauth_real_authentication(self):
        """Test 2: Real Google OAuth authentication"""
        print("\n🧪 TEST 2: Real Google OAuth Authentication")
        print("-" * 60)
        self.total_tests += 1
        
        print("🔑 To test with real Google token:")
        print("1. 🌐 Go to: https://developers.google.com/oauthplayground/")
        print("2. ⚙️  Click gear → Use your own OAuth credentials")
        print("3. 📝 Enter your Google Client ID and Secret")
        print("4. 🔍 Select scopes: userinfo.email, userinfo.profile")
        print("5. 🔓 Authorize and get id_token")
        print()
        
        # Wait for user input
        print("🎯 Paste your real Google id_token (or 'skip' to skip):")
        user_token = input().strip()
        
        if user_token.lower() == 'skip':
            print("⏭️  Skipping real token test")
            return
            
        if len(user_token) < 100:
            print("❌ Token too short, skipping test")
            return
            
        try:
            # Test the real OAuth authentication
            payload = {"id_token": user_token}
            
            print(f"📡 Testing OAuth with real token...")
            start_time = time.time()
            
            response = requests.post(
                self.oauth_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            response_time = time.time() - start_time
            print(f"⏱️  Response time: {response_time:.2f} seconds")
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                oauth_data = response.json()
                print("🎉 SUCCESS! OAuth authentication working!")
                print(f"✅ User: {oauth_data.get('user', {}).get('full_name')}")
                print(f"✅ Email: {oauth_data.get('user', {}).get('email')}")
                print(f"✅ User ID: {oauth_data.get('user', {}).get('id')}")
                print(f"✅ New User: {oauth_data.get('is_new_user')}")
                print(f"✅ Message: {oauth_data.get('message')}")
                
                # Analyze JWT tokens
                access_token = oauth_data.get('access')
                refresh_token = oauth_data.get('refresh')
                
                if access_token:
                    access_payload = self.decode_jwt_payload(access_token)
                    print(f"🔍 Access Token Payload: {access_payload}")
                    
                if refresh_token:
                    refresh_payload = self.decode_jwt_payload(refresh_token)
                    print(f"🔍 Refresh Token Payload: {refresh_payload}")
                
                self.success_tests += 1
                
                # Store successful OAuth response for comparison
                self.oauth_response = oauth_data
                
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"❌ OAuth failed: {error_data}")
                
        except Exception as e:
            print(f"❌ OAuth test failed: {e}")
    
    def test_regular_login_comparison(self):
        """Test 3: Compare OAuth with regular login"""
        print("\n🧪 TEST 3: OAuth vs Regular Login Comparison")
        print("-" * 60)
        self.total_tests += 1
        
        if not hasattr(self, 'oauth_response'):
            print("⏭️  Skipping comparison - no OAuth response available")
            return
            
        # Test regular login for comparison
        regular_login_payload = {
            "email": "user@example.com",
            "password": "User@123"
        }
        
        try:
            print("📡 Testing regular login for comparison...")
            response = requests.post(
                self.login_endpoint,
                json=regular_login_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                regular_data = response.json()
                print("✅ Regular login successful!")
                
                # Compare response structures
                print("\n🔍 RESPONSE STRUCTURE COMPARISON:")
                print("-" * 40)
                
                oauth_keys = set(self.oauth_response.keys())
                regular_keys = set(regular_data.keys())
                
                print(f"OAuth Keys: {sorted(oauth_keys)}")
                print(f"Regular Keys: {sorted(regular_keys)}")
                
                common_keys = oauth_keys & regular_keys
                oauth_only = oauth_keys - regular_keys
                regular_only = regular_keys - oauth_keys
                
                print(f"✅ Common Keys: {sorted(common_keys)}")
                if oauth_only:
                    print(f"🔵 OAuth Only: {sorted(oauth_only)}")
                if regular_only:
                    print(f"🟢 Regular Only: {sorted(regular_only)}")
                
                # Compare user object structure
                if 'user' in self.oauth_response and 'user' in regular_data:
                    oauth_user_keys = set(self.oauth_response['user'].keys())
                    regular_user_keys = set(regular_data['user'].keys())
                    
                    print(f"\n👤 USER OBJECT COMPARISON:")
                    print(f"OAuth User Keys: {sorted(oauth_user_keys)}")
                    print(f"Regular User Keys: {sorted(regular_user_keys)}")
                    
                    if oauth_user_keys == regular_user_keys:
                        print("✅ User object structures match perfectly!")
                        self.success_tests += 1
                    else:
                        print("⚠️  User object structures differ")
                        
            else:
                print(f"❌ Regular login failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Regular login test failed: {e}")
    
    def test_token_validation(self):
        """Test 4: JWT Token validation and structure"""
        print("\n🧪 TEST 4: JWT Token Validation & Structure")
        print("-" * 60)
        self.total_tests += 1
        
        if not hasattr(self, 'oauth_response'):
            print("⏭️  Skipping token validation - no OAuth response available")
            return
            
        access_token = self.oauth_response.get('access')
        refresh_token = self.oauth_response.get('refresh')
        
        if not access_token or not refresh_token:
            print("❌ No tokens found in OAuth response")
            return
            
        try:
            # Validate access token structure
            access_payload = self.decode_jwt_payload(access_token)
            refresh_payload = self.decode_jwt_payload(refresh_token)
            
            print("🔍 ACCESS TOKEN ANALYSIS:")
            print(f"   Token Type: {access_payload.get('token_type')}")
            print(f"   User ID: {access_payload.get('user_id')}")
            print(f"   Issued At: {datetime.fromtimestamp(access_payload.get('iat', 0))}")
            print(f"   Expires At: {datetime.fromtimestamp(access_payload.get('exp', 0))}")
            print(f"   JTI: {access_payload.get('jti')}")
            
            print("\n🔍 REFRESH TOKEN ANALYSIS:")
            print(f"   Token Type: {refresh_payload.get('token_type')}")
            print(f"   User ID: {refresh_payload.get('user_id')}")
            print(f"   Issued At: {datetime.fromtimestamp(refresh_payload.get('iat', 0))}")
            print(f"   Expires At: {datetime.fromtimestamp(refresh_payload.get('exp', 0))}")
            print(f"   JTI: {refresh_payload.get('jti')}")
            
            # Validate token consistency
            if (access_payload.get('user_id') == refresh_payload.get('user_id') == 
                self.oauth_response.get('user', {}).get('id')):
                print("✅ Token user IDs consistent across all tokens!")
                self.success_tests += 1
            else:
                print("❌ Token user ID inconsistency detected")
                
        except Exception as e:
            print(f"❌ Token validation failed: {e}")
    
    def test_authenticated_request(self):
        """Test 5: Using OAuth tokens for authenticated requests"""
        print("\n🧪 TEST 5: Authenticated Request with OAuth Tokens")
        print("-" * 60)
        self.total_tests += 1
        
        if not hasattr(self, 'oauth_response'):
            print("⏭️  Skipping authenticated request test - no OAuth response available")
            return
            
        access_token = self.oauth_response.get('access')
        if not access_token:
            print("❌ No access token available")
            return
            
        try:
            # Test authenticated request to a protected endpoint
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Try to access user profile or similar protected endpoint
            protected_endpoints = [
                f"{self.base_url}/accounts/profile/",
                f"{self.base_url}/accounts/user/",
                f"{self.base_url}/cart/",
            ]
            
            for endpoint in protected_endpoints:
                try:
                    print(f"📡 Testing protected endpoint: {endpoint}")
                    response = requests.get(endpoint, headers=headers, timeout=10)
                    
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        print("   ✅ Access granted with OAuth token!")
                        self.success_tests += 1
                        break
                    elif response.status_code == 401:
                        print("   ❌ Unauthorized - token not accepted")
                    elif response.status_code == 404:
                        print("   ℹ️  Endpoint not found (testing next)")
                    else:
                        print(f"   ⚠️  Unexpected status: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Request failed: {e}")
                    
        except Exception as e:
            print(f"❌ Authenticated request test failed: {e}")
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        success_rate = (self.success_tests / max(self.total_tests, 1)) * 100
        
        print("\n" + "🎉" * 80)
        print("📊 COMPREHENSIVE GOOGLE OAUTH TEST REPORT")
        print("🎉" * 80)
        
        print(f"✅ Tests Completed: {self.total_tests}")
        print(f"✅ Tests Passed: {self.success_tests}")
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉🎉🎉 EXCELLENT! OAUTH SYSTEM WORKING PERFECTLY! 🎉🎉🎉")
        elif success_rate >= 60:
            print("\n✅ GOOD! OAuth system mostly functional with minor issues")
        else:
            print("\n⚠️  NEEDS ATTENTION! Several issues detected")
            
        # Generate detailed report
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": self.total_tests,
            "passed_tests": self.success_tests,
            "success_rate": success_rate,
            "endpoints_tested": {
                "oauth_endpoint": self.oauth_endpoint,
                "login_endpoint": self.login_endpoint,
                "base_url": self.base_url
            },
            "oauth_response_sample": getattr(self, 'oauth_response', None),
            "status": "EXCELLENT" if success_rate >= 80 else "GOOD" if success_rate >= 60 else "NEEDS_REVIEW"
        }
        
        # Save detailed report
        with open("COMPREHENSIVE_OAUTH_TEST_REPORT.json", "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Detailed report saved: COMPREHENSIVE_OAUTH_TEST_REPORT.json")
        
        return report
    
    def run_comprehensive_test(self):
        """Run the complete comprehensive test suite"""
        self.print_banner()
        
        print(f"\n🚀 Starting comprehensive OAuth testing...")
        print(f"📡 Target: {self.base_url}")
        print(f"🔐 OAuth Endpoint: {self.oauth_endpoint}")
        
        # Run all tests
        self.test_oauth_endpoint_structure()
        self.test_oauth_real_authentication()
        self.test_regular_login_comparison()
        self.test_token_validation()
        self.test_authenticated_request()
        
        # Generate final report
        self.generate_comprehensive_report()
        
        print("\n" + "✅" * 80)
        print("🎯 COMPREHENSIVE TESTING COMPLETE!")
        print("📖 Check COMPREHENSIVE_OAUTH_TEST_REPORT.json for details")
        print("✅" * 80)

if __name__ == "__main__":
    tester = ComprehensiveGoogleOAuthTester()
    tester.run_comprehensive_test()