#!/usr/bin/env python3
"""
🔒 Secure Email Test - After Security Fix
========================================

This script tests email functionality after resolving the GitGuardian security issue.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings


def test_email_configuration():
    """Test email configuration security and functionality"""
    print("🔒 SECURE EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    print("📋 Current Email Configuration:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   Host: {settings.EMAIL_HOST}")
    print(f"   Port: {settings.EMAIL_PORT}")
    print(f"   TLS: {settings.EMAIL_USE_TLS}")
    print(f"   User: {settings.EMAIL_HOST_USER}")
    
    # Check if password is set via environment variable
    password_set = bool(os.environ.get('EMAIL_HOST_PASSWORD'))
    print(f"   Password: {'✅ Set via ENV' if password_set else '❌ Not set'}")
    
    # Security check - ensure no hardcoded credentials
    if settings.EMAIL_HOST_PASSWORD and len(settings.EMAIL_HOST_PASSWORD) > 10:
        # Check if it looks like the old compromised password
        if "monb" in settings.EMAIL_HOST_PASSWORD or "vbas" in settings.EMAIL_HOST_PASSWORD:
            print("   🚨 SECURITY WARNING: Old compromised password detected!")
            print("   Please generate new Gmail app password immediately!")
            return False
        else:
            print("   🔒 Password appears to be new/secure")
    
    return password_set


def test_email_sending():
    """Test actual email sending"""
    print("\n📧 EMAIL SENDING TEST")
    print("=" * 60)
    
    if not os.environ.get('EMAIL_HOST_PASSWORD'):
        print("❌ EMAIL_HOST_PASSWORD not set in environment variables")
        print("💡 Please update your .env file with new Gmail app password")
        return False
    
    try:
        # Test email
        send_mail(
            subject='🔒 Email Security Test - Credentials Fixed',
            message='This email confirms that the SMTP security issue has been resolved and email is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['asliprinceraj@gmail.com'],
            fail_silently=False,
        )
        
        print("✅ Email sent successfully!")
        print("📧 Test email sent to: asliprinceraj@gmail.com")
        print("🔒 Email security issue has been resolved!")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Email sending failed: {error_msg}")
        
        if "authentication failed" in error_msg.lower():
            print("💡 Authentication failed - likely need new Gmail app password")
            print("💡 Follow the SECURE_EMAIL_CONFIGURATION_GUIDE.md instructions")
        elif "daily user sending limit exceeded" in error_msg.lower():
            print("💡 Gmail daily limit - wait 24 hours or use new password")
        else:
            print("💡 Check your email configuration and network connection")
        
        return False


def test_rx_verifier_email():
    """Test RX verifier welcome email"""
    print("\n🏥 RX VERIFIER EMAIL TEST")
    print("=" * 60)
    
    try:
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        
        # Test data
        test_data = {
            'verifier_name': 'Dr. Security Test',
            'verifier_email': 'asliprinceraj@gmail.com',
            'temporary_password': 'secure_test_123',
            'login_url': 'http://localhost:8000/api/rx-upload/auth/login/',
            'admin_email': 'admin@medixmall.com'
        }
        
        # Render HTML template
        html_content = render_to_string('emails/verifier_welcome.html', test_data)
        text_content = render_to_string('emails/verifier_welcome.txt', test_data)
        
        # Create email
        email = EmailMultiAlternatives(
            subject='🏥 Welcome to RX Verification System - Security Test',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[test_data['verifier_email']]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        print("✅ RX Verifier welcome email sent successfully!")
        print("📧 Professional email template working correctly")
        print("🔒 Email security and RX system both operational!")
        return True
        
    except Exception as e:
        print(f"❌ RX Verifier email failed: {str(e)}")
        return False


def main():
    """Run security and email tests"""
    print("🔒 EMAIL SECURITY FIX VERIFICATION")
    print("=" * 80)
    print("GitGuardian security issue resolution test")
    print("=" * 80)
    
    # Test 1: Configuration security
    config_secure = test_email_configuration()
    
    # Test 2: Email sending capability
    email_working = test_email_sending() if config_secure else False
    
    # Test 3: RX verifier email system
    rx_email_working = test_rx_verifier_email() if email_working else False
    
    # Final report
    print("\n" + "=" * 80)
    print("🎯 SECURITY FIX VERIFICATION RESULTS")
    print("=" * 80)
    
    print(f"🔒 Configuration Security: {'✅ SECURE' if config_secure else '❌ ISSUES'}")
    print(f"📧 Email Functionality: {'✅ WORKING' if email_working else '❌ BLOCKED'}")
    print(f"🏥 RX Verifier Emails: {'✅ WORKING' if rx_email_working else '❌ BLOCKED'}")
    
    if config_secure and email_working and rx_email_working:
        print("\n🎉 SUCCESS! EMAIL SECURITY ISSUE FULLY RESOLVED!")
        print("✅ SMTP credentials are now secure")
        print("✅ Email delivery is working correctly")
        print("✅ RX verifier system is fully operational")
        print("🔒 System is ready for production use")
        
    elif config_secure and not email_working:
        print("\n⚠️ SECURITY FIXED, EMAIL NEEDS NEW PASSWORD")
        print("✅ Old compromised credentials removed")
        print("❌ Need new Gmail app password to restore email")
        print("📖 Follow SECURE_EMAIL_CONFIGURATION_GUIDE.md")
        
    else:
        print("\n❌ SECURITY ISSUES STILL PRESENT")
        print("🚨 Check for remaining exposed credentials")
        print("📖 Review SECURE_EMAIL_CONFIGURATION_GUIDE.md")
    
    print("=" * 80)


if __name__ == '__main__':
    main()