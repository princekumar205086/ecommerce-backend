# Updated Deployment Guide - Based on Working Configuration

## Key Changes Made to Match Your Working Project:

### 1. **Updated `ecommerce/settings.py`**:

#### Changed environment variable handling:
```python
# Old:
DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 'yes']

# New (matching working project):
DEBUG = os.getenv('DEBUG', 'True') == 'True'
```

#### Updated ALLOWED_HOSTS to use environment variables:
```python
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,backend.okpuja.in,ecommerce-backend-77dc.onrender.com,157.173.221.192').split(',')
```

#### Simplified CORS configuration:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://medixmall.vercel.app',
    'https://backend.okpuja.in',
]
CORS_ALLOW_CREDENTIALS = True
```

#### Removed WhiteNoise (following working project pattern):
- Removed WhiteNoise middleware
- Simplified static file configuration
- Using standard Django static file serving

#### Updated Swagger settings to match working project

### 2. **Updated `ecommerce/urls.py`**:
- Simplified static file serving
- Removed complex production static file handling
- Following the working project's simpler approach

### 3. **Updated `.env` file**:
```env
# Environment variables for the MedixMall application

# Django Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,backend.okpuja.in,ecommerce-backend-77dc.onrender.com,157.173.221.192

# imagekit.io configuration
IMAGEKIT_PRIVATE_KEY=private_BwSqW2hnr3Y6Z3t7p7UWujf+F7o=
IMAGEKIT_PUBLIC_KEY=public_s1TO0E+T48MD2OOcrPPT3v9K75k=
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/medixmall

# Email configuration
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

## Deployment Steps:

### 1. **On Your Server:**

```bash
# 1. Navigate to your project
cd /path/to/your/project

# 2. Install/update dependencies (if needed)
pip install python-dotenv

# 3. Create/update .env file with the content above

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Run system checks
python manage.py check

# 6. Restart your web server
sudo systemctl restart your-web-server-name
# or
sudo service nginx restart
# or whatever your server setup uses
```

### 2. **For Production (after testing):**

In your `.env` file on the server, change:
```env
DEBUG=False
SECRET_KEY=your-actual-production-secret-key
```

## Why This Should Work:

1. **Environment Variables**: Now properly loaded using `os.getenv()` like your working project
2. **Simplified Static Files**: Removed complex WhiteNoise setup, using Django's standard approach
3. **CORS Configuration**: Matches your working project's pattern
4. **Debug Mode**: Following the same pattern as working project
5. **Middleware Order**: Simplified to match working configuration

## Testing:

After deployment, test these URLs:
- ✅ **Home**: `https://backend.okpuja.in/`
- ✅ **Swagger**: `https://backend.okpuja.in/swagger/`
- ✅ **Admin**: `https://backend.okpuja.in/admin/`

## The Key Difference:

Your working project uses a simpler, more standard Django configuration without WhiteNoise and complex production overrides. This updated configuration follows that same pattern, which should resolve the static file serving issues that were preventing Swagger and Admin from working properly.

The main issue was over-complicating the production setup when a simpler approach (like your working project) would suffice.
