#!/usr/bin/env python3
"""
🏥 Complete RX Verifier Account Test with Real Email
==================================================

Based on complete_otp_fix_test.py pattern, this tests RX verifier account creation
with real email delivery to asliprinceraj@gmail.com
"""

import os
import sys
import django
import requests
import json
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import User
from rx_upload.models import VerifierProfile, VerifierWorkload
from rest_framework.authtoken.models import Token
from rx_upload.verifier_management import VerifierAccountManager


def test_email_sending_capability():
    """Test if email sending is currently working"""
    print("📧 TESTING EMAIL SENDING CAPABILITY")
    print("=" * 60)
    
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        print(f"📋 Email Configuration:")
        print(f"   Backend: {settings.EMAIL_BACKEND}")
        print(f"   Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        print(f"   User: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
        print(f"   From: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
        
        # Test simple email
        send_mail(
            'RX Verifier Test - Email Capability Check',
            'This is a test email to verify email sending capability.',
            settings.DEFAULT_FROM_EMAIL,
            ['asliprinceraj@gmail.com'],
            fail_silently=False,
        )
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        if "Daily user sending limit exceeded" in str(e):
            print("💡 Gmail daily limit exceeded - this explains the issue!")
            print("💡 Solution: Wait 24 hours or use different email account")
        return False


def clean_existing_verifier_test_data():
    """Clean up existing test data for clean test"""
    print("\n🧹 CLEANING EXISTING TEST DATA")
    print("=" * 60)
    
    try:
        # Clean up test verifier account
        test_email = 'asliprinceraj@gmail.com'
        
        # Remove any existing verifier with this email
        User.objects.filter(email=test_email, role='rx_verifier').delete()
        
        # Clean up verifier profiles with test license numbers
        VerifierProfile.objects.filter(license_number__startswith='MD').delete()
        
        print(f"✅ Cleaned up existing test data for {test_email}")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup error: {str(e)}")
        return False


def create_admin_user():
    """Create admin user for testing"""
    print("\n👑 CREATING ADMIN USER FOR TESTING")
    print("=" * 60)
    
    try:
        admin_email = 'admin@rxverification.com'
        
        # Clean up existing admin
        User.objects.filter(email=admin_email).delete()
        
        # Create admin user
        admin_user = User.objects.create_user(
            email=admin_email,
            password='admin123',
            full_name='Test Admin',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        
        # Create token for API access
        token, _ = Token.objects.get_or_create(user=admin_user)
        
        print(f"✅ Admin user created: {admin_email}")
        print(f"🔑 Admin token: {token.key}")
        
        return admin_user, token.key
        
    except Exception as e:
        print(f"❌ Admin creation error: {str(e)}")
        return None, None


def test_verifier_account_creation_via_api(admin_token):
    """Test verifier account creation via API with real email"""
    print("\n🏥 TESTING VERIFIER ACCOUNT CREATION VIA API")
    print("=" * 60)
    
    try:
        # Unique license number
        unique_license = f"MD{int(time.time())}"
        
        verifier_data = {
            'email': 'asliprinceraj@gmail.com',
            'full_name': 'Dr. Prince Raj Verifier',
            'specialization': 'General Medicine',
            'license_number': unique_license,
            'verification_level': 'senior',
            'max_daily_prescriptions': 30,
            'send_welcome_email': True
        }
        
        print(f"📤 Verifier Creation Payload:")
        print(json.dumps(verifier_data, indent=2))
        
        # Make API request
        headers = {
            'Authorization': f'Token {admin_token}',
            'Content-Type': 'application/json'
        }
        
        url = 'http://localhost:8000/api/rx-upload/admin/verifiers/create/'
        response = requests.post(url, json=verifier_data, headers=headers, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Content: {response.text}")
        
        if response.status_code == 201:
            response_data = response.json()
            print("✅ Verifier account created successfully!")
            
            # Extract credentials
            credentials = response_data.get('login_credentials', {})
            email_sent = response_data.get('email_sent', False)
            warning = response_data.get('warning', '')
            
            print(f"\n🔑 LOGIN CREDENTIALS:")
            print(f"   Email: {credentials.get('email')}")
            print(f"   Password: {credentials.get('temporary_password')}")
            
            print(f"\n📧 EMAIL STATUS:")
            print(f"   Email Sent: {'✅ YES' if email_sent else '❌ NO'}")
            if warning:
                print(f"   Warning: {warning}")
            
            return {
                'success': True,
                'credentials': credentials,
                'email_sent': email_sent,
                'verifier_id': response_data.get('verifier_id')
            }
        else:
            print(f"❌ Verifier creation failed: {response.text}")
            return {'success': False}
            
    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        return {'success': False}


def test_verifier_login(credentials):
    """Test verifier login with created credentials"""
    print("\n🔐 TESTING VERIFIER LOGIN")
    print("=" * 60)
    
    if not credentials:
        print("❌ No credentials provided")
        return False
    
    try:
        login_data = {
            'email': credentials.get('email'),
            'password': credentials.get('temporary_password')
        }
        
        print(f"📤 Login Payload:")
        print(json.dumps(login_data, indent=2))
        
        url = 'http://localhost:8000/api/rx-upload/auth/login/'
        response = requests.post(url, json=login_data, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("✅ Verifier login successful!")
            return True
        else:
            print("❌ Verifier login failed")
            return False
            
    except Exception as e:
        print(f"❌ Login Error: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🏥 Complete RX Verifier Account Test with Real Email")
    print("Based on OTP test pattern for medixmallstore@gmail.com")
    print("=" * 80)
    print(f"📅 Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Step 1: Test email capability
    email_working = test_email_sending_capability()
    
    # Step 2: Clean existing test data
    cleanup_success = clean_existing_verifier_test_data()
    
    # Step 3: Create admin user
    admin_user, admin_token = create_admin_user()
    
    # Step 4: Test verifier account creation
    if admin_token:
        creation_result = test_verifier_account_creation_via_api(admin_token)
        
        # Step 5: Test verifier login
        if creation_result['success']:
            login_success = test_verifier_login(creation_result.get('credentials'))
        else:
            login_success = False
    else:
        creation_result = {'success': False}
        login_success = False
    
    # Final Results
    print("\n" + "=" * 80)
    print("🎯 FINAL TEST RESULTS:")
    print("=" * 80)
    
    print(f"📧 Email Capability: {'✅ WORKING' if email_working else '❌ FAILED'}")
    print(f"🧹 Data Cleanup: {'✅ SUCCESS' if cleanup_success else '❌ FAILED'}")
    print(f"👑 Admin Creation: {'✅ SUCCESS' if admin_token else '❌ FAILED'}")
    print(f"🏥 Verifier Creation: {'✅ SUCCESS' if creation_result['success'] else '❌ FAILED'}")
    print(f"📧 Email Delivery: {'✅ SENT' if creation_result.get('email_sent') else '❌ NOT SENT'}")
    print(f"🔐 Verifier Login: {'✅ SUCCESS' if login_success else '❌ FAILED'}")
    
    if creation_result['success']:
        print(f"\n🎉 VERIFIER ACCOUNT CREATED SUCCESSFULLY!")
        if creation_result.get('email_sent'):
            print(f"📧 Welcome email sent to: asliprinceraj@gmail.com")
            print(f"📱 Please check your inbox for login credentials")
        else:
            print(f"⚠️ Account created but email not sent (likely Gmail limit)")
            credentials = creation_result.get('credentials', {})
            print(f"🔑 Manual credentials:")
            print(f"   Email: {credentials.get('email')}")
            print(f"   Password: {credentials.get('temporary_password')}")
    
    if email_working and creation_result['success']:
        print(f"\n✅ COMPLETE RX VERIFIER SYSTEM IS WORKING!")
    else:
        print(f"\n⚠️ SOME ISSUES DETECTED - CHECK LOGS ABOVE")
    
    print("=" * 80)


if __name__ == '__main__':
    main()