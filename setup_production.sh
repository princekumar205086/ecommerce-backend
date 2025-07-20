#!/bin/bash
# Production setup script for Ubuntu/Debian servers

echo "🚀 Setting up Medical eCommerce API for production..."

# Install required system packages
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-venv nginx postgresql postgresql-contrib

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install -r requirements.txt

# Setup environment variables
echo "🔧 Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

# Collect static files
echo "🗃️  Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Create superuser (interactive)
echo "👤 Creating superuser..."
python manage.py createsuperuser

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Configure nginx to serve your application"
echo "2. Set up gunicorn or uWSGI"
echo "3. Configure SSL certificate"
echo "4. Test your endpoints:"
echo "   - Admin: https://backend.okpuja.in/admin/"
echo "   - Swagger: https://backend.okpuja.in/swagger/"
