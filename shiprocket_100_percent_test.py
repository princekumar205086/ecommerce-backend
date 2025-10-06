#!/usr/bin/env python
"""
ShipRocket 100% Success Test
Tests multiple pickup locations to achieve 100% success
"""

import sys
import os
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from shiprocket_service import shiprocket_api

def test_with_different_pickup_locations():
    """Test ShipRocket with different pickup locations to find working one"""
    print("🚚 Testing ShipRocket with Multiple Pickup Locations...")
    print("=" * 60)
    
    # Test pickup locations that are commonly pre-verified
    test_locations = [
        {
            "name": "Delhi Hub",
            "pincode": "110001",
            "city": "New Delhi",
            "state": "Delhi"
        },
        {
            "name": "Mumbai Hub", 
            "pincode": "400001",
            "city": "Mumbai",
            "state": "Maharashtra"
        },
        {
            "name": "Bangalore Hub",
            "pincode": "560001", 
            "city": "Bangalore",
            "state": "Karnataka"
        },
        {
            "name": "Chennai Hub",
            "pincode": "600001",
            "city": "Chennai", 
            "state": "Tamil Nadu"
        }
    ]
    
    # 1. Test authentication first
    print("\\n🔐 Testing Authentication...")
    connection_test = shiprocket_api.test_connection()
    
    if not connection_test['success']:
        print(f"❌ Authentication failed: {connection_test['message']}")
        return False
    
    print("✅ ShipRocket authentication successful!")
    
    # 2. Test each pickup location
    successful_location = None
    
    for location in test_locations:
        print(f"\\n📍 Testing {location['name']} ({location['pincode']})...")
        
        # Test serviceability from this location
        serviceability = shiprocket_api.check_serviceability(
            pickup_pincode=location['pincode'],
            delivery_pincode='110002',  # Delhi delivery
            weight=1.0,
            cod=False
        )
        
        if serviceability['success'] and serviceability['serviceable']:
            print(f"✅ {location['name']}: Serviceable with {len(serviceability.get('couriers', []))} couriers")
            
            # Try order creation with this location
            sample_order = {
                'order_id': f'TEST{location["pincode"]}{int(__import__("time").time())}',
                'customer_name': 'Test Customer',
                'customer_email': 'test@example.com',
                'customer_phone': '9876543210',
                'billing_address': '123 Test Street',
                'billing_city': 'Delhi',
                'billing_state': 'Delhi',
                'billing_pincode': '110002',
                'shipping_address': '123 Test Street',
                'shipping_city': 'Delhi',
                'shipping_state': 'Delhi',
                'shipping_pincode': '110002',
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
            
            # Override pickup location in the order
            sample_order.update({
                'pickup_location': location['name'],
                'pickup_postcode': location['pincode']
            })
            
            order_result = shiprocket_api.create_order(sample_order)
            
            if order_result['success']:
                print(f"🎉 ORDER CREATION SUCCESSFUL with {location['name']}!")
                print(f"   Order ID: {order_result.get('order_id')}")
                print(f"   Shipment ID: {order_result.get('shipment_id')}")
                successful_location = location
                
                # Test tracking
                if order_result.get('shipment_id'):
                    print("\\n🔍 Testing Tracking...")
                    tracking = shiprocket_api.track_shipment(order_result['shipment_id'])
                    if tracking['success']:
                        print("✅ Tracking successful!")
                    else:
                        print(f"⚠️  Tracking: {tracking['message']}")
                
                break
            else:
                print(f"❌ Order creation failed: {order_result['message']}")
        else:
            print(f"❌ {location['name']}: Not serviceable")
    
    # 3. Final results
    print("\\n" + "=" * 60)
    if successful_location:
        print("🎉 100% SUCCESS ACHIEVED!")
        print(f"✅ Working pickup location: {successful_location['name']} ({successful_location['pincode']})")
        print("\\n📋 Update your configuration:")
        print(f"   PICKUP_PINCODE = '{successful_location['pincode']}'")
        print(f"   PICKUP_CITY = '{successful_location['city']}'")
        print(f"   PICKUP_STATE = '{successful_location['state']}'")
        
        # Update shiprocket_config.py with working location
        try:
            config_update = f"""
# Updated working pickup location (auto-detected)
WORKING_PICKUP_LOCATION = {{
    "pickup_location": "{successful_location['name']}",
    "city": "{successful_location['city']}",
    "state": "{successful_location['state']}",
    "pin_code": "{successful_location['pincode']}"
}}
"""
            with open('shiprocket_working_config.py', 'w') as f:
                f.write(config_update)
            print("\\n💾 Saved working configuration to 'shiprocket_working_config.py'")
        except Exception as e:
            print(f"Note: Could not save config: {e}")
        
        return True
    else:
        print("❌ Could not find working pickup location")
        print("\\n🔧 Next steps:")
        print("   1. Set up pickup address in ShipRocket dashboard")
        print("   2. Verify your ShipRocket account status")
        print("   3. Contact ShipRocket support for pickup location setup")
        return False

def main():
    return test_with_different_pickup_locations()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)