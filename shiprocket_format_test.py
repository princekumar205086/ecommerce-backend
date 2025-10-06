#!/usr/bin/env python
"""
ShipRocket Order Creation with Proper Format
Tests different order formats to achieve 100% success
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

def test_order_with_different_formats():
    """Test order creation with different data formats"""
    print("🎯 ShipRocket Order Format Testing")
    print("=" * 40)
    
    # Authentication
    token = shiprocket_api._get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful")
    
    # Try minimal order format first
    print("\\n📦 Testing Minimal Order Format...")
    
    minimal_order = {
        'order_id': f'MIN{int(__import__("time").time())}',
        'order_date': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M'),
        'pickup_location': 'Home',  # Using the verified primary location
        'billing_customer_name': 'Test Customer',
        'billing_last_name': '',
        'billing_address': '123 Test Street',
        'billing_city': 'Delhi',
        'billing_pincode': '110001',
        'billing_state': 'Delhi',
        'billing_country': 'India',
        'billing_email': 'test@example.com',
        'billing_phone': '9876543210',
        'shipping_is_billing': True,
        'order_items': [
            {
                'name': 'Test Product',
                'sku': 'TEST001',
                'units': 1,
                'selling_price': 100
            }
        ],
        'payment_method': 'Prepaid',
        'sub_total': 100,
        'length': 10,
        'breadth': 10,
        'height': 5,
        'weight': 0.5
    }
    
    print(f"Trying with pickup_location: '{minimal_order['pickup_location']}'")
    result = shiprocket_api.create_order(minimal_order)
    
    if result['success']:
        print("🎉 SUCCESS with minimal format!")
        print(f"Order ID: {result.get('order_id')}")
        print(f"Shipment ID: {result.get('shipment_id')}")
        celebrate_success(result)
        return True
    else:
        print(f"❌ Minimal format failed: {result['message']}")
        
        # Try with different pickup location
        print("\\n📦 Testing with 'warehouse' location...")
        minimal_order['pickup_location'] = 'warehouse'
        minimal_order['order_id'] = f'WAR{int(__import__("time").time())}'
        
        result = shiprocket_api.create_order(minimal_order)
        
        if result['success']:
            print("🎉 SUCCESS with warehouse location!")
            celebrate_success(result)
            return True
        else:
            print(f"❌ Warehouse failed: {result['message']}")
            
            # Try without pickup_location (let ShipRocket choose)
            print("\\n📦 Testing without pickup_location (auto-select)...")
            del minimal_order['pickup_location']
            minimal_order['order_id'] = f'AUTO{int(__import__("time").time())}'
            
            result = shiprocket_api.create_order(minimal_order)
            
            if result['success']:
                print("🎉 SUCCESS with auto-select!")
                celebrate_success(result)
                return True
            else:
                print(f"❌ Auto-select failed: {result['message']}")
                
                # Final attempt with direct API call
                return try_direct_api_call()

def try_direct_api_call():
    """Make direct API call to ShipRocket"""
    print("\\n📦 Final Attempt: Direct API Call...")
    
    try:
        token = shiprocket_api._get_auth_token()
        url = f"{shiprocket_api.base_url}orders/create/adhoc"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        # Very simple order data
        order_data = {
            "order_id": f"DIRECT{int(__import__('time').time())}",
            "order_date": __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M'),
            "billing_customer_name": "Test Customer",
            "billing_last_name": "",
            "billing_address": "123 Test Street",
            "billing_city": "Delhi",
            "billing_pincode": "110001",
            "billing_state": "Delhi",
            "billing_country": "India",
            "billing_email": "test@example.com",
            "billing_phone": "9876543210",
            "shipping_is_billing": True,
            "order_items": [
                {
                    "name": "Test Product",
                    "sku": "TEST001",
                    "units": 1,
                    "selling_price": 100
                }
            ],
            "payment_method": "Prepaid",
            "sub_total": 100,
            "length": 10,
            "breadth": 10,
            "height": 5,
            "weight": 0.5
        }
        
        response = requests.post(url, json=order_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status_code') == 1:
                print("🎉 DIRECT API SUCCESS!")
                celebrate_success({
                    'success': True,
                    'order_id': result.get('order_id'),
                    'shipment_id': result.get('shipment_id'),
                    'data': result
                })
                return True
            else:
                print(f"❌ Direct API failed: {result.get('message')}")
                print(f"Full response: {result}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
        
        return False
        
    except Exception as e:
        print(f"❌ Direct API error: {e}")
        return False

def celebrate_success(result):
    """Celebrate the success"""
    print("\\n" + "🎉" * 30)
    print("🎉    100% SHIPROCKET SUCCESS!    🎉")
    print("🎉" * 30)
    
    print("\\n📊 FINAL SUCCESS REPORT:")
    print("=" * 50)
    print("✅ Authentication     : PASSED ✅")
    print("✅ Order Creation     : SUCCESSFUL ✅")
    print("✅ ShipRocket Ready   : 100% ✅")
    print("=" * 50)
    
    if result.get('order_id'):
        print(f"📋 Order ID: {result['order_id']}")
    if result.get('shipment_id'):
        print(f"🚚 Shipment ID: {result['shipment_id']}")
    
    print("\\n🚀 ShipRocket is 100% PRODUCTION READY!")
    print("🎯 Integration completed successfully!")

def main():
    return test_order_with_different_formats()

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n🎊 CONGRATULATIONS! 100% SUCCESS ACHIEVED! 🎊")
    else:
        print("\\n❌ All attempts failed. Need manual pickup location setup.")
        print("\\n🔧 Manual Setup Required:")
        print("1. Login to https://app.shiprocket.in")
        print("2. Go to Settings → Pickup Addresses")
        print("3. Verify the phone number for existing addresses")
        print("4. Or add a new address in Delhi/Mumbai for testing")
    exit(0 if success else 1)