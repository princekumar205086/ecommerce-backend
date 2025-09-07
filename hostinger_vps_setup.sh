#!/bin/bash
# Production Environment Setup Script for Hostinger VPS
# Run this script to set up email environment variables

echo "🚀 Setting up Production Environment Variables on Hostinger VPS"
echo "============================================================"

# Create or update .env file with production settings
cat > .env << 'EOF'
# Production Environment Variables for Hostinger VPS

# Django Configuration
DEBUG=False
SECRET_KEY=your-production-secret-key-here-change-this
ALLOWED_HOSTS=157.173.221.192,backend.okpuja.in,localhost,127.0.0.1

# ImageKit.io configuration
IMAGEKIT_PRIVATE_KEY=your_imagekit_private_key_here
IMAGEKIT_PUBLIC_KEY=your_imagekit_public_key_here
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/medixmall

# Email Configuration (Gmail SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=medixmallstore@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password_here
DEFAULT_FROM_EMAIL=medixmallstore@gmail.com

# Razorpay Configuration
RAZORPAY_API_KEY=your_razorpay_api_key_here
RAZORPAY_API_SECRET=your_razorpay_api_secret_here
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_here
APP_NAME=Ecommerce

# SMS Configuration (Twilio) - Set these with your actual values
SMS_BACKEND=accounts.sms.backends.twilio.SMSBackend
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here

# Database (if using PostgreSQL in production)
# DATABASE_URL=postgresql://user:password@localhost:5432/ecommerce_db
EOF

echo "✅ .env file template created"

# Also export environment variables for current session
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=medixmallstore@gmail.com
export EMAIL_HOST_PASSWORD="your_gmail_app_password_here"
export DEFAULT_FROM_EMAIL=medixmallstore@gmail.com
export DEBUG=False

echo "✅ Environment variables template exported"

# Make sure python-dotenv is installed
pip install python-dotenv

echo "✅ python-dotenv installed"

echo ""
echo "🔧 Next steps:"
echo "1. Edit .env file with your actual credentials"
echo "2. Set the EMAIL_HOST_PASSWORD to your Gmail app password"
echo "3. Restart your Django application/server"
echo "4. Test user registration"
echo ""
echo "📝 To test email configuration run:"
echo "   python vps_email_test.py"
