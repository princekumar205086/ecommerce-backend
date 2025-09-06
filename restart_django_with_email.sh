#!/bin/bash
# Django Server Restart Script with Environment Variables
# Run this on your VPS to restart Django with proper email settings

echo "🔄 Restarting Django Server with Email Environment Variables"
echo "============================================================"

# Kill any existing Django processes
echo "🛑 Stopping existing Django processes..."
pkill -f "python manage.py runserver" || echo "No existing Django process found"

# Wait a moment
sleep 2

# Set all environment variables
echo "🔧 Setting environment variables..."
export DJANGO_SETTINGS_MODULE=ecommerce.settings
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=medixmallstore@gmail.com
export EMAIL_HOST_PASSWORD="monb vbas djmw wmeh"
export DEFAULT_FROM_EMAIL=medixmallstore@gmail.com
export DEBUG=False

# Verify environment variables are set
echo "✅ Environment variables set:"
echo "   EMAIL_HOST_USER: $EMAIL_HOST_USER"
echo "   EMAIL_HOST_PASSWORD: SET"
echo "   DEFAULT_FROM_EMAIL: $DEFAULT_FROM_EMAIL"

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Install any missing packages
echo "📦 Installing required packages..."
pip install python-dotenv

# Start Django server with environment variables
echo "🚀 Starting Django server..."
echo "Server will be available at: http://157.173.221.192:8000"
echo "API will be available at: https://backend.okpuja.in"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python manage.py runserver 0.0.0.0:8000

echo "Django server stopped."
