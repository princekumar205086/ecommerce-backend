#!/usr/bin/env python3
"""
Production Email Debug Script
Identifies and fixes common production email issues
"""
import os
import sys
import django
import requests
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from accounts.models import User, OTP

class ProductionEmailDebugger:
    def __init__(self):
        self.issues = []
        self.fixes = []
        
    def print_banner(self, title):
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
        
    def print_step(self, step, description):
        print(f"\n🔍 Step {step}: {description}")
        
    def print_success(self, message):
        print(f"✅ {message}")
        
    def print_error(self, message):
        print(f"❌ {message}")
        self.issues.append(message)
        
    def print_warning(self, message):
        print(f"⚠️  {message}")
        
    def print_info(self, message):
        print(f"ℹ️  {message}")
        
    def print_fix(self, message):
        print(f"🔧 {message}")
        self.fixes.append(message)

    def check_environment_variables(self):
        """Check if all required environment variables are set"""
        self.print_step(1, "Checking Environment Variables")
        
        required_vars = {
            'EMAIL_HOST_USER': 'Gmail account email',
            'EMAIL_HOST_PASSWORD': 'Gmail app password',
            'DEFAULT_FROM_EMAIL': 'From email address'
        }
        
        all_good = True
        for var, description in required_vars.items():
            value = os.environ.get(var)
            if not value:
                self.print_error(f"Missing {var} ({description})")
                all_good = False
            else:
                self.print_success(f"{var}: {value}")
        
        if not all_good:
            self.print_fix("Set missing environment variables in production")
        
        return all_good
    
    def check_django_email_settings(self):
        """Check Django email settings"""
        self.print_step(2, "Checking Django Email Settings")
        
        try:
            self.print_info(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
            self.print_info(f"EMAIL_HOST: {settings.EMAIL_HOST}")
            self.print_info(f"EMAIL_PORT: {settings.EMAIL_PORT}")
            self.print_info(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
            self.print_info(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
            self.print_info(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
            
            # Check if password is set (without revealing it)
            if hasattr(settings, 'EMAIL_HOST_PASSWORD') and settings.EMAIL_HOST_PASSWORD:
                self.print_success("EMAIL_HOST_PASSWORD is set")
            else:
                self.print_error("EMAIL_HOST_PASSWORD is not set")
                
            return True
        except Exception as e:
            self.print_error(f"Error checking Django settings: {str(e)}")
            return False
    
    def test_smtp_connection(self):
        """Test direct SMTP connection"""
        self.print_step(3, "Testing SMTP Connection")
        
        try:
            backend = EmailBackend(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
            )
            
            connection = backend.open()
            if connection:
                self.print_success("SMTP connection successful")
                backend.close()
                return True
            else:
                self.print_error("SMTP connection failed")
                return False
                
        except Exception as e:
            self.print_error(f"SMTP connection error: {str(e)}")
            
            # Specific error handling
            if "Authentication Required" in str(e):
                self.print_fix("Gmail requires App Password, not regular password")
                self.print_fix("Enable 2FA and generate App Password at: https://myaccount.google.com/apppasswords")
            elif "Less secure app access" in str(e):
                self.print_fix("Enable 'Less secure app access' or use App Password")
            elif "Connection refused" in str(e):
                self.print_fix("Check firewall settings and network connectivity")
            
            return False
    
    def test_email_sending(self):
        """Test actual email sending"""
        self.print_step(4, "Testing Email Sending")
        
        test_email = settings.EMAIL_HOST_USER  # Send to self for testing
        
        try:
            result = send_mail(
                subject='Production Email Test',
                message='This is a test email from production server to verify email configuration.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[test_email],
                fail_silently=False,
            )
            
            if result == 1:
                self.print_success(f"Test email sent successfully to {test_email}")
                return True
            else:
                self.print_error("Email sending failed - no exception but result was 0")
                return False
                
        except Exception as e:
            self.print_error(f"Email sending failed: {str(e)}")
            return False
    
    def check_production_specific_issues(self):
        """Check for production-specific issues"""
        self.print_step(5, "Checking Production-Specific Issues")
        
        issues_found = False
        
        # Check if DEBUG is False in production
        if settings.DEBUG:
            self.print_warning("DEBUG=True in production (should be False)")
            self.print_fix("Set DEBUG=False in production environment")
            issues_found = True
        
        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            self.print_warning("ALLOWED_HOSTS not properly configured")
            self.print_fix("Set specific domain names in ALLOWED_HOSTS")
            issues_found = True
        else:
            self.print_success(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        
        # Check if using console backend accidentally
        if 'console' in settings.EMAIL_BACKEND:
            self.print_error("Using console email backend in production")
            self.print_fix("Change EMAIL_BACKEND to django.core.mail.backends.smtp.EmailBackend")
            issues_found = True
        
        if not issues_found:
            self.print_success("No obvious production configuration issues found")
        
        return not issues_found
    
    def test_user_registration_flow(self):
        """Test the actual user registration email flow"""
        self.print_step(6, "Testing User Registration Email Flow")
        
        test_email = "test.production@example.com"
        
        try:
            # Clean up any existing test user
            User.objects.filter(email=test_email).delete()
            
            # Create test user
            user = User.objects.create_user(
                email=test_email,
                password="Test123!@#",
                full_name="Production Test User"
            )
            
            # Test welcome email
            self.print_info("Testing welcome email...")
            welcome_success, welcome_msg = user.send_welcome_email()
            if welcome_success:
                self.print_success("Welcome email method executed successfully")
            else:
                self.print_error(f"Welcome email failed: {welcome_msg}")
            
            # Test verification email
            self.print_info("Testing verification email...")
            verification_success, verification_msg = user.send_verification_email()
            if verification_success:
                self.print_success("Verification email method executed successfully")
                
                # Get the OTP
                otp = OTP.objects.filter(user=user, otp_type='email_verification').first()
                if otp:
                    self.print_info(f"OTP generated: {otp.otp_code}")
            else:
                self.print_error(f"Verification email failed: {verification_msg}")
            
            # Cleanup
            user.delete()
            
            return welcome_success and verification_success
            
        except Exception as e:
            self.print_error(f"User registration flow test failed: {str(e)}")
            return False
    
    def generate_production_fixes(self):
        """Generate specific fixes for production"""
        self.print_step(7, "Generating Production Fixes")
        
        production_env_template = """
# PRODUCTION EMAIL CONFIGURATION
# Copy these to your production environment variables

# Gmail SMTP Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=medixmallstore@gmail.com
EMAIL_HOST_PASSWORD=your_16_character_app_password_here
DEFAULT_FROM_EMAIL=medixmallstore@gmail.com

# Production Django Settings
DEBUG=False
SECRET_KEY=your_production_secret_key_here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# For Render.com specifically:
# Set these as Environment Variables in Render dashboard
"""
        
        print("\n📋 PRODUCTION ENVIRONMENT VARIABLES TEMPLATE:")
        print(production_env_template)
        
        # Platform-specific instructions
        render_instructions = """
🚀 RENDER.COM DEPLOYMENT INSTRUCTIONS:

1. Go to your Render dashboard
2. Select your web service
3. Go to Environment tab
4. Add these variables one by one:

   EMAIL_HOST_USER = medixmallstore@gmail.com
   EMAIL_HOST_PASSWORD = [your 16-character app password]
   DEFAULT_FROM_EMAIL = medixmallstore@gmail.com
   EMAIL_BACKEND = django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST = smtp.gmail.com
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   DEBUG = False

5. Redeploy your service
6. Test email functionality
"""
        
        print(render_instructions)
        
        heroku_instructions = """
🚀 HEROKU DEPLOYMENT INSTRUCTIONS:

Run these commands in your terminal:

heroku config:set EMAIL_HOST_USER=medixmallstore@gmail.com
heroku config:set EMAIL_HOST_PASSWORD=your_app_password_here
heroku config:set DEFAULT_FROM_EMAIL=medixmallstore@gmail.com
heroku config:set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
heroku config:set EMAIL_HOST=smtp.gmail.com
heroku config:set EMAIL_PORT=587
heroku config:set EMAIL_USE_TLS=True
heroku config:set DEBUG=False
"""
        
        print(heroku_instructions)
    
    def run_complete_diagnosis(self):
        """Run complete email diagnosis"""
        self.print_banner("PRODUCTION EMAIL DIAGNOSIS & FIX")
        
        print(f"🕐 Diagnosis Time: {datetime.now()}")
        print(f"🌐 Environment: {'Development' if settings.DEBUG else 'Production'}")
        
        # Run all checks
        checks = [
            ("Environment Variables", self.check_environment_variables),
            ("Django Email Settings", self.check_django_email_settings),
            ("SMTP Connection", self.test_smtp_connection),
            ("Email Sending", self.test_email_sending),
            ("Production Configuration", self.check_production_specific_issues),
            ("Registration Flow", self.test_user_registration_flow)
        ]
        
        results = []
        for check_name, check_func in checks:
            try:
                result = check_func()
                results.append((check_name, result))
            except Exception as e:
                self.print_error(f"Check '{check_name}' crashed: {str(e)}")
                results.append((check_name, False))
        
        # Generate fixes
        self.generate_production_fixes()
        
        # Print summary
        self.print_banner("DIAGNOSIS SUMMARY")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for check_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {check_name}")
        
        print(f"\n📊 Overall Health: {passed}/{total} checks passed")
        
        if self.issues:
            print(f"\n🔍 ISSUES FOUND ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        
        if self.fixes:
            print(f"\n🔧 RECOMMENDED FIXES ({len(self.fixes)}):")
            for i, fix in enumerate(self.fixes, 1):
                print(f"  {i}. {fix}")
        
        # Final recommendations
        print(f"\n💡 IMMEDIATE ACTIONS NEEDED:")
        if passed < total:
            print("1. 🔑 Ensure Gmail App Password is correctly set")
            print("2. 🌐 Verify all environment variables in production")
            print("3. 🔄 Redeploy after fixing environment variables")
            print("4. 📧 Test with a real registration")
        else:
            print("✅ All checks passed! Email should be working in production.")
        
        return passed == total

def main():
    debugger = ProductionEmailDebugger()
    
    print("🔍 Starting Production Email Diagnosis...")
    print("This will help identify why emails work in development but not production.")
    
    success = debugger.run_complete_diagnosis()
    
    if success:
        print("\n🎉 EMAIL SYSTEM IS HEALTHY!")
        print("If emails still don't work in production, check your hosting platform's email policies.")
    else:
        print("\n⚠️ ISSUES FOUND - Please fix the issues above and redeploy.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
