#!/usr/bin/env python3
"""
Production Environment Variables Checker
Run this in your production environment to verify email settings
"""
import os
import sys

def check_production_env():
    print("🔍 PRODUCTION ENVIRONMENT VARIABLES CHECK")
    print("=" * 60)
    
    # Required email variables
    email_vars = {
        'EMAIL_HOST_USER': 'Gmail account email',
        'EMAIL_HOST_PASSWORD': 'Gmail app password',
        'DEFAULT_FROM_EMAIL': 'From email address',
        'EMAIL_BACKEND': 'Email backend class',
        'EMAIL_HOST': 'SMTP host',
        'EMAIL_PORT': 'SMTP port',
        'EMAIL_USE_TLS': 'TLS encryption'
    }
    
    print("\n📧 EMAIL CONFIGURATION:")
    missing_vars = []
    
    for var, description in email_vars.items():
        value = os.environ.get(var)
        if value:
            if var == 'EMAIL_HOST_PASSWORD':
                display_value = f"{'*' * len(value)} ({len(value)} chars)"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET ({description})")
            missing_vars.append(var)
    
    # Check Django settings if available
    try:
        import django
        django.setup()
        from django.conf import settings
        
        print(f"\n🔧 DJANGO SETTINGS:")
        print(f"✅ EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"✅ EMAIL_HOST_PASSWORD: {'SET' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
        print(f"✅ DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        print(f"✅ EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"✅ DEBUG: {settings.DEBUG}")
        
    except Exception as e:
        print(f"\n⚠️ Could not load Django settings: {e}")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    if missing_vars:
        print(f"❌ Missing Variables: {len(missing_vars)}")
        for var in missing_vars:
            print(f"   - {var}")
        print(f"\n🔧 ACTION NEEDED:")
        print(f"Set these environment variables in your production platform:")
        
        if 'EMAIL_HOST_PASSWORD' in missing_vars:
            print(f"   EMAIL_HOST_PASSWORD=your-app-password-here")
        if 'EMAIL_HOST_USER' in missing_vars:
            print(f"   EMAIL_HOST_USER=medixmallstore@gmail.com")
        if 'DEFAULT_FROM_EMAIL' in missing_vars:
            print(f"   DEFAULT_FROM_EMAIL=medixmallstore@gmail.com")
            
        return False
    else:
        print(f"✅ All email environment variables are set!")
        print(f"📤 Email sending should work in production.")
        return True

def test_email_sending():
    """Test email sending if Django is available"""
    try:
        import django
        django.setup()
        from django.core.mail import send_mail
        from django.conf import settings
        
        print(f"\n📧 Testing Email Sending...")
        
        result = send_mail(
            subject='🚀 Production Email Test',
            message='This is a test email from your production server. If you receive this, email is working!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['princekumar205086@gmail.com'],
            fail_silently=False
        )
        
        if result == 1:
            print(f"✅ EMAIL SENT SUCCESSFULLY!")
            print(f"📬 Check princekumar205086@gmail.com for the test email")
            return True
        else:
            print(f"❌ Email sending failed (result: {result})")
            return False
            
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Running Production Environment Check...")
    
    # Check environment variables
    env_ok = check_production_env()
    
    # Test email sending if env is OK
    if env_ok:
        email_ok = test_email_sending()
    else:
        email_ok = False
        print("\n⚠️ Skipping email test due to missing environment variables")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 FINAL RESULT:")
    print(f"Environment Variables: {'✅ OK' if env_ok else '❌ MISSING'}")
    print(f"Email Sending: {'✅ OK' if email_ok else '❌ FAILED'}")
    
    if env_ok and email_ok:
        print(f"\n🎉 SUCCESS! Production emails are working!")
        print(f"✅ User registration emails will be delivered")
        print(f"✅ OTP verification emails will work")
    else:
        print(f"\n⚠️ ACTION NEEDED: Fix environment variables and redeploy")
    
    sys.exit(0 if (env_ok and email_ok) else 1)
