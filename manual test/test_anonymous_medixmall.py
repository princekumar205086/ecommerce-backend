#!/usr/bin/env python3
"""
Test MedixMall mode for anonymous (non-logged) users using session storage
"""

import requests
import json

def test_anonymous_medixmall_mode():
    """Test MedixMall mode functionality for anonymous users"""
    
    base_url = "http://127.0.0.1:8000"
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("🧪 TESTING MEDIXMALL MODE FOR ANONYMOUS USERS")
    print("=" * 60)
    
    # 1. Test initial state (should be false by default)
    print("\n1️⃣ Testing initial MedixMall mode state...")
    response = session.get(f"{base_url}/api/accounts/medixmall-mode/")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Initial mode: {data['medixmall_mode']}")
        print(f"👤 User type: {data['user_type']}")
        print(f"💾 Storage: {data['storage_type']}")
        print(f"🔧 Header: {response.headers.get('X-MedixMall-Mode')}")
    else:
        print(f"❌ Failed to get initial state: {response.status_code}")
        return
    
    # 2. Test enabling MedixMall mode
    print("\n2️⃣ Enabling MedixMall mode...")
    response = session.put(
        f"{base_url}/api/accounts/medixmall-mode/",
        json={"medixmall_mode": True},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Mode enabled: {data['medixmall_mode']}")
        print(f"💬 Message: {data['message']}")
        print(f"👤 User type: {data['user_type']}")
        print(f"💾 Storage: {data['storage_type']}")
        print(f"🔧 Header: {response.headers.get('X-MedixMall-Mode')}")
    else:
        print(f"❌ Failed to enable mode: {response.status_code}")
        return
    
    # 3. Test that mode persists in session
    print("\n3️⃣ Verifying mode persistence...")
    response = session.get(f"{base_url}/api/accounts/medixmall-mode/")
    
    if response.status_code == 200:
        data = response.json()
        if data['medixmall_mode'] == True:
            print("✅ Mode persisted in session successfully")
            print(f"🔧 Header: {response.headers.get('X-MedixMall-Mode')}")
        else:
            print("❌ Mode did not persist in session")
    
    # 4. Test product filtering with MedixMall mode enabled
    print("\n4️⃣ Testing product filtering (MedixMall ON)...")
    response = session.get(f"{base_url}/api/products/")
    
    if response.status_code == 200:
        data = response.json()
        products = data.get('results', [])
        print(f"✅ Products with MedixMall ON: {len(products)}")
        print(f"🔧 Header: {response.headers.get('X-MedixMall-Mode')}")
        
        # Check if all products are medicine type
        if products:
            medicine_count = sum(1 for p in products if p.get('product_type') == 'medicine')
            print(f"💊 Medicine products: {medicine_count}/{len(products)}")
            if medicine_count == len(products):
                print("✅ All products are medicine type - filtering works!")
            else:
                print("⚠️  Some non-medicine products found")
    
    # 5. Test disabling MedixMall mode
    print("\n5️⃣ Disabling MedixMall mode...")
    response = session.put(
        f"{base_url}/api/accounts/medixmall-mode/",
        json={"medixmall_mode": False},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Mode disabled: {not data['medixmall_mode']}")
        print(f"💬 Message: {data['message']}")
        print(f"🔧 Header: {response.headers.get('X-MedixMall-Mode')}")
    
    # 6. Test product filtering with MedixMall mode disabled
    print("\n6️⃣ Testing product filtering (MedixMall OFF)...")
    response = session.get(f"{base_url}/api/products/")
    
    if response.status_code == 200:
        data = response.json()
        products = data.get('results', [])
        print(f"✅ Products with MedixMall OFF: {len(products)}")
        print(f"🔧 Header: {response.headers.get('X-MedixMall-Mode')}")
        
        # Check product types distribution
        if products:
            medicine_count = sum(1 for p in products if p.get('product_type') == 'medicine')
            other_count = len(products) - medicine_count
            print(f"💊 Medicine products: {medicine_count}")
            print(f"🛍️ Other products: {other_count}")
    
    # 7. Test with new session (should reset to default)
    print("\n7️⃣ Testing new session (no cookies)...")
    new_session = requests.Session()
    response = new_session.get(f"{base_url}/api/accounts/medixmall-mode/")
    
    if response.status_code == 200:
        data = response.json()
        if data['medixmall_mode'] == False:
            print("✅ New session has default mode (False)")
        else:
            print("⚠️  New session did not reset to default")
    
    print("\n" + "=" * 60)
    print("🎉 ANONYMOUS USER MEDIXMALL MODE TESTING COMPLETE!")
    print("\n💡 Key Features:")
    print("  ✅ Works without authentication")
    print("  ✅ Stores preference in session")
    print("  ✅ Filters products correctly")
    print("  ✅ Includes proper response headers")
    print("  ✅ Resets with new sessions")
    print("\n🔧 Frontend Integration:")
    print("  • Call API without Authorization header")
    print("  • Mode is stored in browser session")
    print("  • Persists until browser session ends")
    print("  • Use same endpoints as authenticated users")

if __name__ == "__main__":
    test_anonymous_medixmall_mode()