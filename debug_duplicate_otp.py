#!/usr/bin/env python3
"""
🔍 Debug Duplicate OTP Issue
Investigate why user receives multiple OTPs during registration
"""

import os
import sys
import django

# Setup Django
sys.path.append('/srv/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import User, OTP
from django.utils import timezone
from datetime import timedelta

def check_duplicate_otps():
    """Check for duplicate OTPs created for the user"""
    print("🔍 Investigating Duplicate OTP Creation")
    print("=" * 60)
    
    try:
        user = User.objects.get(email='princekumar205086@gmail.com')
        print(f"👤 User: {user.full_name} (ID: {user.id})")
        
        # Get all OTPs for this user in the last hour
        recent_time = timezone.now() - timedelta(hours=1)
        recent_otps = OTP.objects.filter(
            user=user,
            created_at__gte=recent_time
        ).order_by('-created_at')
        
        print(f"\n📊 Found {recent_otps.count()} OTPs in the last hour:")
        
        for i, otp in enumerate(recent_otps, 1):
            print(f"\n🔢 OTP {i}:")
            print(f"  • Code: {otp.otp_code}")
            print(f"  • Type: {otp.otp_type}")
            print(f"  • Email: {otp.email}")
            print(f"  • Verified: {otp.is_verified}")
            print(f"  • Created: {otp.created_at}")
            print(f"  • Expires: {otp.expires_at}")
            print(f"  • Expired: {otp.is_expired()}")
            print(f"  • Attempts: {otp.attempts}")
        
        # Check for duplicates in same type
        email_verification_otps = recent_otps.filter(otp_type='email_verification')
        print(f"\n📧 Email verification OTPs: {email_verification_otps.count()}")
        
        if email_verification_otps.count() > 1:
            print("⚠️ DUPLICATE OTPS DETECTED!")
            print("This explains why you're receiving multiple emails")
            
            # Show the codes
            codes = [otp.otp_code for otp in email_verification_otps]
            print(f"🔢 Codes: {codes}")
            
            # Check creation time differences
            print("\n⏰ Creation Timeline:")
            for otp in email_verification_otps:
                print(f"  • {otp.otp_code}: {otp.created_at}")
        
        return True
        
    except User.DoesNotExist:
        print("❌ User not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_registration_flow():
    """Check what happens during registration"""
    print("\n🔍 Analyzing Registration Flow")
    print("=" * 60)
    
    print("📋 Checking User.send_verification_email() method...")
    
    # Check the send_verification_email method
    user = User.objects.get(email='princekumar205086@gmail.com')
    
    print("🧪 Testing send_verification_email logic:")
    
    # Check if there are existing unverified OTPs
    existing_otps = OTP.objects.filter(
        user=user,
        otp_type='email_verification',
        is_verified=False
    )
    
    print(f"📊 Existing unverified email OTPs: {existing_otps.count()}")
    for otp in existing_otps:
        print(f"  • {otp.otp_code} (Created: {otp.created_at})")
    
    return True

def check_registration_view():
    """Check the registration view for multiple OTP creation"""
    print("\n🔍 Checking Registration View Logic")
    print("=" * 60)
    
    # The issue might be in the registration view calling multiple email methods
    print("📋 Potential causes:")
    print("1. Registration view calls both welcome and verification emails")
    print("2. Each email method might create its own OTP")
    print("3. Frontend might be calling registration multiple times")
    print("4. Some middleware might be duplicating requests")
    
    return True

def main():
    """Main investigation function"""
    print("🚀 Duplicate OTP Investigation")
    print("Finding why you receive multiple OTPs")
    print("=" * 60)
    
    check_duplicate_otps()
    check_registration_flow()
    check_registration_view()
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS:")
    print("Most likely causes:")
    print("1. 📧 Registration sends both welcome + verification emails")
    print("2. 🔄 Each email creates separate OTP")
    print("3. 📱 Frontend might be calling API multiple times")
    print("4. 🔧 Need to consolidate OTP creation logic")
    print("=" * 60)

if __name__ == '__main__':
    main()
