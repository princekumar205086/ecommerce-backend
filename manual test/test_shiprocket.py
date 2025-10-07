#!/usr/bin/env python
"""
ShipRocket Integration Test
Tests ShipRocket API with production credentials
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

def test_shiprocket_connection():
    """Test ShipRocket API connection"""
    print("🚚 Testing ShipRocket API Connection...")
    print("=" * 50)
    
    # 1. Test authentication
    print("\\n🔐 Testing Authentication...")
    connection_test = shiprocket_api.test_connection()
    
    if connection_test['success']:
        print("✅ ShipRocket authentication successful!")
        print(f"   Message: {connection_test['message']}")
        
        # 2. Test serviceability check
        print("\\n🌍 Testing Serviceability Check...")
        serviceability = shiprocket_api.check_serviceability(
            pickup_pincode='854301',  # Purnia, Bihar (from config)
            delivery_pincode='110001',  # Delhi
            weight=1.0,
            cod=False
        )
        
        if serviceability['success']:
            print(f"✅ Serviceability check successful!")
            print(f"   Serviceable: {serviceability['serviceable']}")
            print(f"   Available couriers: {len(serviceability.get('couriers', []))}")
            
            if serviceability['couriers']:
                print("   Courier options:")
                for courier in serviceability['couriers'][:3]:  # Show first 3
                    print(f"     - {courier.get('courier_name', 'Unknown')}: ₹{courier.get('freight_charge', 0)}")
        else:
            print(f"❌ Serviceability check failed: {serviceability['message']}")
        
        # 3. Test shipping rates
        print("\\n💰 Testing Shipping Rates...")
        rates = shiprocket_api.get_shipping_rates(
            pickup_pincode='854301',
            delivery_pincode='110001',
            weight=1.0,
            dimensions={'length': 10, 'breadth': 10, 'height': 5}
        )
        
        if rates['success']:
            print(f"✅ Shipping rates retrieved successfully!")
            print(f"   Available rates: {len(rates.get('rates', []))}")
            
            if rates.get('cheapest'):
                cheapest = rates['cheapest']
                print(f"   Cheapest option: {cheapest.get('courier_name', 'Unknown')} - ₹{cheapest.get('freight_charge', 0)}")
        else:
            print(f"❌ Shipping rates failed: {rates['message']}")
        
        # 4. Test order creation (sample data)
        print("\\n📦 Testing Order Creation (Sample)...")
        sample_order = {
            'order_id': f'TEST{int(__import__("time").time())}',
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
            print("✅ Order creation successful!")
            print(f"   Order ID: {order_result.get('order_id')}")
            print(f"   Shipment ID: {order_result.get('shipment_id')}")
            
            # Test tracking if we got a shipment ID
            if order_result.get('shipment_id'):
                print("\\n🔍 Testing Order Tracking...")
                tracking = shiprocket_api.track_shipment(order_result['shipment_id'])
                
                if tracking['success']:
                    print("✅ Order tracking successful!")
                else:
                    print(f"⚠️  Order tracking info: {tracking['message']}")
            
        else:
            print(f"❌ Order creation failed: {order_result['message']}")
            if 'errors' in order_result:
                print(f"   Errors: {order_result['errors']}")
        
        print("\\n" + "=" * 50)
        print("🎉 ShipRocket integration test completed!")
        return True
        
    else:
        print(f"❌ ShipRocket authentication failed: {connection_test['message']}")
        print("\\n🔧 Troubleshooting tips:")
        print("   1. Check SHIPROCKET_EMAIL and SHIPROCKET_PASSWORD in shiprocket_config.py")
        print("   2. Ensure you have a valid ShipRocket account")
        print("   3. Check if your account has API access enabled")
        print("   4. Verify your internet connection")
        return False

def main():
    test_shiprocket_connection()

if __name__ == "__main__":
    main()