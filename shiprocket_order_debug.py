"""
ShipRocket Order Creation Debug Test
Focuses on fixing the order creation endpoint that's returning 400 Bad Request
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShipRocketOrderDebugger:
    def __init__(self):
        self.base_url = "https://apiv2.shiprocket.in/v1/external/"
        self.email = "avengerprinceraj@gmail.com"
        self.password = "N4nWsj1R^u@IJZHp"
        self.token = None
        
    def authenticate(self):
        """Get authentication token"""
        try:
            response = requests.post(
                f"{self.base_url}auth/login",
                json={
                    "email": self.email,
                    "password": self.password
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def get_pickup_locations(self):
        """Get available pickup locations"""
        try:
            response = requests.get(
                f"{self.base_url}settings/company/pickup",
                headers={
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Pickup locations retrieved successfully")
                print("Available Pickup Locations:")
                for location in data.get('data', []):
                    print(f"- {location.get('pickup_location')} ({location.get('city')})")
                return data.get('data', [])
            else:
                logger.error(f"Failed to get pickup locations: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting pickup locations: {e}")
            return []
    
    def test_minimal_order(self):
        """Test with minimal required fields"""
        order_data = {
            "order_id": f"TEST_MIN_{int(datetime.now().timestamp())}",
            "order_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "pickup_location": "Primary",
            "billing_customer_name": "John",
            "billing_last_name": "Doe", 
            "billing_address": "123 Test Street",
            "billing_city": "New Delhi",
            "billing_pincode": "110001",
            "billing_state": "Delhi",
            "billing_country": "India",
            "billing_email": "john.doe@test.com",
            "billing_phone": "9876543210",
            "shipping_is_billing": True,
            "order_items": [
                {
                    "name": "Test Product",
                    "sku": "TEST001",
                    "units": 1,
                    "selling_price": 100,
                    "discount": 0,
                    "tax": 0,
                    "hsn": 0
                }
            ],
            "payment_method": "Prepaid",
            "sub_total": 100,
            "length": 10,
            "breadth": 10,
            "height": 5,
            "weight": 0.5
        }
        
        return self._test_order_creation(order_data, "Minimal Order")
    
    def test_complete_order(self):
        """Test with all fields properly filled"""
        order_data = {
            "order_id": f"TEST_COMPLETE_{int(datetime.now().timestamp())}",
            "order_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "pickup_location": "Primary",
            "channel_id": "",
            "comment": "Test order from API",
            "billing_customer_name": "John",
            "billing_last_name": "Doe",
            "billing_address": "123 Test Street, Sector 1",
            "billing_address_2": "Near Test Mall",
            "billing_city": "New Delhi", 
            "billing_pincode": "110001",
            "billing_state": "Delhi",
            "billing_country": "India",
            "billing_email": "john.doe@test.com",
            "billing_phone": "9876543210",
            "shipping_is_billing": True,
            "shipping_customer_name": "John",
            "shipping_last_name": "Doe",
            "shipping_address": "123 Test Street, Sector 1",
            "shipping_address_2": "Near Test Mall",
            "shipping_city": "New Delhi",
            "shipping_pincode": "110001",
            "shipping_country": "India",
            "shipping_state": "Delhi",
            "shipping_email": "john.doe@test.com",
            "shipping_phone": "9876543210",
            "order_items": [
                {
                    "name": "Test Product 1",
                    "sku": "TEST-SKU-001",
                    "units": 2,
                    "selling_price": 100.00,
                    "discount": 10.00,
                    "tax": 18.00,
                    "hsn": 1234
                }
            ],
            "payment_method": "Prepaid",
            "shipping_charges": 50.00,
            "giftwrap_charges": 0.00,
            "transaction_charges": 5.00,
            "total_discount": 10.00,
            "sub_total": 213.00,  # (100*2 - 10 + 18 + 50 + 5)
            "length": 15.0,
            "breadth": 10.0, 
            "height": 8.0,
            "weight": 1.5
        }
        
        return self._test_order_creation(order_data, "Complete Order")
    
    def test_cod_order(self):
        """Test COD order"""
        order_data = {
            "order_id": f"TEST_COD_{int(datetime.now().timestamp())}",
            "order_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "pickup_location": "Primary",
            "billing_customer_name": "Jane",
            "billing_last_name": "Smith",
            "billing_address": "456 COD Street",
            "billing_city": "Mumbai",
            "billing_pincode": "400001",
            "billing_state": "Maharashtra", 
            "billing_country": "India",
            "billing_email": "jane.smith@test.com",
            "billing_phone": "9876543211",
            "shipping_is_billing": True,
            "order_items": [
                {
                    "name": "COD Product",
                    "sku": "COD001", 
                    "units": 1,
                    "selling_price": 200,
                    "discount": 0,
                    "tax": 36,
                    "hsn": 0
                }
            ],
            "payment_method": "COD",
            "sub_total": 236,
            "length": 12,
            "breadth": 12,
            "height": 6,
            "weight": 1.0
        }
        
        return self._test_order_creation(order_data, "COD Order")
    
    def _test_order_creation(self, order_data, test_name):
        """Test order creation with given data"""
        try:
            logger.info(f"Testing {test_name}...")
            
            response = requests.post(
                f"{self.base_url}orders/create/adhoc",
                json=order_data,
                headers={
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            print(f"\n=== {test_name} ===")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status_code') == 1:
                    logger.info(f"{test_name} created successfully!")
                    return {
                        'success': True,
                        'order_id': result.get('order_id'),
                        'shipment_id': result.get('shipment_id'),
                        'data': result
                    }
                else:
                    logger.error(f"{test_name} failed: {result.get('message')}")
                    return {
                        'success': False,
                        'error': result.get('message'),
                        'errors': result.get('errors', {})
                    }
            else:
                logger.error(f"{test_name} failed with status {response.status_code}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"{test_name} exception: {e}")
            return {
                'success': False,
                'exception': str(e)
            }
    
    def run_debug_tests(self):
        """Run all debug tests"""
        print("ShipRocket Order Creation Debug Test")
        print("=" * 50)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("Authentication failed. Cannot proceed.")
            return
        
        # Step 2: Get pickup locations
        pickup_locations = self.get_pickup_locations()
        
        # Step 3: Test different order configurations
        tests = [
            self.test_minimal_order,
            self.test_complete_order, 
            self.test_cod_order
        ]
        
        results = []
        for test in tests:
            result = test()
            results.append(result)
        
        # Summary
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]
        
        print(f"Total Tests: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if failed:
            print("\nFailed Tests:")
            for i, result in enumerate(failed):
                print(f"{i+1}. Error: {result.get('error', 'Unknown error')}")
                if 'errors' in result:
                    print(f"   Details: {result['errors']}")
        
        if successful:
            print("\nSuccessful Orders:")
            for i, result in enumerate(successful):
                print(f"{i+1}. Order ID: {result.get('order_id')}")
                print(f"   Shipment ID: {result.get('shipment_id')}")


if __name__ == "__main__":
    debugger = ShipRocketOrderDebugger()
    debugger.run_debug_tests()