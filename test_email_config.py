#!/usr/bin/env python
"""
Email Configuration Test for RX Upload System
============================================

This test verifies the email configuration and provides solutions for email delivery issues.
"""

import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def test_email_configuration():
    """Test current email configuration"""
    print("🔧 EMAIL CONFIGURATION TEST")
    print("=" * 50)
    
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * 8 if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    if not settings.EMAIL_HOST_USER:
        print("\n❌ EMAIL_HOST_USER is not configured!")
        return False
        
    if not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ EMAIL_HOST_PASSWORD is not configured!")
        return False
        
    return True


def test_simple_email():
    """Test sending a simple email"""
    print("\n📧 TESTING SIMPLE EMAIL DELIVERY")
    print("=" * 50)
    
    try:
        send_mail(
            'RX Verifier Email Test',
            'This is a test email from the RX Upload System.',
            settings.DEFAULT_FROM_EMAIL,
            ['asliprinceraj@gmail.com'],
            fail_silently=False,
        )
        print("✅ Simple email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send simple email: {str(e)}")
        return False


def test_html_email():
    """Test sending HTML email with template"""
    print("\n📧 TESTING HTML EMAIL WITH TEMPLATE")
    print("=" * 50)
    
    try:
        # Create HTML content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .email-container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
                .header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
                .content { padding: 30px; background: #f8f9fa; }
                .credentials { background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .footer { background: #34495e; color: white; padding: 15px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🏥 RX Verification System</h1>
                </div>
                <div class="content">
                    <h2>Email Configuration Test</h2>
                    <p>Dear User,</p>
                    <p>This is a test email to verify that the RX Upload System email configuration is working correctly.</p>
                    
                    <div class="credentials">
                        <h3>Test Credentials:</h3>
                        <p><strong>Test Email:</strong> asliprinceraj@gmail.com</p>
                        <p><strong>Test Time:</strong> {timestamp}</p>
                    </div>
                    
                    <p>If you receive this email, the email notification system is working properly!</p>
                    
                    <p>Best regards,<br>RX Verification Team</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 RX Verification System. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Format with timestamp
        from datetime import datetime
        formatted_html = html_content.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Create email message
        email = EmailMultiAlternatives(
            subject='🏥 RX System - Email Configuration Test',
            body='This is a test email from the RX Upload System. Please check the HTML version.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['asliprinceraj@gmail.com']
        )
        email.attach_alternative(formatted_html, "text/html")
        
        email.send()
        print("✅ HTML email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send HTML email: {str(e)}")
        return False


def provide_solutions():
    """Provide solutions for common email issues"""
    print("\n🛠️ EMAIL DELIVERY SOLUTIONS")
    print("=" * 50)
    
    print("📋 Common Issues and Solutions:")
    print()
    
    print("1. 🚫 Daily Sending Limit Exceeded (Current Issue)")
    print("   - Error: '5.4.5 Daily user sending limit exceeded'")
    print("   - Solution: Wait 24 hours or use a different Gmail account")
    print("   - Gmail limit: 100 emails/day for regular accounts")
    print("   - Alternative: Use Google Workspace account (higher limits)")
    print()
    
    print("2. 🔑 Authentication Issues")
    print("   - Solution: Enable 2-Factor Authentication on Gmail")
    print("   - Generate App Password: https://myaccount.google.com/apppasswords")
    print("   - Use App Password instead of regular password")
    print()
    
    print("3. 🔒 Less Secure App Access")
    print("   - Gmail disabled this feature in 2022")
    print("   - Must use App Passwords with 2FA enabled")
    print()
    
    print("4. 💡 Alternative Email Providers")
    print("   - SendGrid: 100 emails/day free")
    print("   - Mailgun: 5,000 emails/month free")
    print("   - Amazon SES: Pay-per-use pricing")
    print()
    
    print("5. 🔧 Environment Configuration")
    print("   Required Environment Variables:")
    print("   - EMAIL_HOST_USER=your-email@gmail.com")
    print("   - EMAIL_HOST_PASSWORD=your-app-password")
    print("   - DEFAULT_FROM_EMAIL=your-email@gmail.com")


def main():
    """Main function to run email tests"""
    print("🏥 RX Upload System - Email Configuration Test")
    print("=" * 80)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Test configuration
    config_ok = test_email_configuration()
    
    if not config_ok:
        print("\n❌ Email configuration incomplete!")
        provide_solutions()
        return 1
    
    # Test simple email
    simple_ok = test_simple_email()
    
    # Test HTML email
    html_ok = test_html_email()
    
    # Results
    print("\n" + "=" * 80)
    print("📊 EMAIL TEST RESULTS")
    print("=" * 80)
    
    print(f"Configuration: {'✅ PASSED' if config_ok else '❌ FAILED'}")
    print(f"Simple Email: {'✅ PASSED' if simple_ok else '❌ FAILED'}")
    print(f"HTML Email: {'✅ PASSED' if html_ok else '❌ FAILED'}")
    
    if simple_ok and html_ok:
        print("\n🎉 EMAIL SYSTEM IS WORKING PERFECTLY!")
        print("✅ You should receive test emails at asliprinceraj@gmail.com")
    else:
        print("\n⚠️ EMAIL SYSTEM HAS ISSUES")
        provide_solutions()
        
    return 0 if (simple_ok and html_ok) else 1


if __name__ == '__main__':
    from datetime import datetime
    exit_code = main()
    sys.exit(exit_code)