#!/usr/bin/env python3
"""
Check Current Django Process Environment
Quick check to see if running Django has email variables
"""
import os
import sys

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.conf import settings

def main():
    print("🔍 CURRENT DJANGO PROCESS EMAIL CHECK")
    print("=" * 50)
    
    print("📊 Process Environment Variables:")
    email_vars = [
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD',
        'DEFAULT_FROM_EMAIL',
        'EMAIL_BACKEND',
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_USE_TLS'
    ]
    
    for var in email_vars:
        value = os.environ.get(var)
        if var == 'EMAIL_HOST_PASSWORD':
            display = "SET" if value else "NOT SET"
        else:
            display = value if value else "NOT SET"
        
        status = "✅" if value else "❌"
        print(f"{status} {var}: {display}")
    
    print(f"\n📊 Django Settings:")
    settings_vars = [
        ('EMAIL_HOST_USER', settings.EMAIL_HOST_USER),
        ('EMAIL_HOST_PASSWORD', 'SET' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'),
        ('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
        ('EMAIL_BACKEND', settings.EMAIL_BACKEND),
        ('EMAIL_HOST', settings.EMAIL_HOST),
        ('EMAIL_PORT', settings.EMAIL_PORT),
        ('EMAIL_USE_TLS', settings.EMAIL_USE_TLS),
        ('DEBUG', settings.DEBUG)
    ]
    
    for name, value in settings_vars:
        status = "✅" if value else "❌"
        print(f"{status} {name}: {value}")
    
    # Quick email test
    print(f"\n📧 Quick Email Test:")
    try:
        from django.core.mail import send_mail
        
        result = send_mail(
            'Quick Django Process Test',
            'Testing if current Django process can send emails',
            settings.DEFAULT_FROM_EMAIL,
            ['princekumar205086@gmail.com'],
            fail_silently=False
        )
        
        if result == 1:
            print("✅ Email sent successfully from current Django process!")
        else:
            print("❌ Email sending failed (result: 0)")
            
    except Exception as e:
        print(f"❌ Email error: {e}")
    
    # Check if all required vars are set
    required_env = ['EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL']
    missing_env = [var for var in required_env if not os.environ.get(var)]
    
    required_settings = [settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD, settings.DEFAULT_FROM_EMAIL]
    missing_settings = [var for var in required_settings if not var]
    
    print(f"\n🎯 STATUS:")
    if not missing_env and not missing_settings:
        print("✅ Current Django process should be able to send emails!")
        print("📧 Frontend registration should work")
    else:
        print("❌ Current Django process is missing email configuration")
        print("🔧 Restart Django server with environment variables")
        if missing_env:
            print(f"   Missing env vars: {missing_env}")
        if missing_settings:
            print(f"   Missing settings: {len(missing_settings)} items")

if __name__ == "__main__":
    main()
