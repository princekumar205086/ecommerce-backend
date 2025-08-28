"""
Django management command to setup ShipRocket configuration
"""

from django.core.management.base import BaseCommand
from shipping.models import ShippingProvider
import json

class Command(BaseCommand):
    help = 'Setup ShipRocket shipping provider configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='ShipRocket account email',
            required=True
        )
        parser.add_argument(
            '--password',
            type=str,
            help='ShipRocket account password',
            required=True
        )
        parser.add_argument(
            '--uat',
            action='store_true',
            help='Setup for UAT/test environment'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        is_uat = options['uat']
        
        # Create or update ShipRocket provider
        provider, created = ShippingProvider.objects.get_or_create(
            name='ShipRocket',
            defaults={
                'is_active': True,
                'api_config': {
                    'email': email,
                    'password': password,
                    'is_uat': is_uat,
                    'base_url': 'https://apiv2.shiprocket.in/v1/external/',
                    'timeout': 30,
                    'retry_attempts': 3
                }
            }
        )
        
        if not created:
            # Update existing provider
            provider.api_config.update({
                'email': email,
                'password': password,
                'is_uat': is_uat
            })
            provider.save()
        
        # Update shiprocket_config.py file
        config_content = f'''# ShipRocket API Integration Settings

# ShipRocket UAT/Test Environment Configuration
SHIPROCKET_UAT = {is_uat}
SHIPROCKET_BASE_URL = "https://apiv2.shiprocket.in/v1/external/"

# Credentials
SHIPROCKET_EMAIL = "{email}"
SHIPROCKET_PASSWORD = "{password}"

# API Configuration
SHIPROCKET_TIMEOUT = 30
SHIPROCKET_RETRY_ATTEMPTS = 3

# Webhook Configuration
SHIPROCKET_WEBHOOK_URL = "https://your-domain.com/api/shiprocket/webhook/"

# Default Pickup Location (Update with your details)
DEFAULT_PICKUP_LOCATION = {{
    "pickup_location": "Primary",
    "name": "Your Company Name",
    "email": "pickup@yourcompany.com",
    "phone": "9876543210",
    "address": "Your Company Address",
    "address_2": "",
    "city": "Your City",
    "state": "Your State",
    "country": "India",
    "pin_code": "110001"
}}

# COD Settings
COD_CHARGES = 25
INSURANCE_CHARGES = 0

# Weight Configuration (in kg)
DEFAULT_WEIGHT = 0.5
MAX_WEIGHT = 30

# Dimensions Configuration (in cm)
DEFAULT_DIMENSIONS = {{
    "length": 10,
    "breadth": 10,
    "height": 5
}}'''
        
        try:
            with open('shiprocket_config.py', 'w') as f:
                f.write(config_content)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ ShipRocket provider {"created" if created else "updated"} successfully!'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'📧 Email: {email}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'🧪 UAT Mode: {is_uat}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'📝 Configuration file updated: shiprocket_config.py'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Please update DEFAULT_PICKUP_LOCATION in shiprocket_config.py with your actual pickup details'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error updating config file: {e}')
            )