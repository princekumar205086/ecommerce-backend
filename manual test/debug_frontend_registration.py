#!/usr/bin/env python3
"""
Debug Frontend Registration Issue
Check why emails work in test but not from frontend
"""
import os
import sys
import requests
import json

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.conf import settings
from accounts.models import User, OTP

def test_api_registration():
    """Test the exact same payload used by frontend"""
    print("🔍 Testing API Registration - Same as Frontend")
    print("=" * 60)
    
    # The exact payload from frontend
    payload = {
        "email": "princekumar205086@gmail.com",
        "full_name": "PRINCE KUMAR",
        "contact": "8677939971",
        "password": "Prince@123",
        "password2": "Prince@123"
    }
    
    print(f"📤 Testing API call to: https://backend.okpuja.in/api/accounts/register/")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Clean up existing user first
        User.objects.filter(email=payload['email']).delete()
        print(f"🗑️ Cleaned up existing user")
        
        # Make API request
        response = requests.post(
            'https://backend.okpuja.in/api/accounts/register/',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Registration successful!")
            print(f"👤 User ID: {data.get('user', {}).get('id')}")
            print(f"📧 Email: {data.get('user', {}).get('email')}")
            print(f"📨 Message: {data.get('message')}")
            
            # Check if OTP was created
            user = User.objects.get(email=payload['email'])
            otp = OTP.objects.filter(user=user, otp_type='email_verification').order_by('-created_at').first()
            
            if otp:
                print(f"🔢 OTP Created: {otp.otp_code}")
                print(f"📅 Created At: {otp.created_at}")
                print(f"⏰ Expires At: {otp.expires_at}")
                print(f"📧 Email Field: {otp.email}")
                
                # Check email sending logs
                print(f"\n🔍 Checking email sending...")
                
                # Test email sending manually
                try:
                    welcome_success, welcome_msg = user.send_welcome_email()
                    print(f"📬 Welcome Email: {'✅ SUCCESS' if welcome_success else '❌ FAILED'}")
                    if not welcome_success:
                        print(f"   Error: {welcome_msg}")
                    
                    verification_success, verification_msg = user.send_verification_email()
                    print(f"🔐 Verification Email: {'✅ SUCCESS' if verification_success else '❌ FAILED'}")
                    if not verification_success:
                        print(f"   Error: {verification_msg}")
                        
                except Exception as e:
                    print(f"❌ Email sending error: {str(e)}")
            else:
                print(f"❌ No OTP found in database!")
                
            return True
        else:
            print(f"❌ Registration failed!")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API request failed: {str(e)}")
        return False

def check_server_environment():
    """Check if Django server has the right environment variables"""
    print(f"\n🔧 Checking Django Settings")
    print("=" * 60)
    
    print(f"📧 EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"🔑 EMAIL_HOST_PASSWORD: {'SET' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"📮 DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"🔧 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"🌐 EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"📡 EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"🔒 EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"🐛 DEBUG: {settings.DEBUG}")
    
    # Check if all required settings are present
    required_settings = [
        ('EMAIL_HOST_USER', settings.EMAIL_HOST_USER),
        ('EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD),
        ('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
        ('EMAIL_BACKEND', settings.EMAIL_BACKEND),
    ]
    
    missing_settings = []
    for name, value in required_settings:
        if not value:
            missing_settings.append(name)
    
    if missing_settings:
        print(f"\n❌ Missing Settings: {missing_settings}")
        return False
    else:
        print(f"\n✅ All email settings are configured")
        return True

def check_process_environment():
    """Check if the process has environment variables"""
    print(f"\n🔍 Checking Process Environment Variables")
    print("=" * 60)
    
    env_vars = [
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD', 
        'DEFAULT_FROM_EMAIL',
        'EMAIL_BACKEND',
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_USE_TLS'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if var == 'EMAIL_HOST_PASSWORD':
            display_value = f"{'SET' if value else 'NOT SET'}"
        else:
            display_value = value or 'NOT SET'
        print(f"{var}: {display_value}")

if __name__ == "__main__":
    print("🚀 Frontend Registration Debug Script")
    print("Investigating why emails work in test but not from frontend")
    
    # Check environment and settings
    env_ok = check_process_environment()
    settings_ok = check_server_environment()
    
    # Test the actual API call
    api_ok = test_api_registration()
    
    print(f"\n" + "=" * 60)
    print(f"🎯 DIAGNOSIS SUMMARY:")
    print(f"Process Environment: {'✅ OK' if env_ok else '❌ ISSUE'}")
    print(f"Django Settings: {'✅ OK' if settings_ok else '❌ ISSUE'}")
    print(f"API Registration: {'✅ OK' if api_ok else '❌ ISSUE'}")
    
    if settings_ok and api_ok:
        print(f"\n🎉 Email system should be working!")
        print(f"📧 Check princekumar205086@gmail.com for emails")
    else:
        print(f"\n⚠️ Issues found - check Django server environment variables")
        print(f"🔧 Make sure Django server is started with environment variables")
    
    sys.exit(0 if (settings_ok and api_ok) else 1)
