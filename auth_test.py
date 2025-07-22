import requests
import json

# Test authentication endpoint directly
BASE_URL = "http://127.0.0.1:8000"

def test_auth():
    print("Testing authentication endpoint...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/token/", 
            json={
                "email": "admin@test.com",
                "password": "admin123"
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Authentication successful!")
            print(f"Access Token: {token_data.get('access', 'N/A')[:50]}...")
            return token_data.get('access')
        else:
            print("❌ Authentication failed")
            return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_simple_endpoints(token):
    if not token:
        print("❌ No token available")
        return
    
    print("\nTesting authenticated endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test categories
    try:
        response = requests.get(f"{BASE_URL}/api/products/categories/", headers=headers)
        print(f"Categories endpoint: {response.status_code}")
        if response.status_code == 200:
            categories = response.json()
            print(f"Found {len(categories)} categories")
    except Exception as e:
        print(f"Categories error: {e}")
    
    # Test brands
    try:
        response = requests.get(f"{BASE_URL}/api/products/brands/", headers=headers)
        print(f"Brands endpoint: {response.status_code}")
        if response.status_code == 200:
            brands = response.json()
            print(f"Found {len(brands)} brands")
    except Exception as e:
        print(f"Brands error: {e}")
    
    # Test warehouses
    try:
        response = requests.get(f"{BASE_URL}/api/inventory/warehouses/", headers=headers)
        print(f"Warehouses endpoint: {response.status_code}")
        if response.status_code == 200:
            warehouses = response.json()
            print(f"Found {len(warehouses)} warehouses")
    except Exception as e:
        print(f"Warehouses error: {e}")

if __name__ == "__main__":
    print("🚀 Simple Authentication Test")
    print("=" * 40)
    
    token = test_auth()
    test_simple_endpoints(token)
