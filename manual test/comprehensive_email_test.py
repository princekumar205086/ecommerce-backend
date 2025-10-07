#!/usr/bin/env python3
"""
Comprehensive Email and OTP Test Script
Tests complete authentication flow with real email sending
"""
import os
import sys
import django
import requests
import json
import time
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from accounts.models import User, OTP

class EmailOTPTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000/api/accounts"
        self.test_email = "princekumar205086@gmail.com"
        self.test_password = "Test123!@#"
        self.session = requests.Session()
        self.otp_code = None  # Initialize otp_code
        
    def print_banner(self, title):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def print_step(self, step, description):
        print(f"\n🔹 Step {step}: {description}")
        
    def print_success(self, message):
        print(f"✅ {message}")
        
    def print_error(self, message):
        print(f"❌ {message}")
        
    def print_info(self, message):
        print(f"ℹ️  {message}")
        
    def check_email_config(self):
        """Check if email configuration is properly set"""
        self.print_step(1, "Checking Email Configuration")
        
        required_vars = ['EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.print_error(f"Missing environment variables: {', '.join(missing_vars)}")
            return False
        
        self.print_success("Email configuration is properly set")
        self.print_info(f"Email Host User: {os.environ.get('EMAIL_HOST_USER')}")
        return True
        
    def test_direct_email_sending(self):
        """Test direct email sending using Django's send_mail"""
        self.print_step(2, "Testing Direct Email Sending")
        
        try:
            result = send_mail(
                subject='Test Email from Django',
                message='This is a test email sent directly from Django to verify SMTP configuration.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.test_email],
                fail_silently=False,
            )
            
            if result == 1:
                self.print_success("Direct email sent successfully")
                return True
            else:
                self.print_error("Failed to send direct email")
                return False
                
        except Exception as e:
            self.print_error(f"Direct email sending failed: {str(e)}")
            return False
    
    def cleanup_existing_user(self):
        """Clean up existing test user and OTPs"""
        self.print_step(3, "Cleaning up existing test data")
        
        try:
            # Delete existing user and related OTPs
            User.objects.filter(email=self.test_email).delete()
            self.print_success("Existing test data cleaned up")
        except Exception as e:
            self.print_info(f"No existing data to cleanup: {str(e)}")
    
    def test_user_registration(self):
        """Test user registration with email sending"""
        self.print_step(4, "Testing User Registration")
        
        registration_data = {
            "email": self.test_email,
            "password": self.test_password,
            "password2": self.test_password,  # Fixed: Use password2 instead of confirm_password
            "full_name": "Test User",
            "contact": "1234567890"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/register/",
                json=registration_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                data = response.json()
                self.print_success("User registration successful")
                self.print_info(f"User ID: {data['user']['id']}")
                self.print_info(f"Message: {data['message']}")
                
                # Store tokens for later use
                self.access_token = data['access']
                self.refresh_token = data['refresh']
                return True
            else:
                self.print_error(f"Registration failed: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Registration request failed: {str(e)}")
            return False
    
    def check_otp_created(self):
        """Check if OTP was created in database"""
        self.print_step(5, "Checking OTP Creation in Database")
        
        try:
            user = User.objects.get(email=self.test_email)
            otp = OTP.objects.filter(
                user=user,
                otp_type='email_verification'
            ).order_by('-created_at').first()
            
            if otp:
                self.print_success("OTP created successfully in database")
                self.print_info(f"OTP Code: {otp.otp_code}")
                self.print_info(f"Created: {otp.created_at}")
                self.print_info(f"Expires: {otp.expires_at}")
                self.print_info(f"Email: {otp.email}")
                self.otp_code = otp.otp_code
                return True
            else:
                self.print_error("No OTP found in database")
                return False
                
        except Exception as e:
            self.print_error(f"Error checking OTP: {str(e)}")
            return False
    
    def test_otp_resend_too_early(self):
        """Test OTP resend before 1 minute cooldown"""
        self.print_step(6, "Testing OTP Resend (Too Early - Should Fail)")
        
        resend_data = {
            "email": self.test_email,
            "otp_type": "email_verification"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/otp/resend/",
                json=resend_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 400:
                data = response.json()
                self.print_success("Resend correctly blocked (too early)")
                self.print_info(f"Error message: {data.get('error', 'No error message')}")
                return True
            else:
                self.print_error(f"Unexpected response: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Resend request failed: {str(e)}")
            return False
    
    def wait_for_resend_cooldown(self):
        """Wait for 1 minute cooldown period"""
        self.print_step(7, "Waiting for Resend Cooldown (60 seconds)")
        
        for i in range(60, 0, -1):
            print(f"\r⏳ Waiting {i} seconds for cooldown...", end="", flush=True)
            time.sleep(1)
        
        print("\n✅ Cooldown period completed")
    
    def test_otp_resend_after_cooldown(self):
        """Test OTP resend after 1 minute cooldown"""
        self.print_step(8, "Testing OTP Resend (After Cooldown - Should Succeed)")
        
        resend_data = {
            "email": self.test_email,
            "otp_type": "email_verification"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/otp/resend/",
                json=resend_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("OTP resent successfully")
                self.print_info(f"Message: {data.get('message', 'No message')}")
                self.print_info(f"Cooldown: {data.get('can_resend_after', 'Not specified')}")
                
                # Get new OTP code from database
                user = User.objects.get(email=self.test_email)
                new_otp = OTP.objects.filter(
                    user=user,
                    otp_type='email_verification'
                ).order_by('-created_at').first()
                
                if new_otp:
                    self.print_info(f"New OTP Code: {new_otp.otp_code}")
                    self.otp_code = new_otp.otp_code
                
                return True
            else:
                self.print_error(f"Resend failed: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Resend request failed: {str(e)}")
            return False
    
    def test_otp_verification(self):
        """Test OTP verification"""
        self.print_step(9, "Testing OTP Verification")
        
        if not hasattr(self, 'otp_code') or not self.otp_code:
            self.print_error("No OTP code available for verification")
            return False
        
        verification_data = {
            "email": self.test_email,
            "otp_code": self.otp_code,
            "otp_type": "email_verification"  # Added required field
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/verify-email/",
                json=verification_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("Email verification successful")
                self.print_info(f"Message: {data.get('message', 'No message')}")
                return True
            else:
                self.print_error(f"Verification failed: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Verification request failed: {str(e)}")
            return False
    
    def test_login_after_verification(self):
        """Test login after email verification"""
        self.print_step(10, "Testing Login After Verification")
        
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/login/",
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("Login successful after verification")
                self.print_info(f"User: {data['user']['email']}")
                self.print_info(f"Email Verified: {data['user']['email_verified']}")
                return True
            else:
                self.print_error(f"Login failed: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Login request failed: {str(e)}")
            return False
    
    def test_resend_after_verification(self):
        """Test that resend is blocked after verification"""
        self.print_step(11, "Testing Resend After Verification (Should Fail)")
        
        resend_data = {
            "email": self.test_email,
            "otp_type": "email_verification"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/otp/resend/",
                json=resend_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 400:
                data = response.json()
                self.print_success("Resend correctly blocked (already verified)")
                self.print_info(f"Error message: {data.get('error', 'No error message')}")
                return True
            else:
                self.print_error(f"Unexpected response: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Resend request failed: {str(e)}")
            return False
    
    def run_complete_test(self):
        """Run the complete test suite"""
        self.print_banner("COMPREHENSIVE EMAIL & OTP TEST SUITE")
        
        test_results = []
        
        # Run all tests
        tests = [
            ("Email Configuration Check", self.check_email_config),
            ("Direct Email Sending", self.test_direct_email_sending),
            ("Cleanup Existing Data", lambda: (self.cleanup_existing_user(), True)[1]),
            ("User Registration", self.test_user_registration),
            ("OTP Database Creation", self.check_otp_created),
            ("OTP Resend Too Early", self.test_otp_resend_too_early),
            ("Cooldown Wait", lambda: (self.wait_for_resend_cooldown(), True)[1]),
            ("OTP Resend After Cooldown", self.test_otp_resend_after_cooldown),
            ("OTP Verification", self.test_otp_verification),
            ("Login After Verification", self.test_login_after_verification),
            ("Resend After Verification", self.test_resend_after_verification)
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results.append((test_name, result))
            except Exception as e:
                self.print_error(f"Test '{test_name}' crashed: {str(e)}")
                test_results.append((test_name, False))
        
        # Print summary
        self.print_banner("TEST RESULTS SUMMARY")
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
        
        print(f"\n📊 Overall Results: {passed}/{total} tests passed")
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            self.print_success("🎉 ALL TESTS PASSED! Email and OTP system is fully functional.")
        else:
            self.print_error(f"⚠️ Some tests failed. Please check the configuration and logs.")
        
        return success_rate == 100

def main():
    tester = EmailOTPTester()
    
    print("🚀 Starting Comprehensive Email & OTP Test Suite...")
    print(f"📧 Test Email: {tester.test_email}")
    print(f"🌐 Base URL: {tester.base_url}")
    
    success = tester.run_complete_test()
    
    if success:
        print("\n🎊 COMPREHENSIVE TEST COMPLETED SUCCESSFULLY!")
        print("✅ Email sending is working")
        print("✅ OTP generation and verification is working")
        print("✅ OTP resend with 1-minute cooldown is working")
        print("✅ Complete authentication flow is working")
    else:
        print("\n⚠️ SOME TESTS FAILED - Please check the logs above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
