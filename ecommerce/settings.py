import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Frontend URL for email templates
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Use environment variable for ALLOWED_HOSTS or default to localhost
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'testserver',  # Added for Django test client
    'ecommerce-backend-77dc.onrender.com',
    'backend.okpuja.in',
    '157.173.221.192',
    'https://medixmall.com',
    'https://www.medixmall.com'
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_yasg',

    # Local apps
    'accounts',
    'products',
    'cart',
    'core',
    'coupon',
    'orders',
    'payments',
    'notifications',
    'adminpanel',
    'cms',
    'analytics',
    'invoice',
    'support',
    'wishlist',
    'shipping',
    'inventory',
    'reviews',
    'rx_upload',  # RX Verifier System for prescription management
    'corsheaders',
    'taggit'
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.1:3000',
    'https://medixmall.vercel.app',
    'https://medixmall.com',
    'https://www.medixmall.com'
]

CSRF_TRUSTED_ORIGINS = [
    'https://backend.okpuja.in',
    'https://medixmall.vercel.app',
    'http://127.0.1:3000',
    'https://127.0.0.1:8000/',
    'http://localhost:3000',
    'https://medixmall.com',
    'https://www.medixmall.com'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Optional
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Use PostgreSQL in production
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static and media files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise configuration for static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# DRF Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

# Allow larger request body in Django so that Django can validate file sizes
# (Nginx/proxy may still reject requests if their limits are smaller)
# Set to 10 MB so app can accept files up to this and then enforce 2 MB at app level
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # Short-lived access tokens
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # Long-lived refresh tokens
    'ROTATE_REFRESH_TOKENS': True,                   # Auto-rotate refresh tokens
    'BLACKLIST_AFTER_ROTATION': True,               # Blacklist old tokens
    'UPDATE_LAST_LOGIN': True,                       # Update last login on token refresh
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=15),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# Custom User model
AUTH_USER_MODEL = 'accounts.User'

# Login URL for Django authentication redirects
LOGIN_URL = '/api/accounts/login/'

# Swagger settings
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
        'patch'
    ],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'SHOW_COMMON_EXTENSIONS': True,
}

# ReDoc settings
REDOC_SETTINGS = {
    'LAZY_RENDERING': False,
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Razorpay Configuration
RAZORPAY_API_KEY = os.environ.get('RAZORPAY_API_KEY', 'rzp_test_your_key_here')
RAZORPAY_API_SECRET = os.environ.get('RAZORPAY_API_SECRET', 'your_razorpay_secret_here')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', 'your_webhook_secret_here')
APP_NAME = os.environ.get('APP_NAME', 'Ecommerce')

# imagekitio configuration

IMAGEKIT_URL_ENDPOINT = os.environ.get('IMAGEKIT_URL_ENDPOINT')
IMAGEKIT_PUBLIC_KEY = os.environ.get('IMAGEKIT_PUBLIC_KEY')
IMAGEKIT_PRIVATE_KEY = os.environ.get('IMAGEKIT_PRIVATE_KEY')

# Email smtp Configuration
# SMTP backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', os.environ.get('EMAIL_HOST_USER', 'medixmallstore@gmail.com'))

# For testing only: Use console backend to avoid Gmail limits
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

SECURE_SSL_REDIRECT = False
