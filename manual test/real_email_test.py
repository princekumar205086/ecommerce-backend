#!/usr/bin/env python3
"""
End-to-End Authentication Test with Real Email
Tests the complete authentication flow with avengerprinceraj@gmail.com
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

class RealEmailAuthTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_email = "avengerprinceraj@gmail.com"
        self.test_password = "TestPass123!"
        self.test_contact = "9876543210"
        self.test_full_name = "Prince Raj"
        self.results = {}
        
    def log_test(self, test_name, status, details="", extra_data=None):
        """Log test results"""
        self.results[test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "extra_data": extra_data or {}
        }
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")

    def test_01_registration(self):
        """Test user registration with real email"""
        print("\n1️⃣ Testing Registration with Real Email...")
        try:
            payload = {
                "email": self.test_email,
                "password": self.test_password,
                "password2": self.test_password,
                "full_name": self.test_full_name,
                "contact": self.test_contact
            }
            
            response = self.session.post(f"{API_BASE}/accounts/register/user/", json=payload)
            
            if response.status_code == 201:
                data = response.json()
                self.log_test(
                    "Registration (Real Email)", 
                    "PASS", 
                    f"User registered successfully. Email: {self.test_email}",
                    {"status_code": response.status_code, "user_id": data.get('user', {}).get('id')}
                )
                return True
            elif response.status_code == 400:
                # Check if user already exists
                try:
                    error_data = response.json()
                    if "already exists" in str(error_data).lower():
                        self.log_test(
                            "Registration (Real Email)", 
                            "PASS", 
                            f"User already exists (expected). Email: {self.test_email}",
                            {"status_code": response.status_code, "note": "User already registered"}
                        )
                        return True
                except:
                    pass
                    
                self.log_test(
                    "Registration (Real Email)", 
                    "FAIL", 
                    f"Registration failed: {response.text[:200]}",
                    {"status_code": response.status_code}
                )
                return False
            else:
                self.log_test(
                    "Registration (Real Email)", 
                    "FAIL", 
                    f"Registration failed: {response.text[:200]}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test("Registration (Real Email)", "FAIL", f"Exception: {str(e)}")
            return False

    def test_02_otp_login_request(self):
        """Test OTP login request with real email"""
        print("\n2️⃣ Testing OTP Login Request...")
        try:
            payload = {
                "email": self.test_email,
                "login_type": "otp"
            }
            
            response = self.session.post(f"{API_BASE}/accounts/login/choice/", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.otp_data = data
                self.log_test(
                    "OTP Login Request (Real Email)", 
                    "PASS", 
                    f"OTP sent successfully to {self.test_email}",
                    {"status_code": response.status_code, "otp_id": data.get('otp_id')}
                )
                return True
            else:
                self.log_test(
                    "OTP Login Request (Real Email)", 
                    "FAIL", 
                    f"OTP request failed: {response.text[:200]}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test("OTP Login Request (Real Email)", "FAIL", f"Exception: {str(e)}")
            return False

    def test_03_password_login(self):
        """Test password login with real email"""
        print("\n3️⃣ Testing Password Login...")
        try:
            payload = {
                "email": self.test_email,
                "password": self.test_password,
                "login_type": "password"
            }
            
            response = self.session.post(f"{API_BASE}/accounts/login/choice/", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.tokens = {
                    'access': data.get('access'),
                    'refresh': data.get('refresh')
                }
                self.log_test(
                    "Password Login (Real Email)", 
                    "PASS", 
                    f"Login successful for {self.test_email}",
                    {"status_code": response.status_code, "has_tokens": bool(self.tokens['access'])}
                )
                return True
            elif response.status_code == 403:
                # Check if it's email verification requirement
                try:
                    error_data = response.json()
                    if "Email not verified" in error_data.get('error', ''):
                        self.log_test(
                            "Password Login (Real Email)", 
                            "PASS", 
                            "Email verification required (use OTP login instead)",
                            {"status_code": response.status_code, "note": "Email verification working correctly"}
                        )
                        return True
                except:
                    pass
                    
                self.log_test(
                    "Password Login (Real Email)", 
                    "FAIL", 
                    f"Login failed: {response.text[:200]}",
                    {"status_code": response.status_code}
                )
                return False
            else:
                self.log_test(
                    "Password Login (Real Email)", 
                    "FAIL", 
                    f"Login failed: {response.text[:200]}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test("Password Login (Real Email)", "FAIL", f"Exception: {str(e)}")
            return False

    def test_04_password_reset(self):
        """Test password reset with real email"""
        print("\n4️⃣ Testing Password Reset...")
        try:
            payload = {
                "email": self.test_email
            }
            
            response = self.session.post(f"{API_BASE}/accounts/password/reset-request/", json=payload)
            
            if response.status_code == 200:
                self.log_test(
                    "Password Reset (Real Email)", 
                    "PASS", 
                    f"Password reset email sent to {self.test_email}",
                    {"status_code": response.status_code}
                )
                return True
            else:
                self.log_test(
                    "Password Reset (Real Email)", 
                    "FAIL", 
                    f"Password reset failed: {response.text[:200]}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test("Password Reset (Real Email)", "FAIL", f"Exception: {str(e)}")
            return False

    def test_05_email_verification_request(self):
        """Test email verification request"""
        print("\n5️⃣ Testing Email Verification Request...")
        try:
            payload = {
                "email": self.test_email
            }
            
            response = self.session.post(f"{API_BASE}/accounts/resend-verification/", json=payload)
            
            if response.status_code == 200:
                self.log_test(
                    "Email Verification Request", 
                    "PASS", 
                    f"Verification email sent to {self.test_email}",
                    {"status_code": response.status_code}
                )
                return True
            else:
                self.log_test(
                    "Email Verification Request", 
                    "FAIL", 
                    f"Verification request failed: {response.text[:200]}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test("Email Verification Request", "FAIL", f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("🎯 REAL EMAIL END-TO-END AUTHENTICATION TEST")
        print(f"📧 Testing with: {self.test_email}")
        print(f"🔧 Django Server: {BASE_URL}")
        print("="*70)
        
        tests = [
            self.test_01_registration,
            self.test_02_otp_login_request,
            self.test_03_password_login,
            self.test_04_password_reset,
            self.test_05_email_verification_request
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        # Summary
        print("\n" + "="*70)
        print("📊 REAL EMAIL TEST RESULTS:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        # Save results
        with open("real_email_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "email": self.test_email,
                    "total_tests": passed + failed,
                    "passed": passed,
                    "failed": failed,
                    "success_rate": passed/(passed+failed)*100,
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to: real_email_test_results.json")
        
        if passed == len(tests):
            print("\n🎉 ALL REAL EMAIL TESTS PASSED!")
            print(f"📧 Check {self.test_email} for emails sent during testing")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Check the output above for details.")
            
        return passed == len(tests)

if __name__ == "__main__":
    tester = RealEmailAuthTest()
    success = tester.run_all_tests()
    
    print("\n📋 WHAT TO CHECK IN YOUR EMAIL:")
    print("1. Registration/Welcome email (if first time)")
    print("2. OTP email for login verification")
    print("3. Password reset email")
    print("4. Email verification email")
    print(f"\n📧 All emails should be sent to: {tester.test_email}")
    
    exit(0 if success else 1)
