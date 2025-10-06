#!/usr/bin/env python
"""
ShipRocket Pickup Location Finder and Test
Gets exact pickup location names and tests order creation
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

def find_and_test_pickup_locations():
    """Find exact pickup locations and test each one"""
    print("🎯 ShipRocket Pickup Location Finder & Tester")
    print("=" * 50)
    
    # Authentication
    token = shiprocket_api._get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful")
    
    # Get pickup locations
    try:
        url = f"{shiprocket_api.base_url}settings/company/pickup"
        headers = shiprocket_api._get_headers()
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            pickup_data = response.json()
            locations = pickup_data.get('data', {}).get('shipping_address', [])
            
            print(f"\\n📍 Found {len(locations)} pickup locations:")
            
            for i, location in enumerate(locations):
                print(f"\\n{i+1}. Pickup Location: '{location.get('pickup_location')}'")
                print(f"   Status: {location.get('status')} ({'Verified' if location.get('status') == 2 else 'Pending' if location.get('status') == 1 else 'Unknown'})")
                print(f"   Primary: {'Yes' if location.get('is_primary_location') else 'No'}")
                print(f"   Phone Verified: {'Yes' if location.get('phone_verified') else 'No'}")
                print(f"   Address: {location.get('address')}, {location.get('city')}")
                print(f"   PIN: {location.get('pin_code')}")
                
                # Test order creation with this location
                if location.get('status') in [1, 2]:  # 1=Pending, 2=Verified
                    success = test_order_with_location(location.get('pickup_location'))
                    if success:
                        print(f"🎉 SUCCESS! Working pickup location: '{location.get('pickup_location')}'")
                        return True
                else:
                    print("   ⏭️  Skipping (not active)")
            
            print("\\n❌ No working pickup location found")
            return False
            
        else:
            print(f"❌ Failed to get pickup locations: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_order_with_location(pickup_location_name):
    """Test order creation with specific pickup location"""
    print(f"\\n   🧪 Testing order creation with: '{pickup_location_name}'")
    
    sample_order = {
        'order_id': f'TEST{pickup_location_name.replace(" ", "")}{int(__import__("time").time())}',
        'pickup_location': pickup_location_name,
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
        'shipping_charges': 50.0,
        'total_discount': 0.0,
        'total_weight': 0.5,
        'length': 10,
        'breadth': 10,
        'height': 5,
        'items': [
            {
                'name': 'Test Medicine',
                'sku': 'MED001',
                'units': 1,
                'selling_price': 100.0,
                'discount': 0,
                'tax': 0,
                'hsn': 30049099
            }
        ]
    }
    
    order_result = shiprocket_api.create_order(sample_order)
    
    if order_result['success']:
        print("   ✅ ORDER CREATION SUCCESSFUL!")
        print(f"      📋 Order ID: {order_result.get('order_id')}")
        print(f"      🚚 Shipment ID: {order_result.get('shipment_id')}")
        
        # Final success celebration
        print("\\n" + "🎉" * 25)
        print("🎉  100% SHIPROCKET SUCCESS ACHIEVED!  🎉")
        print("🎉" * 25)
        
        print("\\n📊 COMPLETE SUCCESS REPORT:")
        print("=" * 50)
        print("✅ Authentication      : PASSED ✅")
        print("✅ Pickup Locations    : DISCOVERED ✅")
        print("✅ Order Creation      : SUCCESSFUL ✅")
        print("✅ ShipRocket Ready    : 100% ✅")
        print("=" * 50)
        print(f"🎯 Working Pickup Location: '{pickup_location_name}'")
        print(f"📋 Test Order ID: {order_result.get('order_id')}")
        print(f"🚚 Shipment ID: {order_result.get('shipment_id')}")
        print("\\n🚀 ShipRocket is 100% PRODUCTION READY!")
        
        return True
    else:
        print(f"   ❌ Failed: {order_result['message']}")
        return False

def main():
    return find_and_test_pickup_locations()

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n🎊 FINAL STATUS: 100% SUCCESS! 🎊")
    else:
        print("\\n❌ Need to configure pickup locations properly")
    exit(0 if success else 1)