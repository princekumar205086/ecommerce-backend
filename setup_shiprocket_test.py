#!/usr/bin/env python3
"""
Quick setup script for ShipRocket UAT testing
This will configure the system with test credentials for immediate testing
"""

import os
import sys

# Add Django project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

def setup_test_credentials():
    """Setup test credentials for immediate testing"""
    
    # Update shiprocket_config.py with test credentials
    config_content = '''# ShipRocket API Integration Settings

# ShipRocket UAT/Test Environment Configuration
SHIPROCKET_UAT = True  # Set to False for production
SHIPROCKET_BASE_URL = "https://apiv2.shiprocket.in/v1/external/"

# UAT Test Credentials (These are demo credentials for testing)
SHIPROCKET_EMAIL = "test@shiprocket.co"  # Replace with your actual UAT email
SHIPROCKET_PASSWORD = "test123"  # Replace with your actual UAT password

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
}'''
    
    try:
        with open('shiprocket_config.py', 'w') as f:
            f.write(config_content)
        
        print("✅ Test configuration created!")
        print("📝 File: shiprocket_config.py")
        print("\n⚠️  IMPORTANT:")
        print("   1. Replace test credentials with your actual ShipRocket UAT credentials")
        print("   2. Update pickup location details with your company information")
        print("   3. Test the integration using: python test_shiprocket_uat.py")
        print("\n🔧 To get UAT credentials:")
        print("   1. Sign up at https://shiprocket.co/")
        print("   2. Request UAT access from ShipRocket support")
        print("   3. Update SHIPROCKET_EMAIL and SHIPROCKET_PASSWORD")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating config: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up ShipRocket UAT test configuration...")
    if setup_test_credentials():
        print("\n🎉 Setup complete! Ready for testing.")
    else:
        print("\n❌ Setup failed!")