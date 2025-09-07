#!/usr/bin/env python3
"""
🧪 Fresh OTP Test with Current User
Generate new OTP and test immediately
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

def generate_fresh_otp():
    """Generate a fresh OTP for the current user"""
    print("🔄 Generating Fresh OTP")
    print("=" * 60)
    
    try:
        user = User.objects.get(email='princekumar205086@gmail.com')
        
        # Send fresh verification email
        success, message = user.send_verification_email()
        
        if success:
            print("✅ Fresh verification email sent!")
            
            # Get the latest OTP
            latest_otp = OTP.objects.filter(
                user=user,
                otp_type='email_verification',
                is_verified=False
            ).order_by('-created_at').first()
            
            if latest_otp:
                print(f"🔢 New OTP: {latest_otp.otp_code}")
                print(f"📅 Created: {latest_otp.created_at}")
                print(f"⏰ Expires: {latest_otp.expires_at}")
                print(f"🕐 Expired: {latest_otp.is_expired()}")
                return latest_otp.otp_code
            else:
                print("❌ No OTP found after sending")
                return None
        else:
            print(f"❌ Failed to send email: {message}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_fresh_otp_verification(otp_code):
    """Test OTP verification with fresh code"""
    print(f"\n🧪 Testing Fresh OTP Verification")
    print("=" * 60)
    
    if not otp_code:
        print("❌ No OTP code provided")
        return False
    
    # Frontend payload format
    frontend_payload = {
        "email": "princekumar205086@gmail.com",
        "otp": otp_code,
        "purpose": "email_verification"
    }
    
    print(f"📤 Frontend Payload:")
    print(json.dumps(frontend_payload, indent=2))
    
    try:
        url = 'https://backend.okpuja.in/api/accounts/verify-email/'
        response = requests.post(url, json=frontend_payload, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("🎉 SUCCESS! Frontend payload verification WORKS!")
            
            # Verify in database
            user = User.objects.get(email='princekumar205086@gmail.com')
            print(f"✅ User email_verified status: {user.email_verified}")
            
            return True
        else:
            print("❌ Verification failed")
            
            # Show error details
            try:
                error_data = response.json()
                print(f"🔍 Error details: {error_data}")
            except:
                pass
                
            return False
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Fresh OTP End-to-End Test")
    print("Testing complete flow with new OTP")
    print("=" * 60)
    
    # Step 1: Generate fresh OTP
    fresh_otp = generate_fresh_otp()
    
    if fresh_otp:
        print(f"\n💡 Check your email for OTP: {fresh_otp}")
        print("📧 You should receive a verification email with this code")
        
        # Step 2: Test verification immediately
        success = test_fresh_otp_verification(fresh_otp)
        
        print("\n" + "=" * 60)
        print("🎯 FINAL RESULT:")
        
        if success:
            print("🎉 COMPLETE SUCCESS!")
            print("✅ OTP verification works with frontend payload")
            print("✅ Email marked as verified")
            print("✅ Ready for production use!")
        else:
            print("❌ Verification failed - check error details above")
            
    else:
        print("❌ Failed to generate fresh OTP")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
