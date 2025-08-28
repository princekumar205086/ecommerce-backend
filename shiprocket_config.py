# ShipRocket API Integration Settings

# ShipRocket UAT/Test Environment Configuration
SHIPROCKET_UAT = True  # Set to False for production
SHIPROCKET_BASE_URL = "https://apiv2.shiprocket.in/v1/external/"

# UAT Test Credentials (Update these with your actual UAT credentials)
# For testing, you need to register at https://app.shiprocket.in/ and get UAT access
SHIPROCKET_EMAIL = "demo@example.com"  # Replace with your actual UAT email
SHIPROCKET_PASSWORD = "demo123"  # Replace with your actual UAT password

# API Configuration
SHIPROCKET_TIMEOUT = 30  # API request timeout in seconds
SHIPROCKET_RETRY_ATTEMPTS = 3

# Webhook Configuration
SHIPROCKET_WEBHOOK_URL = "https://your-domain.com/api/shiprocket/webhook/"

# Default Shipping Configuration
DEFAULT_PICKUP_LOCATION = {
    "pickup_location": "Primary",
    "name": "Test Ecommerce Company",
    "email": "pickup@testecommerce.com",
    "phone": "9876543210",
    "address": "123 Test Street, Business Park",
    "address_2": "Near Test Mall",
    "city": "New Delhi",
    "state": "Delhi",
    "country": "India",
    "pin_code": "110001"
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