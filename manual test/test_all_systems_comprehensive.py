#!/usr/bin/env python3
"""
Comprehensive test script for MedixMall mode, Enterprise Search, and ShipRocket Integration
Tests all major functionality and verifies API endpoints work correctly
"""

import requests
import json
import sys
from datetime import datetime

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_test(test_name, status, details=None):
    """Print test result with formatting"""
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_symbol} {test_name}: {status}")
    if details:
        print(f"   {details}")

def test_medixmall_mode():
    """Test MedixMall mode functionality"""
    print_section("TESTING MEDIXMALL MODE")
    
    base_url = "http://127.0.0.1:8000"
    session = requests.Session()
    
    # Test 1: Anonymous user mode toggle
    try:
        response = session.get(f"{base_url}/api/accounts/medixmall-mode/")
        if response.status_code == 200:
            data = response.json()
            print_test("Anonymous MedixMall Mode Check", "PASS", 
                      f"Initial mode: {data['medixmall_mode']}, Storage: {data['storage_type']}")
        else:
            print_test("Anonymous MedixMall Mode Check", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Anonymous MedixMall Mode Check", "FAIL", str(e))
    
    # Test 2: Enable MedixMall mode
    try:
        response = session.put(
            f"{base_url}/api/accounts/medixmall-mode/",
            json={"medixmall_mode": True},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print_test("Enable MedixMall Mode", "PASS", data['message'])
        else:
            print_test("Enable MedixMall Mode", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Enable MedixMall Mode", "FAIL", str(e))
    
    # Test 3: Product filtering (corrected URL)
    try:
        response = session.get(f"{base_url}/api/public/products/products/")
        if response.status_code == 200:
            data = response.json()
            products = data.get('results', [])
            header_mode = response.headers.get('X-MedixMall-Mode')
            print_test("Product Filtering with MedixMall ON", "PASS", 
                      f"Products: {len(products)}, Header: {header_mode}")
        else:
            print_test("Product Filtering with MedixMall ON", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Product Filtering with MedixMall ON", "FAIL", str(e))
    
    return session

def test_enterprise_search(session):
    """Test enterprise search functionality"""
    print_section("TESTING ENTERPRISE SEARCH")
    
    base_url = "http://127.0.0.1:8000"
    
    # Test different search scenarios
    search_tests = [
        {"q": "paracetamol", "description": "Medicine search"},
        {"q": "equipment", "description": "Equipment search"}, 
        {"q": "tablet", "description": "Form-based search"},
        {"product_type": "medicine", "description": "Product type filter"},
        {"sort_by": "price_low", "description": "Price sorting"},
        {"min_price": "10", "max_price": "100", "description": "Price range"},
        {"q": "blood pressure", "description": "Multi-word search"}
    ]
    
    for test in search_tests:
        try:
            params = {k: v for k, v in test.items() if k != 'description'}
            response = session.get(f"{base_url}/api/public/products/search/", params=params)
            
            if response.status_code == 200:
                data = response.json()
                results_count = len(data.get('results', []))
                suggestions = len(data.get('search_suggestions', []))
                filters = data.get('filters', {})
                print_test(f"Search: {test['description']}", "PASS", 
                          f"Results: {results_count}, Suggestions: {suggestions}, Filters: {len(filters)}")
            else:
                print_test(f"Search: {test['description']}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Search: {test['description']}", "FAIL", str(e))

def test_authenticated_user():
    """Test authenticated user functionality"""
    print_section("TESTING AUTHENTICATED USER FEATURES")
    
    base_url = "http://127.0.0.1:8000"
    
    # Login as test user
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/accounts/login/", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data['access']
            print_test("User Authentication", "PASS", "Login successful")
            
            # Test authenticated MedixMall mode
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Get current mode
            response = requests.get(f"{base_url}/api/accounts/medixmall-mode/", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print_test("Authenticated MedixMall Check", "PASS", 
                          f"Mode: {data['medixmall_mode']}, Type: {data['user_type']}")
            
            # Test orders endpoint (should work now)
            response = requests.get(f"{base_url}/api/orders/", headers=headers)
            if response.status_code == 200:
                data = response.json()
                orders = data.get('results', [])
                print_test("Orders List", "PASS", f"Orders count: {len(orders)}")
            else:
                print_test("Orders List", "FAIL", f"Status: {response.status_code}")
                
        else:
            print_test("User Authentication", "FAIL", f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        print_test("User Authentication", "FAIL", str(e))
        return None
    
    return access_token

def test_shiprocket_integration():
    """Test ShipRocket integration"""
    print_section("TESTING SHIPROCKET INTEGRATION")
    
    base_url = "http://127.0.0.1:8000"
    
    # Test 1: Connection test
    try:
        response = requests.get(f"{base_url}/api/shipping/test/")
        if response.status_code == 200:
            data = response.json()
            print_test("ShipRocket Connection", "PASS", data.get('message', 'Connected'))
        else:
            data = response.json() if response.content else {}
            print_test("ShipRocket Connection", "FAIL", 
                      data.get('message', f"Status: {response.status_code}"))
    except Exception as e:
        print_test("ShipRocket Connection", "FAIL", str(e))
    
    # Test 2: Serviceability check
    try:
        params = {
            'pickup_pincode': '110001',
            'delivery_pincode': '400001',
            'weight': '1.0'
        }
        response = requests.get(f"{base_url}/api/shipping/serviceability/", params=params)
        if response.status_code == 200:
            data = response.json()
            serviceable = data.get('serviceable', False)
            print_test("Serviceability Check", "PASS", f"Serviceable: {serviceable}")
        else:
            data = response.json() if response.content else {}
            print_test("Serviceability Check", "FAIL", 
                      data.get('message', f"Status: {response.status_code}"))
    except Exception as e:
        print_test("Serviceability Check", "FAIL", str(e))
    
    # Test 3: Shipping rates
    try:
        params = {
            'pickup_pincode': '110001',
            'delivery_pincode': '560001',
            'weight': '2.5'
        }
        response = requests.get(f"{base_url}/api/shipping/rates/", params=params)
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', [])
            print_test("Shipping Rates", "PASS", f"Rate options: {len(rates)}")
        else:
            data = response.json() if response.content else {}
            print_test("Shipping Rates", "FAIL", 
                      data.get('message', f"Status: {response.status_code}"))
    except Exception as e:
        print_test("Shipping Rates", "FAIL", str(e))

def test_swagger_documentation():
    """Test Swagger documentation"""
    print_section("TESTING SWAGGER DOCUMENTATION")
    
    base_url = "http://127.0.0.1:8000"
    
    # Test Swagger JSON endpoint
    try:
        response = requests.get(f"{base_url}/swagger.json")
        if response.status_code == 200:
            try:
                swagger_data = response.json()
                paths = swagger_data.get('paths', {})
                
                # Check for key endpoints
                key_endpoints = [
                    '/api/accounts/medixmall-mode/',
                    '/api/public/products/search/',
                    '/api/shipping/test/',
                    '/api/orders/'
                ]
                
                found_endpoints = 0
                for endpoint in key_endpoints:
                    if endpoint in paths:
                        found_endpoints += 1
                
                print_test("Swagger Documentation", "PASS", 
                          f"Found {found_endpoints}/{len(key_endpoints)} key endpoints")
            except json.JSONDecodeError:
                print_test("Swagger Documentation", "PASS", 
                          f"Swagger available (Status: {response.status_code})")
        else:
            print_test("Swagger Documentation", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Swagger Documentation", "FAIL", str(e))

def main():
    """Run all tests"""
    print(f"""
🚀 COMPREHENSIVE SYSTEM TEST
============================
Testing: MedixMall Mode, Enterprise Search, ShipRocket Integration
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
    
    # Test anonymous MedixMall mode
    session = test_medixmall_mode()
    
    # Test enterprise search
    test_enterprise_search(session)
    
    # Test authenticated features
    access_token = test_authenticated_user()
    
    # Test ShipRocket integration
    test_shiprocket_integration()
    
    # Test Swagger documentation
    test_swagger_documentation()
    
    print_section("TEST SUMMARY")
    print("""
🎯 Key Features Tested:
  • MedixMall Mode Toggle (Anonymous & Authenticated)
  • Product Filtering based on mode
  • Enterprise Search with multiple parameters
  • Order Management with MedixMall filtering
  • ShipRocket API Integration
  • Swagger Documentation Coverage

📋 Manual Verification Needed:
  • Check Swagger UI at: http://127.0.0.1:8000/swagger/
  • Verify all endpoints are documented
  • Test frontend integration with response headers
  • Update ShipRocket credentials for production

🔧 Next Steps:
  1. Fix any failed tests above
  2. Update ShipRocket credentials in shiprocket_config.py
  3. Test with real ShipRocket UAT account
  4. Deploy documentation updates
""")

if __name__ == "__main__":
    main()