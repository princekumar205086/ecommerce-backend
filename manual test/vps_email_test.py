#!/usr/bin/env python3
"""
Simple Production Email Test for VPS
Fixed version that properly sets Django settings
"""
import os
import sys

# Set Django settings module before importing Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_production_email():
    print("🔍 Testing Production Email on VPS...")
    print("=" * 50)
    
    print(f"📧 EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"🔑 EMAIL_HOST_PASSWORD: {'SET' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"📮 DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"🔧 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"🌐 EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"📡 EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"🔒 EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"🐛 DEBUG: {settings.DEBUG}")
    
    print(f"\n📤 Sending test email...")
    
    try:
        result = send_mail(
            subject='🚀 VPS Production Email Test - SUCCESS',
            message='''
🎉 PRODUCTION EMAIL IS WORKING!

This email was sent from your Hostinger VPS production server.

✅ Django Settings: Loaded
✅ Environment Variables: Set
✅ Gmail SMTP: Working
✅ Email Delivery: SUCCESS

Time: {}
Server: Hostinger VPS (157.173.221.192)
Environment: Production

Your users can now receive:
- Welcome emails during registration
- OTP verification codes
- Password reset emails

Authentication system is fully operational! 🚀
            '''.format(__import__('datetime').datetime.now()),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['princekumar205086@gmail.com'],
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ SUCCESS! Test email sent successfully.")
            print("📬 Check princekumar205086@gmail.com for the test email.")
            print("🎉 Production email system is working!")
            return True
        else:
            print("❌ FAILED! Email was not sent (result: 0)")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Email sending failed!")
        print(f"🔍 Error details: {str(e)}")
        return False

def test_registration_flow():
    """Test the actual registration email flow"""
    print(f"\n🧪 Testing Registration Email Flow...")
    
    try:
        from accounts.models import User, OTP
        
        # Clean up any existing test user
        test_email = "test.production.vps@example.com"
        User.objects.filter(email=test_email).delete()
        
        # Create test user
        user = User.objects.create_user(
            email=test_email,
            password="Test123!@#",
            full_name="VPS Test User"
        )
        
        print(f"👤 Created test user: {user.email}")
        
        # Test welcome email
        print("📧 Testing welcome email...")
        welcome_success, welcome_msg = user.send_welcome_email()
        if welcome_success:
            print("✅ Welcome email sent successfully")
        else:
            print(f"❌ Welcome email failed: {welcome_msg}")
        
        # Test verification email
        print("🔐 Testing verification OTP email...")
        verification_success, verification_msg = user.send_verification_email()
        if verification_success:
            print("✅ Verification OTP email sent successfully")
            
            # Get the OTP
            otp = OTP.objects.filter(user=user, otp_type='email_verification').first()
            if otp:
                print(f"🔢 OTP Code Generated: {otp.otp_code}")
                print(f"⏰ Expires At: {otp.expires_at}")
        else:
            print(f"❌ Verification email failed: {verification_msg}")
        
        # Cleanup
        user.delete()
        
        return welcome_success and verification_success
        
    except Exception as e:
        print(f"❌ Registration flow test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 VPS Production Email Test")
    print("Testing email functionality on Hostinger VPS")
    
    # Test basic email sending
    email_ok = test_production_email()
    
    # Test registration flow
    if email_ok:
        registration_ok = test_registration_flow()
    else:
        registration_ok = False
        print("\n⚠️ Skipping registration test due to basic email failure")
    
    print(f"\n" + "=" * 50)
    print(f"🎯 FINAL RESULTS:")
    print(f"Basic Email Test: {'✅ PASS' if email_ok else '❌ FAIL'}")
    print(f"Registration Flow: {'✅ PASS' if registration_ok else '❌ FAIL'}")
    
    if email_ok and registration_ok:
        print(f"\n🎉 SUCCESS! Production emails are fully working!")
        print(f"✅ Users will receive welcome emails")
        print(f"✅ Users will receive OTP verification emails")
        print(f"✅ Complete authentication flow is operational")
        print(f"\n📧 Check princekumar205086@gmail.com for test emails")
    else:
        print(f"\n⚠️ Some issues found - check the logs above")
    
    sys.exit(0 if (email_ok and registration_ok) else 1)
