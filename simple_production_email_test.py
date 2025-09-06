#!/usr/bin/env python3
"""
Simple Production Email Test
Quick test to verify if email settings work in production
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_production_email():
    print("🔍 Testing Production Email Configuration...")
    print(f"📧 From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"🔧 Backend: {settings.EMAIL_BACKEND}")
    print(f"🌐 Host: {settings.EMAIL_HOST}")
    print(f"📮 Port: {settings.EMAIL_PORT}")
    print(f"🔒 TLS: {settings.EMAIL_USE_TLS}")
    
    # Test email to the sender (safe test)
    test_email = settings.EMAIL_HOST_USER
    
    try:
        print(f"\n📤 Sending test email to: {test_email}")
        
        result = send_mail(
            subject='🚀 Production Email Test - SUCCESS',
            message='''
This is a test email from your production Django server.

If you receive this email, your email configuration is working correctly!

✅ SMTP Connection: Working
✅ Authentication: Working  
✅ Email Delivery: Working

You can now proceed with user registration emails.

Time: {datetime.now()}
Server: Production Django Server
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ SUCCESS! Test email sent successfully.")
            print("📬 Check your email inbox for the test message.")
            print("🎉 Production email configuration is working!")
            return True
        else:
            print("❌ FAILED! Email was not sent (result: 0)")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Email sending failed!")
        print(f"🔍 Error details: {str(e)}")
        
        # Common error solutions
        if "Authentication Required" in str(e):
            print("\n🔧 SOLUTION:")
            print("1. Enable 2-Factor Authentication on Gmail")
            print("2. Generate App Password: https://myaccount.google.com/apppasswords")
            print("3. Use the 16-character app password, not your regular password")
            print("4. Update EMAIL_HOST_PASSWORD environment variable")
        elif "Connection refused" in str(e):
            print("\n🔧 SOLUTION:")
            print("1. Check your server's outbound email policy")
            print("2. Ensure port 587 is not blocked")
            print("3. Contact your hosting provider about SMTP restrictions")
        
        return False

if __name__ == "__main__":
    from datetime import datetime
    success = test_production_email()
    
    if success:
        print(f"\n✅ PRODUCTION EMAIL: WORKING")
        print("Your users should now receive registration and OTP emails!")
    else:
        print(f"\n❌ PRODUCTION EMAIL: NOT WORKING")
        print("Please fix the configuration and test again.")
    
    sys.exit(0 if success else 1)
