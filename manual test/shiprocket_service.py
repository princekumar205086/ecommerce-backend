"""
ShipRocket API Service for E-commerce Backend
Handles all ShipRocket API interactions in UAT mode
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from typing import Dict, List, Optional, Union
from decimal import Decimal
import traceback

# Import configuration
try:
    from shiprocket_config import (
        SHIPROCKET_BASE_URL, SHIPROCKET_EMAIL, SHIPROCKET_PASSWORD,
        SHIPROCKET_TIMEOUT, DEFAULT_PICKUP_LOCATION, DEFAULT_WEIGHT,
        DEFAULT_DIMENSIONS, SHIPROCKET_UAT
    )
except ImportError:
    # Fallback configuration
    SHIPROCKET_BASE_URL = "https://apiv2.shiprocket.in/v1/external/"
    SHIPROCKET_EMAIL = "test@example.com"
    SHIPROCKET_PASSWORD = "test123"
    SHIPROCKET_TIMEOUT = 30
    SHIPROCKET_UAT = True
    DEFAULT_PICKUP_LOCATION = {
        "pickup_location": "Primary",
        "name": "Test Company",
        "email": "test@company.com",
        "phone": "9876543210",
        "address": "Test Address",
        "city": "Delhi",
        "state": "Delhi",
        "country": "India",
        "pin_code": "110001"
    }
    DEFAULT_WEIGHT = 0.5
    DEFAULT_DIMENSIONS = {"length": 10, "breadth": 10, "height": 5}

logger = logging.getLogger(__name__)


class ShipRocketAPI:
    """
    ShipRocket API Integration Service
    Handles authentication, order creation, tracking, and other shipping operations
    """
    
    def __init__(self):
        self.base_url = SHIPROCKET_BASE_URL
        self.email = SHIPROCKET_EMAIL
        self.password = SHIPROCKET_PASSWORD
        self.timeout = SHIPROCKET_TIMEOUT
        self.token = None
        self.token_expires = None
        
    def _get_headers(self, authenticated=True):
        """Get API request headers"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'EcommercePlatform/1.0'
        }
        
        if authenticated:
            token = self._get_auth_token()
            if token:
                headers['Authorization'] = f'Bearer {token}'
                
        return headers
    
    def _get_auth_token(self):
        """Get or refresh authentication token"""
        # Check if we have a valid cached token
        cached_token = cache.get('shiprocket_auth_token')
        if cached_token:
            return cached_token
            
        # Request new token
        try:
            auth_url = f"{self.base_url}auth/login"
            auth_data = {
                "email": self.email,
                "password": self.password
            }
            
            response = requests.post(
                auth_url,
                json=auth_data,
                headers={'Content-Type': 'application/json'},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                token = result.get('token')
                
                if token:
                    # Cache token for 23 hours (tokens expire in 24 hours)
                    cache.set('shiprocket_auth_token', token, 23 * 60 * 60)
                    logger.info("ShipRocket authentication successful")
                    return token
                    
            logger.error(f"ShipRocket authentication failed: {response.status_code} - {response.text}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ShipRocket authentication error: {str(e)}")
            return None
    
    def test_connection(self):
        """Test ShipRocket API connection"""
        try:
            token = self._get_auth_token()
            if not token:
                return {
                    'success': False,
                    'message': 'Authentication failed',
                    'data': None
                }
            
            # Test with a simple API call
            url = f"{self.base_url}courier/serviceability/"
            params = {
                'pickup_postcode': '110001',
                'delivery_postcode': '110002',
                'weight': '1',
                'cod': '0'
            }
            
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'ShipRocket API connection successful',
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'message': f'API test failed: {response.status_code}',
                    'data': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection test error: {str(e)}',
                'data': None
            }
    
    def check_serviceability(self, pickup_pincode: str, delivery_pincode: str, weight: float = 1.0, cod: bool = False):
        """Check if delivery is serviceable for given pincodes"""
        try:
            url = f"{self.base_url}courier/serviceability/"
            params = {
                'pickup_postcode': pickup_pincode,
                'delivery_postcode': delivery_pincode,
                'weight': str(weight),
                'cod': '1' if cod else '0'
            }
            
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'serviceable': len(result.get('data', {}).get('available_courier_companies', [])) > 0,
                    'couriers': result.get('data', {}).get('available_courier_companies', []),
                    'message': 'Serviceability check completed'
                }
            else:
                return {
                    'success': False,
                    'serviceable': False,
                    'message': f'Serviceability check failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Serviceability check error: {str(e)}")
            return {
                'success': False,
                'serviceable': False,
                'message': f'Error: {str(e)}'
            }
    
    def create_order(self, order_data: Dict):
        """Create shipping order in ShipRocket"""
        try:
            url = f"{self.base_url}orders/create/adhoc"
            
            # Format order data for ShipRocket API
            shiprocket_order = self._format_order_data(order_data)
            
            response = requests.post(
                url,
                json=shiprocket_order,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status_code') == 1:
                    return {
                        'success': True,
                        'order_id': result.get('order_id'),
                        'shipment_id': result.get('shipment_id'),
                        'data': result,
                        'message': 'Order created successfully'
                    }
                else:
                    return {
                        'success': False,
                        'message': result.get('message', 'Order creation failed'),
                        'errors': result.get('errors', {})
                    }
            else:
                return {
                    'success': False,
                    'message': f'API error: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Order creation error: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def _format_order_data(self, order_data: Dict) -> Dict:
        """Format order data for ShipRocket API"""
        # Get default pickup location
        try:
            pickup_location = DEFAULT_PICKUP_LOCATION.copy()
        except:
            pickup_location = {
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
            }
        
        # Calculate total weight and dimensions
        try:
            default_weight = DEFAULT_WEIGHT
        except:
            default_weight = 0.5
            
        try:
            default_dimensions = DEFAULT_DIMENSIONS.copy()
        except:
            default_dimensions = {"length": 10, "breadth": 10, "height": 5}
        
        total_weight = float(order_data.get('total_weight', order_data.get('weight', default_weight)))
        dimensions = order_data.get('dimensions', default_dimensions)
        
        # Convert Decimal to float for JSON serialization
        def convert_decimal(value):
            if isinstance(value, Decimal):
                return float(value)
            return value
        
        # Format items for ShipRocket
        order_items = []
        for item in order_data.get('items', []):
            order_items.append({
                "name": item.get('name', 'Product'),
                "sku": item.get('sku', 'SKU001'),
                "units": int(item.get('quantity', 1)),
                "selling_price": convert_decimal(item.get('price', 0)),
                "discount": convert_decimal(item.get('discount', 0)),
                "tax": convert_decimal(item.get('tax', 0)),
                "hsn": item.get('hsn', 0)
            })
        
        # Build ShipRocket order structure
        shiprocket_order = {
            "order_id": str(order_data.get('order_id')),
            "order_date": order_data.get('order_date', datetime.now().strftime('%Y-%m-%d %H:%M')),
            "pickup_location": pickup_location.get('pickup_location'),
            "channel_id": "",
            "comment": order_data.get('comment', 'E-commerce order'),
            "billing_customer_name": str(order_data.get('customer_name')),
            "billing_last_name": str(order_data.get('customer_last_name', '')),
            "billing_address": str(order_data.get('billing_address')),
            "billing_address_2": str(order_data.get('billing_address_2', '')),
            "billing_city": str(order_data.get('billing_city')),
            "billing_pincode": str(order_data.get('billing_pincode')),
            "billing_state": str(order_data.get('billing_state')),
            "billing_country": str(order_data.get('billing_country', 'India')),
            "billing_email": str(order_data.get('billing_email', order_data.get('customer_email', ''))),
            "billing_phone": str(order_data.get('billing_phone', order_data.get('customer_phone', ''))),
            "shipping_is_billing": order_data.get('shipping_is_billing', True),
            "shipping_customer_name": str(order_data.get('shipping_customer_name', order_data.get('customer_name'))),
            "shipping_last_name": str(order_data.get('shipping_last_name', '')),
            "shipping_address": str(order_data.get('shipping_address', order_data.get('billing_address'))),
            "shipping_address_2": str(order_data.get('shipping_address_2', '')),
            "shipping_city": str(order_data.get('shipping_city', order_data.get('billing_city'))),
            "shipping_pincode": str(order_data.get('shipping_pincode', order_data.get('billing_pincode'))),
            "shipping_country": str(order_data.get('shipping_country', 'India')),
            "shipping_state": str(order_data.get('shipping_state', order_data.get('billing_state'))),
            "shipping_email": str(order_data.get('shipping_email', order_data.get('billing_email', order_data.get('customer_email', '')))),
            "shipping_phone": str(order_data.get('shipping_phone', order_data.get('billing_phone', order_data.get('customer_phone', '')))),
            "order_items": order_items,
            "payment_method": order_data.get('payment_method', 'Prepaid'),
            "shipping_charges": convert_decimal(order_data.get('shipping_charges', 0)),
            "giftwrap_charges": convert_decimal(order_data.get('giftwrap_charges', 0)),
            "transaction_charges": convert_decimal(order_data.get('transaction_charges', 0)),
            "total_discount": convert_decimal(order_data.get('total_discount', 0)),
            "sub_total": convert_decimal(order_data.get('sub_total')),
            "length": convert_decimal(dimensions.get('length')),
            "breadth": convert_decimal(dimensions.get('breadth')),
            "height": convert_decimal(dimensions.get('height')),
            "weight": convert_decimal(total_weight)
        }
        
        return shiprocket_order
    
    def track_shipment(self, shipment_id: str):
        """Track shipment by shipment ID"""
        try:
            url = f"{self.base_url}courier/track/shipment/{shipment_id}"
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'tracking_data': result,
                    'message': 'Tracking data retrieved successfully'
                }
            else:
                return {
                    'success': False,
                    'message': f'Tracking failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Tracking error: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def cancel_shipment(self, awb_numbers: List[str]):
        """Cancel shipment(s)"""
        try:
            url = f"{self.base_url}orders/cancel/shipment/awbs"
            data = {"awbs": awb_numbers}
            
            response = requests.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'data': result,
                    'message': 'Shipment cancellation requested'
                }
            else:
                return {
                    'success': False,
                    'message': f'Cancellation failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Cancellation error: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_invoice(self, order_ids: List[str]):
        """Generate invoice for orders"""
        try:
            url = f"{self.base_url}orders/print/invoice"
            data = {"ids": order_ids}
            
            response = requests.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'invoice_url': result.get('invoice_url'),
                    'data': result,
                    'message': 'Invoice generated successfully'
                }
            else:
                return {
                    'success': False,
                    'message': f'Invoice generation failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Invoice generation error: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_shipping_rates(self, pickup_pincode: str, delivery_pincode: str, weight: float, dimensions: Dict):
        """Get shipping rates from different couriers"""
        try:
            url = f"{self.base_url}courier/serviceability/"
            params = {
                'pickup_postcode': pickup_pincode,
                'delivery_postcode': delivery_pincode,
                'weight': str(weight),
                'cod': '0'
            }
            
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                couriers = result.get('data', {}).get('available_courier_companies', [])
                
                # Sort by freight charges
                couriers.sort(key=lambda x: float(x.get('freight_charge', 0)))
                
                return {
                    'success': True,
                    'rates': couriers,
                    'cheapest': couriers[0] if couriers else None,
                    'message': 'Shipping rates retrieved successfully'
                }
            else:
                return {
                    'success': False,
                    'message': f'Rate check failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Rate check error: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }


# Singleton instance
shiprocket_api = ShipRocketAPI()