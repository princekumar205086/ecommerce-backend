#!/usr/bin/env python
"""
Comprehensive Authentication Test Suite
Tests all authentication features including:
- Registration with email verification
- OTP verification (email/SMS)
- Login/Logout with automatic token refresh
- Password reset functionality
- Change password
- Email verification flows
"""

import os
import sys
import django
import json
import time
import requests
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import OTP, PasswordResetToken
from django.core.management import call_command

User = get_user_model()

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

class AuthTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.test_user_data = {
            "email": "test@medixmall.com",
            "full_name": "Test User",
            "contact": "+919876543210",
            "password": "testpassword123",
            "password2": "testpassword123"
        }
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.access_token = None
        self.refresh_token = None
        
    def log_result(self, test_name, success, message="", error_details=""):
        """Log test results"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if message:
            print(f"   📝 {message}")
        if error_details:
            print(f"   🔍 {error_details}")
        
        if success:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append({
                "test": test_name,
                "error": error_details,
                "message": message
            })
        print()

    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            User.objects.filter(email=self.test_user_data["email"]).delete()
            OTP.objects.all().delete()
            PasswordResetToken.objects.all().delete()
            print("🧹 Test data cleaned up")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")

    def start_server(self):
        """Start Django development server"""
        print("🚀 Starting Django development server...")
        import subprocess
        import threading
        
        def run_server():
            subprocess.run(["python", "manage.py", "runserver", "127.0.0.1:8000"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(3)  # Wait for server to start
        
        # Test if server is running
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            print("✅ Django server is running")
            return True
        except:
            print("❌ Failed to start Django server")
            return False

    def test_user_registration(self):
        """Test 1: User Registration with Email Verification"""
        try:
            response = self.session.post(
                f"{API_BASE}/accounts/register/",
                json=self.test_user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                self.access_token = data.get('access')
                self.refresh_token = data.get('refresh')
                
                # Check if user was created
                user = User.objects.get(email=self.test_user_data["email"])
                if not user.email_verified:
                    self.log_result(
                        "User Registration", 
                        True, 
                        f"User registered successfully. Email verification required. Token: {user.email_verification_token[:20]}..."
                    )
                    return True
                else:
                    self.log_result("User Registration", False, "Email should not be verified immediately")
            else:
                self.log_result(
                    "User Registration", 
                    False, 
                    f"Registration failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("User Registration", False, "Registration error", str(e))
        
        return False

    def test_email_verification(self):
        """Test 2: Email Verification"""
        try:
            user = User.objects.get(email=self.test_user_data["email"])
            token = user.email_verification_token
            
            if token:
                response = self.session.get(f"{API_BASE}/accounts/verify-email/{token}/")
                
                if response.status_code == 200:
                    # Check if user is now verified
                    user.refresh_from_db()
                    if user.email_verified:
                        self.log_result("Email Verification", True, "Email verified successfully")
                        return True
                    else:
                        self.log_result("Email Verification", False, "User not marked as verified")
                else:
                    self.log_result(
                        "Email Verification", 
                        False, 
                        f"Verification failed with status {response.status_code}",
                        response.text
                    )
            else:
                self.log_result("Email Verification", False, "No verification token found")
        except Exception as e:
            self.log_result("Email Verification", False, "Verification error", str(e))
        
        return False

    def test_login(self):
        """Test 3: User Login"""
        try:
            login_data = {
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            
            response = self.session.post(
                f"{API_BASE}/accounts/login/",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access')
                self.refresh_token = data.get('refresh')
                user_data = data.get('user', {})
                
                self.log_result(
                    "User Login", 
                    True, 
                    f"Login successful. User: {user_data.get('full_name')} ({user_data.get('email')})"
                )
                return True
            else:
                self.log_result(
                    "User Login", 
                    False, 
                    f"Login failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("User Login", False, "Login error", str(e))
        
        return False

    def test_token_refresh(self):
        """Test 4: Token Refresh"""
        try:
            if not self.refresh_token:
                self.log_result("Token Refresh", False, "No refresh token available")
                return False
            
            response = self.session.post(
                f"{API_BASE}/accounts/token/refresh/",
                json={"refresh": self.refresh_token},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                new_access = data.get('access')
                new_refresh = data.get('refresh')
                user_data = data.get('user', {})
                
                if new_access and (new_refresh or self.refresh_token):
                    self.access_token = new_access
                    if new_refresh:
                        self.refresh_token = new_refresh
                    
                    self.log_result(
                        "Token Refresh", 
                        True, 
                        f"Tokens refreshed successfully. User: {user_data.get('full_name', 'N/A')}"
                    )
                    return True
                else:
                    self.log_result("Token Refresh", False, "No new tokens in response")
            else:
                self.log_result(
                    "Token Refresh", 
                    False, 
                    f"Token refresh failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Token Refresh", False, "Token refresh error", str(e))
        
        return False

    def test_profile_access(self):
        """Test 5: Authenticated Profile Access"""
        try:
            if not self.access_token:
                self.log_result("Profile Access", False, "No access token available")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(f"{API_BASE}/accounts/me/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Profile Access", 
                    True, 
                    f"Profile accessed. User: {data.get('full_name')} - Verified: {data.get('email_verified')}"
                )
                return True
            else:
                self.log_result(
                    "Profile Access", 
                    False, 
                    f"Profile access failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Profile Access", False, "Profile access error", str(e))
        
        return False

    def test_otp_request_email(self):
        """Test 6: OTP Request via Email"""
        try:
            otp_data = {
                "otp_type": "email_verification",
                "email": self.test_user_data["email"]
            }
            
            response = self.session.post(
                f"{API_BASE}/accounts/otp/request/",
                json=otp_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                otp_id = data.get('otp_id')
                
                # Verify OTP was created in database
                if otp_id:
                    otp = OTP.objects.get(id=otp_id)
                    self.log_result(
                        "OTP Request (Email)", 
                        True, 
                        f"OTP sent successfully. Code: {otp.otp_code} (for testing)"
                    )
                    return True, otp.otp_code
                else:
                    self.log_result("OTP Request (Email)", False, "No OTP ID in response")
            else:
                self.log_result(
                    "OTP Request (Email)", 
                    False, 
                    f"OTP request failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("OTP Request (Email)", False, "OTP request error", str(e))
        
        return False, None

    def test_otp_verification(self, otp_code):
        """Test 7: OTP Verification"""
        try:
            if not otp_code:
                self.log_result("OTP Verification", False, "No OTP code to verify")
                return False
            
            verify_data = {
                "otp_code": otp_code,
                "otp_type": "email_verification",
                "email": self.test_user_data["email"]
            }
            
            response = self.session.post(
                f"{API_BASE}/accounts/otp/verify/",
                json=verify_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('verified'):
                    self.log_result("OTP Verification", True, "OTP verified successfully")
                    return True
                else:
                    self.log_result("OTP Verification", False, data.get('error', 'Verification failed'))
            else:
                self.log_result(
                    "OTP Verification", 
                    False, 
                    f"OTP verification failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("OTP Verification", False, "OTP verification error", str(e))
        
        return False

    def test_password_reset_request(self):
        """Test 8: Password Reset Request"""
        try:
            reset_data = {
                "email": self.test_user_data["email"]
            }
            
            response = self.session.post(
                f"{API_BASE}/accounts/password/reset-request/",
                json=reset_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Check if reset token was created
                reset_token = PasswordResetToken.objects.filter(
                    user__email=self.test_user_data["email"]
                ).first()
                
                if reset_token and reset_token.is_valid():
                    self.log_result(
                        "Password Reset Request", 
                        True, 
                        f"Reset email sent. Token: {reset_token.token[:20]}..."
                    )
                    return True, reset_token.token
                else:
                    self.log_result("Password Reset Request", False, "No valid reset token created")
            else:
                self.log_result(
                    "Password Reset Request", 
                    False, 
                    f"Reset request failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Password Reset Request", False, "Reset request error", str(e))
        
        return False, None

    def test_password_reset_confirm(self, reset_token):
        """Test 9: Password Reset Confirmation"""
        try:
            if not reset_token:
                self.log_result("Password Reset Confirm", False, "No reset token to test")
                return False
            
            new_password = "newpassword123"
            confirm_data = {
                "token": reset_token,
                "new_password": new_password,
                "confirm_password": new_password
            }
            
            response = self.session.post(
                f"{API_BASE}/accounts/password/reset-confirm/",
                json=confirm_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Test login with new password
                login_data = {
                    "email": self.test_user_data["email"],
                    "password": new_password
                }
                
                login_response = self.session.post(
                    f"{API_BASE}/accounts/login/",
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    data = login_response.json()
                    self.access_token = data.get('access')
                    self.refresh_token = data.get('refresh')
                    
                    self.log_result(
                        "Password Reset Confirm", 
                        True, 
                        "Password reset successful and login works with new password"
                    )
                    # Update test data for future tests
                    self.test_user_data["password"] = new_password
                    return True
                else:
                    self.log_result("Password Reset Confirm", False, "Password reset successful but login failed")
            else:
                self.log_result(
                    "Password Reset Confirm", 
                    False, 
                    f"Password reset failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Password Reset Confirm", False, "Password reset confirm error", str(e))
        
        return False

    def test_change_password(self):
        """Test 10: Change Password"""
        try:
            if not self.access_token:
                self.log_result("Change Password", False, "No access token available")
                return False
            
            new_password = "changedpassword123"
            change_data = {
                "old_password": self.test_user_data["password"],
                "new_password": new_password,
                "confirm_password": new_password
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.post(
                f"{API_BASE}/accounts/password/change/",
                json=change_data,
                headers=headers
            )
            
            if response.status_code == 200:
                # Test login with new password
                login_data = {
                    "email": self.test_user_data["email"],
                    "password": new_password
                }
                
                login_response = self.session.post(
                    f"{API_BASE}/accounts/login/",
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    self.log_result(
                        "Change Password", 
                        True, 
                        "Password changed successfully and login works with new password"
                    )
                    self.test_user_data["password"] = new_password
                    return True
                else:
                    self.log_result("Change Password", False, "Password change successful but login failed")
            else:
                self.log_result(
                    "Change Password", 
                    False, 
                    f"Password change failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("Change Password", False, "Change password error", str(e))
        
        return False

    def test_logout(self):
        """Test 11: User Logout"""
        try:
            if not self.refresh_token:
                self.log_result("User Logout", False, "No refresh token available")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            logout_data = {
                "refresh_token": self.refresh_token
            }
            
            response = self.session.post(
                f"{API_BASE}/accounts/logout/",
                json=logout_data,
                headers=headers
            )
            
            if response.status_code == 205:
                # Try to use the blacklisted token
                refresh_response = self.session.post(
                    f"{API_BASE}/accounts/token/refresh/",
                    json={"refresh": self.refresh_token},
                    headers={"Content-Type": "application/json"}
                )
                
                if refresh_response.status_code != 200:
                    self.log_result("User Logout", True, "Logout successful and token blacklisted")
                    return True
                else:
                    self.log_result("User Logout", False, "Logout successful but token not blacklisted")
            else:
                self.log_result(
                    "User Logout", 
                    False, 
                    f"Logout failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_result("User Logout", False, "Logout error", str(e))
        
        return False

    def test_resend_verification(self):
        """Test 12: Resend Email Verification"""
        try:
            # Create a new unverified user for this test
            test_email = "resend@medixmall.com"
            
            # First register a new user
            register_data = {
                "email": test_email,
                "full_name": "Resend Test User",
                "contact": "+919876543211",
                "password": "testpassword123",
                "password2": "testpassword123"
            }
            
            register_response = self.session.post(
                f"{API_BASE}/accounts/register/",
                json=register_data,
                headers={"Content-Type": "application/json"}
            )
            
            if register_response.status_code == 201:
                # Now test resend verification
                resend_data = {"email": test_email}
                
                response = self.session.post(
                    f"{API_BASE}/accounts/resend-verification/",
                    json=resend_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    self.log_result(
                        "Resend Verification", 
                        True, 
                        "Verification email resent successfully"
                    )
                    # Cleanup
                    User.objects.filter(email=test_email).delete()
                    return True
                else:
                    self.log_result(
                        "Resend Verification", 
                        False, 
                        f"Resend verification failed with status {response.status_code}",
                        response.text
                    )
            else:
                self.log_result("Resend Verification", False, "Could not create test user for resend test")
        except Exception as e:
            self.log_result("Resend Verification", False, "Resend verification error", str(e))
        
        return False

    def run_all_tests(self):
        """Run comprehensive authentication test suite"""
        print("🔐 COMPREHENSIVE AUTHENTICATION TEST SUITE")
        print("=" * 50)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Start server
        if not self.start_server():
            print("❌ Could not start server. Exiting.")
            return
        
        # Cleanup before tests
        self.cleanup_test_data()
        
        print("🧪 Running Authentication Tests...")
        print()
        
        # Test sequence
        tests_passed = 0
        
        # 1. Registration
        if self.test_user_registration():
            tests_passed += 1
            
            # 2. Email Verification
            if self.test_email_verification():
                tests_passed += 1
                
                # 3. Login
                if self.test_login():
                    tests_passed += 1
                    
                    # 4. Token Refresh
                    if self.test_token_refresh():
                        tests_passed += 1
                    
                    # 5. Profile Access
                    if self.test_profile_access():
                        tests_passed += 1
                    
                    # 6-7. OTP Flow
                    otp_success, otp_code = self.test_otp_request_email()
                    if otp_success:
                        tests_passed += 1
                        if self.test_otp_verification(otp_code):
                            tests_passed += 1
                    
                    # 8-9. Password Reset Flow
                    reset_success, reset_token = self.test_password_reset_request()
                    if reset_success:
                        tests_passed += 1
                        if self.test_password_reset_confirm(reset_token):
                            tests_passed += 1
                    
                    # 10. Change Password
                    if self.test_change_password():
                        tests_passed += 1
                    
                    # 11. Logout
                    if self.test_logout():
                        tests_passed += 1
        
        # 12. Resend Verification (independent test)
        if self.test_resend_verification():
            tests_passed += 1
        
        # Final cleanup
        self.cleanup_test_data()
        
        # Print results
        print("=" * 50)
        print("📊 FINAL TEST RESULTS")
        print("=" * 50)
        print(f"✅ Tests Passed: {self.test_results['passed']}")
        print(f"❌ Tests Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   ❌ {error['test']}: {error['message']}")
        
        print(f"\n📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Return success if all critical tests passed
        return self.test_results['failed'] == 0

if __name__ == "__main__":
    test_suite = AuthTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Authentication system is working perfectly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  Some tests failed. Check the results above.")
        sys.exit(1)
