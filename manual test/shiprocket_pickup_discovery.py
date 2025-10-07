#!/usr/bin/env python
"""
ShipRocket Pickup Locations Discovery
Gets available pickup locations from ShipRocket API
"""

import sys
import os
import django
import requests

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from shiprocket_service import shiprocket_api

def get_shiprocket_pickup_locations():
    """Get available pickup locations from ShipRocket API"""
    print("🚚 Discovering ShipRocket Pickup Locations...")
    print("=" * 50)
    
    # Get auth token
    token = shiprocket_api._get_auth_token()
    if not token:
        print("❌ Failed to authenticate with ShipRocket")
        return False
    
    print("✅ Authentication successful")
    
    # Get pickup locations
    try:
        url = f"{shiprocket_api.base_url}settings/company/pickup"
        headers = shiprocket_api._get_headers()
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            pickup_data = response.json()
            print(f"\\n📍 Available Pickup Locations:")
            
            # Handle different response formats
            locations = []
            if isinstance(pickup_data, dict):
                if 'data' in pickup_data:
                    locations = pickup_data['data']
                elif 'pickup_location' in pickup_data:
                    locations = pickup_data['pickup_location']
                else:
                    locations = [pickup_data]
            elif isinstance(pickup_data, list):
                locations = pickup_data
            
            if locations:
                print(f"Found {len(locations)} pickup locations:")
                for i, location in enumerate(locations):
                    print(f"\\n{i+1}. {location.get('pickup_location', 'Unknown')}")
                    print(f"   Address: {location.get('address', 'N/A')}")
                    print(f"   City: {location.get('city', 'N/A')}")
                    print(f"   State: {location.get('state', 'N/A')}")
                    print(f"   PIN: {location.get('pin_code', 'N/A')}")
                    print(f"   Phone: {location.get('phone', 'N/A')}")
                
                # Test order creation with first available location
                if locations:
                    return test_order_with_pickup_location(locations[0])
            else:
                print("❌ No pickup locations found")
                print("\\n🔧 You need to add a pickup location in ShipRocket dashboard:")
                print("   1. Go to https://app.shiprocket.in")
                print("   2. Settings → Pickup Addresses")
                print("   3. Add New Address")
                return create_pickup_location_via_api()
                
        else:
            print(f"❌ Failed to get pickup locations: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try to create a pickup location
            return create_pickup_location_via_api()
            
    except Exception as e:
        print(f"❌ Error getting pickup locations: {e}")
        return create_pickup_location_via_api()

def create_pickup_location_via_api():
    """Create pickup location via API"""
    print("\\n🔧 Creating pickup location via API...")
    
    try:
        token = shiprocket_api._get_auth_token()
        url = f"{shiprocket_api.base_url}settings/company/addpickup"
        headers = shiprocket_api._get_headers()
        
        pickup_data = {
            "pickup_location": "MedixMall Primary",
            "name": "MedixMall",
            "email": "pickup@medixmall.com",
            "phone": "9876543210",
            "address": "123 Business Park, Tech Hub",
            "address_2": "Near Metro Station",
            "city": "Purnia",
            "state": "Bihar",
            "country": "India",
            "pin_code": "854301"
        }
        
        response = requests.post(url, json=pickup_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Pickup location created successfully!")
            print(f"Response: {result}")
            
            # Now test order creation
            return test_order_with_pickup_location({
                "pickup_location": "MedixMall Primary",
                "city": "Purnia",
                "state": "Bihar",
                "pin_code": "854301"
            })
        else:
            print(f"❌ Failed to create pickup location: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating pickup location: {e}")
        return False

def test_order_with_pickup_location(pickup_location):
    """Test order creation with specific pickup location"""
    print(f"\\n📦 Testing order creation with pickup location: {pickup_location.get('pickup_location', 'Unknown')}")
    
    sample_order = {
        'order_id': f'TEST{int(__import__("time").time())}',
        'pickup_location': pickup_location.get('pickup_location'),
        'customer_name': 'Test Customer',
        'customer_email': 'test@example.com',
        'customer_phone': '9876543210',
        'billing_address': '123 Test Street',
        'billing_city': 'Delhi',
        'billing_state': 'Delhi',
        'billing_pincode': '110001',
        'shipping_address': '123 Test Street',
        'shipping_city': 'Delhi',
        'shipping_state': 'Delhi',
        'shipping_pincode': '110001',
        'payment_method': 'Prepaid',
        'sub_total': 100.0,
        'total_weight': 0.5,
        'items': [
            {
                'name': 'Test Product',
                'sku': 'TEST001',
                'units': 1,
                'selling_price': 100.0,
                'discount': 0,
                'tax': 0,
                'hsn': 0
            }
        ]
    }
    
    order_result = shiprocket_api.create_order(sample_order)
    
    if order_result['success']:
        print("🎉 ORDER CREATION SUCCESSFUL!")
        print(f"   Order ID: {order_result.get('order_id')}")
        print(f"   Shipment ID: {order_result.get('shipment_id')}")
        
        # Test tracking
        if order_result.get('shipment_id'):
            print("\\n🔍 Testing tracking...")
            tracking = shiprocket_api.track_shipment(order_result['shipment_id'])
            if tracking['success']:
                print("✅ Tracking successful!")
            else:
                print(f"⚠️  Tracking: {tracking['message']}")
        
        print("\\n🎉 100% SHIPROCKET SUCCESS ACHIEVED!")
        return True
    else:
        print(f"❌ Order creation failed: {order_result['message']}")
        if 'errors' in order_result:
            print(f"   Errors: {order_result['errors']}")
        return False

def main():
    return get_shiprocket_pickup_locations()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)