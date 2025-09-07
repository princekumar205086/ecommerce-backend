#!/usr/bin/env python3
"""
🔧 Production Email Fix Verification Script
Tests the complete email system after dotenv fix
"""

import os
import sys
import django

# Setup Django
sys.path.append('/srv/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from accounts.models import User, OTPModel
import requests
import json

def test_dotenv_loading():
    """Test if .env file is properly loaded"""
    print("🔧 Testing .env File Loading")
    print("=" * 60)
    
    # Check if settings are loaded from .env
    email_user = settings.EMAIL_HOST_USER
    email_pass = settings.EMAIL_HOST_PASSWORD
    debug_mode = settings.DEBUG
    
    print(f"📧 EMAIL_HOST_USER: {email_user}")
    print(f"🔑 EMAIL_HOST_PASSWORD: {'SET' if email_pass else 'NOT SET'}")
    print(f"🐛 DEBUG: {debug_mode}")
    print(f"🔧 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"🌐 EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"📡 EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"🔒 EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    
    # Verify critical settings are loaded
    missing_settings = []
    if not email_user:
        missing_settings.append('EMAIL_HOST_USER')
    if not email_pass:
        missing_settings.append('EMAIL_HOST_PASSWORD')
    
    if missing_settings:
        print(f"❌ Missing Settings: {missing_settings}")
        return False
    else:
        print("✅ All email settings loaded from .env file")
        return True

def test_direct_email():
    """Test direct email sending"""
    print("\n📧 Testing Direct Email Sending")
    print("=" * 60)
    
    try:
        result = send_mail(
            subject='🧪 Production Email Test - dotenv Fix',
            message=f'Test email sent from production server after dotenv fix.\n\nTime: {os.popen("date").read().strip()}\nServer: 157.173.221.192',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['princekumar205086@gmail.com'],
            fail_silently=False
        )
        print(f"✅ Email sent successfully! Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

def test_frontend_registration():
    """Test the actual frontend registration API"""
    print("\n🌐 Testing Frontend Registration API")
    print("=" * 60)
    
    # Clean up existing user first
    try:
        User.objects.filter(email='princekumar205086@gmail.com').delete()
        print("🗑️ Cleaned up existing user")
    except:
        pass
    
    # Test API call
    url = 'https://backend.okpuja.in/api/accounts/register/'
    payload = {
        "email": "princekumar205086@gmail.com",
        "full_name": "PRINCE KUMAR - DOTENV FIX TEST",
        "contact": "8677939971", 
        "password": "Prince@123",
        "password2": "Prince@123"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Registration successful!")
            print(f"👤 User ID: {data.get('user', {}).get('id')}")
            print(f"📧 Email: {data.get('user', {}).get('email')}")
            print(f"📨 Message: {data.get('message')}")
            
            # Check OTP creation
            try:
                otp = OTPModel.objects.filter(email='princekumar205086@gmail.com').latest('created_at')
                print(f"🔢 OTP Created: {otp.otp}")
                print(f"📅 Created At: {otp.created_at}")
                print(f"⏰ Expires At: {otp.expires_at}")
                return True
            except Exception as e:
                print(f"❌ OTP check failed: {e}")
                return False
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Production Email Fix Verification")
    print("Testing dotenv integration with Django settings")
    print("=" * 60)
    
    # Test 1: dotenv loading
    dotenv_ok = test_dotenv_loading()
    
    # Test 2: Direct email
    email_ok = test_direct_email()
    
    # Test 3: Frontend API
    api_ok = test_frontend_registration()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"🔧 dotenv Loading: {'✅ PASS' if dotenv_ok else '❌ FAIL'}")
    print(f"📧 Direct Email: {'✅ PASS' if email_ok else '❌ FAIL'}")
    print(f"🌐 Frontend API: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if all([dotenv_ok, email_ok, api_ok]):
        print("\n🎉 SUCCESS! All email systems working!")
        print("📧 Check princekumar205086@gmail.com for test emails")
    else:
        print("\n❌ Some tests failed - check the issues above")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
