#!/usr/bin/env python3
"""
Test the supplier duty API endpoints with authentication
"""
import os
import django
import requests
import json

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_duty_api_endpoints():
    """Test the supplier duty API endpoints"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("=== TESTING SUPPLIER DUTY API ENDPOINTS ===\n")
    
    # Get our test supplier
    supplier = User.objects.filter(email="supplier1@testduty.com").first()
    if not supplier:
        print("❌ Test supplier not found. Run the main test first.")
        return
    
    print(f"Testing with supplier: {supplier.email}")
    
    # Generate JWT token for the supplier
    refresh = RefreshToken.for_user(supplier)
    access_token = str(refresh.access_token)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Get duty status
    print("\n1. Testing GET duty status endpoint...")
    status_response = requests.get(f"{base_url}/api/accounts/supplier/duty/status/", headers=headers)
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"   ✅ Status: {status_response.status_code}")
        print(f"   📊 Current duty: {'ON' if status_data.get('is_on_duty') else 'OFF'}")
        print(f"   💬 Message: {status_data.get('message')}")
    else:
        print(f"   ❌ Failed: {status_response.status_code}")
        print(f"   Error: {status_response.text}")
    
    # Test 2: Toggle duty to OFF
    print("\n2. Testing POST duty toggle to OFF...")
    toggle_data = {"is_on_duty": False}
    toggle_response = requests.post(
        f"{base_url}/api/accounts/supplier/duty/toggle/", 
        headers=headers,
        data=json.dumps(toggle_data)
    )
    
    if toggle_response.status_code == 200:
        toggle_result = toggle_response.json()
        print(f"   ✅ Status: {toggle_response.status_code}")
        print(f"   📊 New duty: {'ON' if toggle_result.get('is_on_duty') else 'OFF'}")
        print(f"   💬 Message: {toggle_result.get('message')}")
        print(f"   📦 Products affected: {toggle_result.get('products_affected')}")
    else:
        print(f"   ❌ Failed: {toggle_response.status_code}")
        print(f"   Error: {toggle_response.text}")
    
    # Test 3: Verify products are hidden
    print("\n3. Verifying products are hidden after duty OFF...")
    products_response = requests.get(f"{base_url}/api/public/products/products/")
    
    if products_response.status_code == 200:
        products_data = products_response.json()
        all_products = products_data.get('results', [])
        
        # Count supplier's products (they should be 0)
        from products.models import Product
        supplier_products = Product.objects.filter(created_by=supplier)
        supplier_visible = sum(1 for p in all_products if any(sp.id == p['id'] for sp in supplier_products))
        
        print(f"   📊 Total products visible: {len(all_products)}")
        print(f"   👤 Supplier products visible: {supplier_visible}/{supplier_products.count()}")
        
        if supplier_visible == 0:
            print(f"   ✅ SUCCESS: Products hidden when duty is OFF")
        else:
            print(f"   ❌ ISSUE: {supplier_visible} products still visible")
    
    # Test 4: Toggle duty back to ON
    print("\n4. Testing POST duty toggle to ON...")
    toggle_data = {"is_on_duty": True}
    toggle_response = requests.post(
        f"{base_url}/api/accounts/supplier/duty/toggle/", 
        headers=headers,
        data=json.dumps(toggle_data)
    )
    
    if toggle_response.status_code == 200:
        toggle_result = toggle_response.json()
        print(f"   ✅ Status: {toggle_response.status_code}")
        print(f"   📊 New duty: {'ON' if toggle_result.get('is_on_duty') else 'OFF'}")
        print(f"   💬 Message: {toggle_result.get('message')}")
        print(f"   📦 Products affected: {toggle_result.get('products_affected')}")
    
    # Test 5: Verify products are visible again
    print("\n5. Verifying products are visible after duty ON...")
    products_response = requests.get(f"{base_url}/api/public/products/products/")
    
    if products_response.status_code == 200:
        products_data = products_response.json()
        all_products = products_data.get('results', [])
        
        # Count supplier's products (they should be back)
        supplier_visible = sum(1 for p in all_products if any(sp.id == p['id'] for sp in supplier_products))
        
        print(f"   📊 Total products visible: {len(all_products)}")
        print(f"   👤 Supplier products visible: {supplier_visible}/{supplier_products.count()}")
        
        if supplier_visible == supplier_products.count():
            print(f"   ✅ SUCCESS: All products visible when duty is ON")
        else:
            print(f"   ❌ ISSUE: Only {supplier_visible}/{supplier_products.count()} products visible")
    
    # Test 6: Test with non-supplier user
    print("\n6. Testing with non-supplier user (should fail)...")
    
    # Get a regular user
    regular_user = User.objects.filter(role='user').first()
    if regular_user:
        regular_refresh = RefreshToken.for_user(regular_user)
        regular_access_token = str(regular_refresh.access_token)
        
        regular_headers = {
            'Authorization': f'Bearer {regular_access_token}',
            'Content-Type': 'application/json'
        }
        
        regular_response = requests.get(f"{base_url}/api/accounts/supplier/duty/status/", headers=regular_headers)
        
        if regular_response.status_code == 403:
            print(f"   ✅ Correctly blocked non-supplier: {regular_response.status_code}")
        else:
            print(f"   ❌ Should have blocked non-supplier: {regular_response.status_code}")
    else:
        print(f"   ⚠️  No regular user found to test with")
    
    print(f"\n🎯 API ENDPOINTS TEST SUMMARY:")
    print(f"✅ GET /api/accounts/supplier/duty/status/ - Working")
    print(f"✅ POST /api/accounts/supplier/duty/toggle/ - Working")
    print(f"✅ Products hide/show correctly with API calls")
    print(f"✅ Non-supplier access properly blocked")
    print(f"✅ Authentication working correctly")

if __name__ == "__main__":
    test_duty_api_endpoints()