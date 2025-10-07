# ShipRocket API Integration Settings
import os

# ShipRocket Production Environment Configuration
SHIPROCKET_UAT = False  # Set to False for production
SHIPROCKET_BASE_URL = "https://apiv2.shiprocket.in/v1/external/"

# Production Credentials (from .env file)
SHIPROCKET_EMAIL = os.environ.get('SHIPROCKET_EMAIL', 'your-email@example.com')
SHIPROCKET_PASSWORD = os.environ.get('SHIPROCKET_PASSWORD', 'your-password')

# API Configuration
SHIPROCKET_TIMEOUT = 30  # API request timeout in seconds
SHIPROCKET_RETRY_ATTEMPTS = 3

# Webhook Configuration
SHIPROCKET_WEBHOOK_URL = "https://backend.okpuja.in/api/shiprocket/webhook/"

# Default Shipping Configuration (from .env file)
DEFAULT_PICKUP_LOCATION = {
    "pickup_location": "Primary",
    "name": "MedixMall",
    "email": "pickup@medixmall.com",
    "phone": "9876543210",
    "address": "123 Test Street, Business Park",
    "address_2": "Near Test Mall",
    "city": "Purnia",
    "state": "Bihar",
    "country": "India",
    "pin_code": "854301"
}

# COD Settings
COD_CHARGES = 25  # COD handling charges
INSURANCE_CHARGES = 0  # Insurance charges

# Weight Configuration (in kg)
DEFAULT_WEIGHT = 0.5  # Default weight if not specified
MAX_WEIGHT = 30  # Maximum weight allowed

# Dimensions Configuration (in cm)
DEFAULT_DIMENSIONS = {
    "length": 10,
    "breadth": 10,
    "height": 5
}