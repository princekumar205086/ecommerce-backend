#!/usr/bin/env python
"""
Simple Email Authentication Test
==============================
"""

import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def test_smtp_direct():
    """Test SMTP connection directly"""
    print("🔍 TESTING DIRECT SMTP CONNECTION")
    print("=" * 50)
    
    try:
        # Create SMTP connection
        smtp_server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        smtp_server.starttls()
        
        print("✅ SMTP connection established")
        print("✅ TLS encryption started")
        
        # Try to login
        smtp_server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("✅ Authentication successful")
        
        # Create a simple message
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = 'asliprinceraj@gmail.com'
        msg['Subject'] = 'Direct SMTP Test - RX Verifier System'
        
        body = """
        This is a direct SMTP test email from the RX Verifier System.
        
        If you receive this email, the SMTP configuration is working correctly!
        
        Test timestamp: {timestamp}
        
        Best regards,
        RX Verification Team
        """.format(timestamp=str(datetime.now()))
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        text = msg.as_string()
        smtp_server.sendmail(settings.EMAIL_HOST_USER, 'asliprinceraj@gmail.com', text)
        print("✅ Email sent successfully via direct SMTP!")
        
        smtp_server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Possible solutions:")
        print("   1. Enable 2-Factor Authentication on Gmail")
        print("   2. Generate App Password: https://myaccount.google.com/apppasswords")
        print("   3. Use App Password instead of regular password")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_gmail_settings():
    """Check Gmail account settings recommendations"""
    print("\n🔧 GMAIL ACCOUNT SETTINGS CHECK")
    print("=" * 50)
    
    print("For medixmallstore@gmail.com account:")
    print()
    
    print("1. ✅ Two-Factor Authentication")
    print("   - Go to: https://myaccount.google.com/security")
    print("   - Enable 2-Step Verification")
    print()
    
    print("2. 🔑 App Password Generation")
    print("   - Go to: https://myaccount.google.com/apppasswords")
    print("   - Create app password for 'Mail'")
    print("   - Use this 16-character password in EMAIL_HOST_PASSWORD")
    print()
    
    print("3. 📧 Account Security")
    print("   - Less secure app access is disabled by Google (2022)")
    print("   - Must use App Passwords for SMTP authentication")
    print()
    
    print("4. 🚫 Sending Limits")
    print("   - Regular Gmail: 100 emails/day")
    print("   - Google Workspace: 2000 emails/day")
    print("   - Current account type: Regular Gmail")


def main():
    """Main function"""
    from datetime import datetime
    
    print("🏥 RX Upload System - Email Authentication Test")
    print("=" * 80)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📧 From Account: {settings.EMAIL_HOST_USER}")
    print(f"📧 To Account: asliprinceraj@gmail.com")
    print("=" * 80)
    
    # Test direct SMTP
    smtp_success = test_smtp_direct()
    
    # Show settings recommendations
    check_gmail_settings()
    
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS")
    print("=" * 80)
    
    if smtp_success:
        print("✅ SMTP authentication working!")
        print("✅ Email should be sent to asliprinceraj@gmail.com")
        print("✅ Check inbox (and spam folder)")
        return 0
    else:
        print("❌ SMTP authentication failed")
        print("💡 Please check Gmail account settings above")
        return 1


if __name__ == '__main__':
    from datetime import datetime
    exit_code = main()
    sys.exit(exit_code)