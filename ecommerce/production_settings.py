"""
Production settings for the eCommerce backend
Override specific settings for production deployment
"""

from .settings import *
import os

# Force DEBUG to be environment-controlled
DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 'yes']

# Static files configuration for production
# WhiteNoise is already configured in main settings.py

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    
    # CORS settings for production
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        'https://medixmall.vercel.app',
        'https://backend.okpuja.in',
    ]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
