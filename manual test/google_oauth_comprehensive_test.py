"""
Google OAuth Test for Accounts App
Tests the Google OAuth implementation with real tokens and comprehensive validation
"""

import os
import requests
import json
from datetime import datetime
import base64

# Configuration
BASE_URL = "https://backend.okpuja.in"  # Production URL
LOCAL_URL = "http://127.0.0.1:8000"  # Local URL for testing

class GoogleOAuthTester:
    def __init__(self, use_production=True):
        self.base_url = BASE_URL if use_production else LOCAL_URL
        self.test_results = []
        
    def log_result(self, test_name, status, details, response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"✓ {test_name}: {status}")
        if details:
            print(f"  Details: {details}")
        
    def decode_jwt_payload(self, token):
        """Decode JWT payload without verification"""
        try:
            # Split the token
            parts = token.split('.')
            if len(parts) != 3:
                return None
                
            # Decode the payload (second part)
            payload = parts[1]
            # Add padding if needed
            padding = len(payload) % 4
            if padding:
                payload += '=' * (4 - padding)
                
            decoded_bytes = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded_bytes.decode('utf-8'))
            return payload_data
        except Exception as e:
            print(f"Error decoding JWT: {e}")
            return None
    
    def analyze_token(self, token):
        """Analyze the Google ID token"""
        print("\n" + "="*60)
        print("GOOGLE ID TOKEN ANALYSIS")
        print("="*60)
        
        payload = self.decode_jwt_payload(token)
        if payload:
            print(f"Issuer (iss): {payload.get('iss', 'Not found')}")
            print(f"Audience (aud): {payload.get('aud', 'Not found')}")
            print(f"Subject (sub): {payload.get('sub', 'Not found')}")
            print(f"Email: {payload.get('email', 'Not found')}")
            print(f"Email Verified: {payload.get('email_verified', 'Not found')}")
            print(f"Name: {payload.get('name', 'Not found')}")
            print(f"Issued At (iat): {payload.get('iat', 'Not found')}")
            print(f"Expires At (exp): {payload.get('exp', 'Not found')}")
            print(f"Not Before (nbf): {payload.get('nbf', 'Not found')}")
            print(f"JWT ID (jti): {payload.get('jti', 'Not found')}")
            
            # Check if token is expired
            import time
            current_time = int(time.time())
            exp_time = payload.get('exp', 0)
            if exp_time and current_time > exp_time:
                print("⚠️  TOKEN IS EXPIRED!")
            else:
                print("✓ Token is not expired")
                
            return payload
        return None
    
    def test_google_oauth_endpoint(self, id_token, role="user"):
        """Test the Google OAuth endpoint"""
        print(f"\n{'='*60}")
        print("TESTING GOOGLE OAUTH ENDPOINT")
        print("="*60)
        
        url = f"{self.base_url}/api/accounts/login/google/"
        data = {
            "id_token": id_token,
            "role": role
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            print(f"Making request to: {url}")
            print(f"Payload: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"Response Data: {json.dumps(response_data, indent=2)}")
            except:
                response_data = {"raw_response": response.text}
                print(f"Raw Response: {response.text}")
            
            # Log the result
            if response.status_code == 200:
                self.log_result(
                    "Google OAuth Login", 
                    "SUCCESS", 
                    "Login successful with Google OAuth",
                    response_data
                )
            elif response.status_code == 400:
                self.log_result(
                    "Google OAuth Login", 
                    "EXPECTED_FAILURE", 
                    f"Expected validation error: {response_data.get('error', 'Unknown error')}",
                    response_data
                )
            else:
                self.log_result(
                    "Google OAuth Login", 
                    "FAILURE", 
                    f"Unexpected error: {response_data.get('error', 'Unknown error')}",
                    response_data
                )
                
            return response_data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.log_result("Google OAuth Login", "FAILURE", error_msg)
            return {"error": error_msg}
    
    def test_invalid_token(self):
        """Test with invalid token"""
        print(f"\n{'='*60}")
        print("TESTING INVALID TOKEN")
        print("="*60)
        
        invalid_token = "invalid.token.here"
        return self.test_google_oauth_endpoint(invalid_token)
    
    def test_expired_token(self):
        """Test with an expired token"""
        print(f"\n{'='*60}")
        print("TESTING EXPIRED TOKEN")
        print("="*60)
        
        # This is an intentionally expired token for testing
        expired_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE3ZjBmMGYxNGU5Y2FmYTlhYjUxODAxNTBhZTcxNGM5ZmQxYjVjMjYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXpwIjoiNjE4MTA0NzA4MDU0LTlyOXMxYzRhbGczNmVybGl1Y2hvOXQ1Mm4zMm42ZGdxLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwiYXVkIjoiNjE4MTA0NzA4MDU0LTlyOXMxYzRhbGczNmVybGl1Y2hvOXQ1Mm4zMm42ZGdxLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwic3ViIjoiMTAyNjMxOTg5NDk0NjA2MjQzMTQxIiwiZW1haWwiOiJtZWRpeG1hbGxzdG9yZUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXRfaGFzaCI6ImhmYXp0Nk1hZWxWUUN2S1JYd0RqQWciLCJuYmYiOjE3NTk1MjI3MzksImlhdCI6MTc1OTUyMzAzOSwiZXhwIjoxNzU5NTI2NjM5LCJqdGkiOiJiZGFkMDJhYzQ2MzE2OTJkNDQxMGUyYzFjMjE4ZjRhNTUwNmFlZTIzIn0.i5LjiC3-Fs_dEa4t6vS2O8JEyFNJk8lYKozYPUFT4gLIr-DZXhZdkXxlk0C1117A2nYgq-39ijdgciXpQKNCXU7e0RnbPl1qoZ3Bdn7HQUjZq5Hxsj--EZFG8rRy_lPhuS2SxG9wtCPIsn5-tlczstAKFtBiDrOBC0E4DaCDn5X5dpHTTnXzwMT3D3bJ_Sas47Z34gsXxHHD2KzMsHfRr-b9P8dcfnMNl8TAoPaTeRv2qaevv801COMEgxFnORBsit9uKJfr1vwO_lRZwnIJmzMRwXOImuiJR1Sq5wkxfbhE4J8n4uVa_dGO3_wZ82WXPclQ_IaCK_Y9jtdyLlgmCQ"
        
        # Analyze the token first
        self.analyze_token(expired_token)
        
        return self.test_google_oauth_endpoint(expired_token)
    
    def test_different_roles(self, id_token):
        """Test different user roles"""
        roles = ["user", "supplier"]
        for role in roles:
            print(f"\n{'='*60}")
            print(f"TESTING ROLE: {role.upper()}")
            print("="*60)
            self.test_google_oauth_endpoint(id_token, role)
    
    def save_results(self, filename="google_oauth_test_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump({
                "test_timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "total_tests": len(self.test_results),
                "results": self.test_results
            }, f, indent=2)
        print(f"\n📊 Test results saved to {filename}")
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print("="*60)
        
        success_count = len([r for r in self.test_results if r["status"] == "SUCCESS"])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {success_count}")
        print(f"Failed: {total_tests - success_count}")
        print(f"Success Rate: {(success_count/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")

def main():
    """Main test function"""
    print("🚀 Starting Google OAuth Tests for MedixMall")
    print("="*60)
    
    # The token from the user's request
    user_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE3ZjBmMGYxNGU5Y2FmYTlhYjUxODAxNTBhZTcxNGM5ZmQxYjVjMjYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXpwIjoiNjE4MTA0NzA4MDU0LTlyOXMxYzRhbGczNmVybGl1Y2hvOXQ1Mm4zMm42ZGdxLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwiYXVkIjoiNjE4MTA0NzA4MDU0LTlyOXMxYzRhbGczNmVybGl1Y2hvOXQ1Mm4zMm42ZGdxLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwic3ViIjoiMTAyNjMxOTg5NDk0NjA2MjQzMTQxIiwiZW1haWwiOiJtZWRpeG1hbGxzdG9yZUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXRfaGFzaCI6ImhmYXp0Nk1hZWxWUUN2S1JYd0RqQWciLCJuYmYiOjE3NTk1MjI3MzksImlhdCI6MTc1OTUyMzAzOSwiZXhwIjoxNzU5NTI2NjM5LCJqdGkiOiJiZGFkMDJhYzQ2MzE2OTJkNDQxMGUyYzFjMjE4ZjRhNTUwNmFlZTIzIn0.i5LjiC3-Fs_dEa4t6vS2O8JEyFNJk8lYKozYPUFT4gLIr-DZXhZdkXxlk0C1117A2nYgq-39ijdgciXpQKNCXU7e0RnbPl1qoZ3Bdn7HQUjZq5Hxsj--EZFG8rRy_lPhuS2SxG9wtCPIsn5-tlczstAKFtBiDrOBC0E4DaCDn5X5dpHTTnXzwMT3D3bJ_Sas47Z34gsXxHHD2KzMsHfRr-b9P8dcfnMNl8TAoPaTeRv2qaevv801COMEgxFnORBsit9uKJfr1vwO_lRZwnIJmzMRwXOImuiJR1Sq5wkxfbhE4J8n4uVa_dGO3_wZ82WXPclQ_IaCK_Y9jtdyLlgmCQ"
    
    # Test with production server
    tester = GoogleOAuthTester(use_production=True)
    
    # Analyze the token first
    tester.analyze_token(user_token)
    
    # Test the specific token from user
    tester.test_google_oauth_endpoint(user_token)
    
    # Test different roles
    tester.test_different_roles(user_token)
    
    # Test invalid token
    tester.test_invalid_token()
    
    # Print summary and save results
    tester.print_summary()
    tester.save_results("google_oauth_comprehensive_test.json")
    
    # Also test local server if it's running
    print(f"\n{'='*60}")
    print("TESTING LOCAL SERVER (if available)")
    print("="*60)
    
    local_tester = GoogleOAuthTester(use_production=False)
    try:
        local_tester.test_google_oauth_endpoint(user_token)
        local_tester.save_results("google_oauth_local_test.json")
    except Exception as e:
        print(f"❌ Local server test failed: {e}")

if __name__ == "__main__":
    main()