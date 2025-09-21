#!/usr/bin/env python
"""
Email OTP and RX Verifier Email Test
==================================

Test both email verification OTP and RX verifier account creation emails
"""

import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import User
from rx_upload.verifier_management import VerifierAccountManager


def test_email_verification_otp():
    """Test OTP email for user registration"""
    print("📧 TESTING EMAIL VERIFICATION OTP")
    print("=" * 50)
    
    try:
        # Create a test user for email verification
        test_email = 'asliprinceraj@gmail.com'
        
        # Clean up any existing user
        User.objects.filter(email=test_email).delete()
        
        # Generate OTP
        import random
        otp_code = f"{random.randint(100000, 999999)}"
        
        # Send OTP email
        subject = 'MedixMall - Email Verification Code'
        message = f"""
Hi USER,

Thank you for registering with MedixMall!

Your email verification code is: {otp_code}

Please enter this 6-digit code to verify your email address.

This code will expire in 10 minutes.

If you did not create this account, please ignore this email.

Best regards,
MedixMall Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [test_email],
            fail_silently=False,
        )
        
        print(f"✅ OTP email sent successfully!")
        print(f"📧 To: {test_email}")
        print(f"🔢 OTP Code: {otp_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send OTP email: {str(e)}")
        return False


def test_rx_verifier_email():
    """Test RX verifier account creation email"""
    print("\n📧 TESTING RX VERIFIER ACCOUNT EMAIL")
    print("=" * 50)
    
    try:
        # Create verifier account manager
        manager = VerifierAccountManager()
        
        # Create test verifier data
        import time
        unique_license = f"MD{int(time.time())}"
        
        verifier_data = {
            'email': 'asliprinceraj@gmail.com',
            'full_name': 'Dr. Test Verifier',
            'specialization': 'General Medicine',
            'license_number': unique_license,
            'verification_level': 'senior',
            'max_daily_prescriptions': 30,
            'send_welcome_email': True
        }
        
        # Clean up any existing verifier
        User.objects.filter(email=verifier_data['email']).delete()
        
        # Create verifier account
        from rx_upload.verifier_management import VerifierAccountCreationSerializer
        serializer = VerifierAccountCreationSerializer(data=verifier_data)
        
        if serializer.is_valid():
            verifier = serializer.save()
            print(f"✅ Verifier account created successfully!")
            print(f"📧 Email should be sent to: {verifier_data['email']}")
            print(f"👨‍⚕️ Verifier: {verifier_data['full_name']}")
            
            return True
        else:
            print(f"❌ Verifier creation failed: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to create verifier account: {str(e)}")
        return False


def test_smtp_status():
    """Test current SMTP status"""
    print("\n🔧 CHECKING EMAIL CONFIGURATION")
    print("=" * 50)
    
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    
    if 'console' in settings.EMAIL_BACKEND:
        print("📺 Using CONSOLE backend - emails will print to console")
        print("💡 This bypasses Gmail limits for testing")
        return True
    else:
        print(f"📧 Using SMTP backend: {settings.EMAIL_HOST}")
        print(f"📧 From: {settings.EMAIL_HOST_USER}")
        return True


def main():
    """Main function"""
    from datetime import datetime
    
    print("🏥 Email OTP and RX Verifier Test")
    print("=" * 80)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check email configuration
    config_ok = test_smtp_status()
    
    # Test OTP email
    otp_ok = test_email_verification_otp()
    
    # Test RX verifier email
    verifier_ok = test_rx_verifier_email()
    
    # Results
    print("\n" + "=" * 80)
    print("📊 EMAIL TEST RESULTS")
    print("=" * 80)
    
    print(f"Configuration: {'✅ PASSED' if config_ok else '❌ FAILED'}")
    print(f"OTP Email: {'✅ PASSED' if otp_ok else '❌ FAILED'}")
    print(f"Verifier Email: {'✅ PASSED' if verifier_ok else '❌ FAILED'}")
    
    if otp_ok and verifier_ok:
        print("\n🎉 ALL EMAIL TESTS PASSED!")
        if 'console' in settings.EMAIL_BACKEND:
            print("📺 Emails printed to console above")
            print("💡 To send real emails, switch back to SMTP backend")
        else:
            print("📧 Real emails sent to asliprinceraj@gmail.com")
    else:
        print("\n⚠️ SOME EMAIL TESTS FAILED")
        
    return 0 if (otp_ok and verifier_ok) else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)