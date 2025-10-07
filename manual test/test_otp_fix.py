#!/usr/bin/env python3
"""
🧪 OTP Verification Fix Test
Test the updated EmailVerificationView with frontend payload format
"""

import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append('/srv/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import User, OTP

def test_frontend_payload():
    """Test the exact frontend payload format"""
    print("🧪 Testing Frontend OTP Verification Payload")
    print("=" * 60)
    
    # Get the latest OTP for the user
    try:
        user = User.objects.get(email='princekumar205086@gmail.com')
        latest_otp = OTP.objects.filter(
            user=user,
            otp_type='email_verification',
            is_verified=False
        ).order_by('-created_at').first()
        
        if not latest_otp:
            print("❌ No unverified OTP found")
            return False
        
        print(f"📋 Found OTP: {latest_otp.otp_code}")
        print(f"📅 Created: {latest_otp.created_at}")
        print(f"⏰ Expires: {latest_otp.expires_at}")
        print(f"🔄 Verified: {latest_otp.is_verified}")
        print(f"⚡ Expired: {latest_otp.is_expired()}")
        
        # Test with the frontend payload format
        frontend_payload = {
            "email": "princekumar205086@gmail.com",
            "otp": latest_otp.otp_code,  # Frontend uses 'otp'
            "purpose": "email_verification"  # Frontend uses 'purpose'
        }
        
        print(f"\n📤 Testing with frontend payload:")
        print(json.dumps(frontend_payload, indent=2))
        
        # Test the API endpoint
        url = 'https://backend.okpuja.in/api/accounts/verify-email/'
        response = requests.post(url, json=frontend_payload, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("✅ Frontend payload verification SUCCESSFUL!")
            return True
        else:
            print("❌ Frontend payload verification FAILED")
            return False
            
    except User.DoesNotExist:
        print("❌ User not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_standard_payload():
    """Test the standard API payload format"""
    print("\n🧪 Testing Standard OTP Verification Payload")
    print("=" * 60)
    
    # Get the latest OTP for the user
    try:
        user = User.objects.get(email='princekumar205086@gmail.com')
        latest_otp = OTP.objects.filter(
            user=user,
            otp_type='email_verification',
            is_verified=False
        ).order_by('-created_at').first()
        
        if not latest_otp:
            print("❌ No unverified OTP found")
            return False
        
        # Test with the standard payload format
        standard_payload = {
            "email": "princekumar205086@gmail.com",
            "otp_code": latest_otp.otp_code,  # Standard uses 'otp_code'
            "otp_type": "email_verification"  # Standard uses 'otp_type'
        }
        
        print(f"📤 Testing with standard payload:")
        print(json.dumps(standard_payload, indent=2))
        
        # Test the API endpoint
        url = 'https://backend.okpuja.in/api/accounts/verify-email/'
        response = requests.post(url, json=standard_payload, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("✅ Standard payload verification SUCCESSFUL!")
            return True
        else:
            print("❌ Standard payload verification FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 OTP Verification Fix Testing")
    print("Testing both frontend and standard payload formats")
    print("=" * 60)
    
    # Test frontend format (what the user is sending)
    frontend_success = test_frontend_payload()
    
    # Create a new OTP for standard format test (if first test succeeded)
    if frontend_success:
        print("\n🔄 Creating new OTP for standard format test...")
        try:
            user = User.objects.get(email='princekumar205086@gmail.com')
            # Send new verification email to get fresh OTP
            user.send_verification_email()
            print("✅ New OTP sent")
        except Exception as e:
            print(f"❌ Failed to send new OTP: {e}")
    
    # Test standard format
    standard_success = test_standard_payload()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"📱 Frontend Format: {'✅ PASS' if frontend_success else '❌ FAIL'}")
    print(f"🔧 Standard Format: {'✅ PASS' if standard_success else '❌ FAIL'}")
    
    if frontend_success:
        print("\n🎉 SUCCESS! Frontend payload format now works!")
        print("Frontend can now send: {email, otp, purpose}")
    else:
        print("\n❌ Frontend payload still failing - check the fix")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
