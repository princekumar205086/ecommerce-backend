#!/bin/bash
# 🚀 Production Django Server Restart Script with dotenv Fix
# This script properly restarts Django with .env file loading

echo "🔧 Restarting Django Server with dotenv Fix"
echo "================================================="

# Navigate to project directory
cd /srv/backend

# Activate virtual environment
source venv/bin/activate

# Kill existing Django processes
echo "🛑 Stopping existing Django processes..."
pkill -f "python manage.py runserver" || echo "No Django runserver processes found"
pkill -f "gunicorn" || echo "No gunicorn processes found"

# Wait a moment for processes to stop
sleep 2

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file found"
    echo "📄 .env file contents:"
    echo "----------------------"
    grep -E "EMAIL_|DEBUG=" .env | sed 's/EMAIL_HOST_PASSWORD=.*/EMAIL_HOST_PASSWORD=***HIDDEN***/'
    echo "----------------------"
else
    echo "❌ .env file not found!"
    exit 1
fi

# Test the dotenv loading in Django
echo ""
echo "🧪 Testing Django settings with dotenv..."
python -c "
import os
import django
from pathlib import Path
from dotenv import load_dotenv

# Load .env manually to test
BASE_DIR = Path('.').resolve()
load_dotenv(BASE_DIR / '.env')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings
print(f'📧 EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
print(f'🔑 EMAIL_HOST_PASSWORD: {\"SET\" if settings.EMAIL_HOST_PASSWORD else \"NOT SET\"}')
print(f'🐛 DEBUG: {settings.DEBUG}')
print(f'✅ dotenv loading works!')
"

if [ $? -eq 0 ]; then
    echo "✅ Django settings loading correctly!"
else
    echo "❌ Django settings loading failed!"
    exit 1
fi

# Start Django server in background
echo ""
echo "🚀 Starting Django server..."
nohup python manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &
DJANGO_PID=$!

# Wait a moment for server to start
sleep 3

# Check if server is running
if ps -p $DJANGO_PID > /dev/null; then
    echo "✅ Django server started successfully!"
    echo "📊 Process ID: $DJANGO_PID"
    echo "📝 Log file: django.log"
    echo "🌐 Server URL: https://backend.okpuja.in"
    
    # Test server response
    echo ""
    echo "🧪 Testing server response..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/ | grep -q "200\|302"; then
        echo "✅ Server responding correctly!"
    else
        echo "⚠️ Server may still be starting up..."
    fi
    
else
    echo "❌ Django server failed to start!"
    echo "📝 Check django.log for errors:"
    tail -20 django.log
    exit 1
fi

echo ""
echo "🎉 Django server restart complete!"
echo "💡 The .env file is now properly loaded by Django"
echo "📧 Email system should work from frontend now"
echo "================================================="
