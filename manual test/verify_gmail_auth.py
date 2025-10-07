#!/usr/bin/env python3
"""
Gmail App Password Verification Script
Tests if the current Gmail configuration works
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_app_password():
    # Your Gmail credentials
    gmail_user = "medixmallstore@gmail.com"
    gmail_password = "monb vbas djmw wmeh"  # This should be App Password
    
    print("🔍 Testing Gmail SMTP Authentication...")
    print(f"📧 Email: {gmail_user}")
    print(f"🔑 Password: {'*' * len(gmail_password)} ({len(gmail_password)} characters)")
    
    try:
        # Create SMTP connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable encryption
        
        print("🔗 SMTP connection established...")
        
        # Attempt login
        server.login(gmail_user, gmail_password)
        print("✅ LOGIN SUCCESSFUL! Gmail authentication working.")
        
        # Send test email
        sender_email = gmail_user
        receiver_email = "princekumar205086@gmail.com"
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "🚀 Gmail App Password Test - SUCCESS"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        text = f"""
🎉 GMAIL AUTHENTICATION SUCCESS!

Your Gmail App Password is working correctly.

✅ SMTP Connection: Working
✅ Authentication: Working
✅ Email Sending: Working

Time: {__import__('datetime').datetime.now()}
Server: Gmail SMTP
Configuration: Production Ready

This means your production emails should work now!
        """
        
        text_part = MIMEText(text, "plain")
        message.attach(text_part)
        
        # Send email
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        
        print(f"📤 Test email sent successfully to {receiver_email}")
        print("🎊 Gmail configuration is working perfectly!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION FAILED: {e}")
        print("\n🔧 SOLUTION NEEDED:")
        print("1. The current password is NOT an App Password")
        print("2. You need to generate a Gmail App Password")
        print("3. Steps:")
        print("   a. Enable 2FA on Gmail")
        print("   b. Go to https://myaccount.google.com/apppasswords")
        print("   c. Generate new App Password for 'Mail'")
        print("   d. Update EMAIL_HOST_PASSWORD with the 16-character code")
        return False
        
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print("\n🔧 POSSIBLE SOLUTIONS:")
        print("1. Check internet connection")
        print("2. Verify Gmail settings allow SMTP")
        print("3. Check firewall settings")
        return False

def verify_app_password_format():
    password = "monb vbas djmw wmeh"
    
    print("\n🔍 Analyzing Current Password Format...")
    print(f"Length: {len(password)} characters")
    print(f"Contains spaces: {'Yes' if ' ' in password else 'No'}")
    
    # Remove spaces and check length
    password_no_spaces = password.replace(' ', '')
    print(f"Without spaces: {len(password_no_spaces)} characters")
    
    if len(password_no_spaces) == 16:
        print("✅ Length is correct for App Password (16 characters)")
        return True
    else:
        print("❌ Length is incorrect for App Password (should be 16)")
        print("🔧 This might be a regular Gmail password, not an App Password")
        return False

if __name__ == "__main__":
    print("🚀 Gmail Configuration Verification")
    print("=" * 50)
    
    # Verify password format
    format_ok = verify_app_password_format()
    
    # Test actual connection
    auth_ok = test_gmail_app_password()
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY:")
    print(f"Password Format: {'✅ OK' if format_ok else '❌ ISSUE'}")
    print(f"Gmail Authentication: {'✅ OK' if auth_ok else '❌ ISSUE'}")
    
    if format_ok and auth_ok:
        print("\n🎉 SUCCESS! Your Gmail configuration is ready for production!")
    else:
        print("\n⚠️ ACTION NEEDED: Generate Gmail App Password and update EMAIL_HOST_PASSWORD")
        
    print(f"\n📧 If successful, check {receiver_email} for test email.")
    
    import sys
    sys.exit(0 if (format_ok and auth_ok) else 1)
