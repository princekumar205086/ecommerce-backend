import requests
import json

# Test basic authentication and API endpoints
BASE_URL = "http://127.0.0.1:8000"

def test_basic_authentication():
    print("Testing basic authentication...")
    
    # Test admin login
    response = requests.post(f"{BASE_URL}/api/token/", {
        "email": "admin@test.com",
        "password": "admin123"
    })
    
    if response.status_code == 200:
        admin_token = response.json()['access']
        print("✅ Admin authentication successful")
        
        # Test supplier login
        supplier_response = requests.post(f"{BASE_URL}/api/token/", {
            "email": "supplier@test.com",
            "password": "testpass123"
        })
        
        if supplier_response.status_code == 200:
            supplier_token = supplier_response.json()['access']
            print("✅ Supplier authentication successful")
            
            # Test customer login
            customer_response = requests.post(f"{BASE_URL}/api/token/", {
                "email": "customer@test.com",
                "password": "customer123"
            })
            
            if customer_response.status_code == 200:
                customer_token = customer_response.json()['access']
                print("✅ Customer authentication successful")
                
                return admin_token, supplier_token, customer_token
            else:
                print("❌ Customer authentication failed:", customer_response.json())
        else:
            print("❌ Supplier authentication failed:", supplier_response.json())
    else:
        print("❌ Admin authentication failed:", response.json())
    
    return None, None, None

def test_product_creation(supplier_token):
    print("\nTesting product creation by supplier...")
    
    headers = {"Authorization": f"Bearer {supplier_token}"}
    
    # First get category and brand
    categories_response = requests.get(f"{BASE_URL}/api/products/categories/", headers=headers)
    brands_response = requests.get(f"{BASE_URL}/api/products/brands/", headers=headers)
    
    if categories_response.status_code == 200 and brands_response.status_code == 200:
        categories = categories_response.json()
        brands = brands_response.json()
        
        if categories and brands:
            category_id = categories[0]['id'] if categories else None
            brand_id = brands[0]['id'] if brands else None
            
            product_data = {
                "name": "Test Medicine API",
                "description": "Test medicine via API",
                "price": "199.99",
                "stock": 50,
                "product_type": "medicine",
                "category": category_id,
                "brand": brand_id
            }
            
            response = requests.post(f"{BASE_URL}/api/products/products/", 
                                   json=product_data, headers=headers)
            
            if response.status_code in [200, 201]:
                product = response.json()
                print("✅ Product created successfully:", product['name'])
                return product['id']
            else:
                print("❌ Product creation failed:", response.json())
        else:
            print("❌ No categories or brands found")
    else:
        print("❌ Failed to get categories or brands")
    
    return None

def test_inventory_setup(supplier_token, product_id):
    print("\nTesting inventory setup...")
    
    headers = {"Authorization": f"Bearer {supplier_token}"}
    
    # Get warehouses
    warehouses_response = requests.get(f"{BASE_URL}/api/inventory/warehouses/", headers=headers)
    
    if warehouses_response.status_code == 200:
        warehouses = warehouses_response.json()
        
        if warehouses:
            warehouse_id = warehouses[0]['id']
            
            inventory_data = {
                "product": product_id,
                "warehouse": warehouse_id,
                "quantity": 50,
                "low_stock_threshold": 5
            }
            
            response = requests.post(f"{BASE_URL}/api/inventory/inventory-items/", 
                                   json=inventory_data, headers=headers)
            
            if response.status_code in [200, 201]:
                print("✅ Inventory setup successful")
                return True
            else:
                print("❌ Inventory setup failed:", response.json())
        else:
            print("❌ No warehouses found")
    else:
        print("❌ Failed to get warehouses")
    
    return False

def test_add_to_cart(customer_token, product_id):
    print("\nTesting add to cart...")
    
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    cart_data = {
        "product_id": product_id,
        "quantity": 2
    }
    
    response = requests.post(f"{BASE_URL}/api/cart/add/", 
                           json=cart_data, headers=headers)
    
    if response.status_code in [200, 201]:
        print("✅ Product added to cart successfully")
        return True
    else:
        print("❌ Add to cart failed:", response.json())
    
    return False

def test_offline_sale(supplier_token, product_id):
    print("\nTesting offline sale creation...")
    
    headers = {"Authorization": f"Bearer {supplier_token}"}
    
    # Get warehouses
    warehouses_response = requests.get(f"{BASE_URL}/api/inventory/warehouses/", headers=headers)
    
    if warehouses_response.status_code == 200:
        warehouses = warehouses_response.json()
        
        if warehouses:
            warehouse_id = warehouses[0]['id']
            
            offline_sale_data = {
                "warehouse": warehouse_id,
                "customer_name": "Walk-in Customer",
                "customer_phone": "9876543210",
                "payment_method": "cash",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 1,
                        "unit_price": 199.99
                    }
                ]
            }
            
            response = requests.post(f"{BASE_URL}/api/inventory/offline-sales/create/", 
                                   json=offline_sale_data, headers=headers)
            
            if response.status_code in [200, 201]:
                sale = response.json()
                print("✅ Offline sale created successfully:", sale.get('sale_number'))
                return True
            else:
                print("❌ Offline sale creation failed:", response.json())
        else:
            print("❌ No warehouses found")
    else:
        print("❌ Failed to get warehouses")
    
    return False

def main():
    print("🚀 Starting E-commerce API Test")
    print("=" * 50)
    
    # Test authentication
    admin_token, supplier_token, customer_token = test_basic_authentication()
    
    if not all([admin_token, supplier_token, customer_token]):
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Test product creation
    product_id = test_product_creation(supplier_token)
    
    if not product_id:
        print("❌ Product creation failed. Cannot proceed with tests.")
        return
    
    # Test inventory setup
    inventory_success = test_inventory_setup(supplier_token, product_id)
    
    # Test add to cart
    cart_success = test_add_to_cart(customer_token, product_id)
    
    # Test offline sale
    offline_sale_success = test_offline_sale(supplier_token, product_id)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    tests = [
        ("Authentication", True),
        ("Product Creation", bool(product_id)),
        ("Inventory Setup", inventory_success),
        ("Add to Cart", cart_success),
        ("Offline Sale", offline_sale_success)
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed!")
    else:
        print("⚠️ Some tests failed. Check implementation.")

if __name__ == "__main__":
    main()
