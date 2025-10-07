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
IMAGEKIT_PRIVATE_KEY=private_BwSqW2hnr3Y6Z3t7p7UWujf+F7o=
IMAGEKIT_PUBLIC_KEY=public_s1TO0E+T48MD2OOcrPPT3v9K75k=
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/medixmall

# Email Configuration (Gmail SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=medixmallstore@gmail.com
EMAIL_HOST_PASSWORD=monb vbas djmw wmeh
DEFAULT_FROM_EMAIL=medixmallstore@gmail.com

# Razorpay Configuration
RAZORPAY_API_KEY=rzp_test_hZpYcGhumUM4Z2
RAZORPAY_API_SECRET=9ge230isKnELfyR3QN2o5SXF
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

echo "✅ .env file created with production settings"

# Also export environment variables for current session
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=medixmallstore@gmail.com
export EMAIL_HOST_PASSWORD="monb vbas djmw wmeh"
export DEFAULT_FROM_EMAIL=medixmallstore@gmail.com
export DEBUG=False

echo "✅ Environment variables exported for current session"

# Make sure python-dotenv is installed
pip install python-dotenv

echo "✅ python-dotenv installed"

# Test the configuration
echo "🧪 Testing email configuration..."
python check_production_email.py

echo ""
echo "🔧 Next steps:"
echo "1. Restart your Django application/server"
echo "2. Test user registration"
echo "3. Check that emails are received at princekumar205086@gmail.com"
echo ""
echo "📝 To make environment variables permanent across reboots:"
echo "   Add the export commands to /etc/environment or ~/.bashrc"
