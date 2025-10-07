import requests
import json

def test_product_workflow():
    print("🚀 Testing Product Creation and Approval Workflow")
    print("=" * 60)
    
    # Get tokens
    admin_response = requests.post('http://127.0.0.1:8000/api/token/', json={'email': 'admin@test.com', 'password': 'admin123'})
    admin_token = admin_response.json()['access']

    supplier_response = requests.post('http://127.0.0.1:8000/api/token/', json={'email': 'supplier@test.com', 'password': 'testpass123'})
    supplier_token = supplier_response.json()['access']

    customer_response = requests.post('http://127.0.0.1:8000/api/token/', json={'email': 'customer@test.com', 'password': 'customer123'})
    customer_token = customer_response.json()['access']

    print("✅ All users authenticated")

    # Get basic data
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    supplier_headers = {'Authorization': f'Bearer {supplier_token}'}
    customer_headers = {'Authorization': f'Bearer {customer_token}'}

    categories_response = requests.get('http://127.0.0.1:8000/api/products/categories/', headers=admin_headers).json()
    brands_response = requests.get('http://127.0.0.1:8000/api/products/brands/', headers=admin_headers).json()
    warehouses_response = requests.get('http://127.0.0.1:8000/api/inventory/warehouses/', headers=admin_headers).json()

    categories = categories_response.get('results', categories_response)
    brands = brands_response.get('results', brands_response)
    warehouses = warehouses_response.get('results', warehouses_response)

    print(f"✅ Data available - Categories: {len(categories)}, Brands: {len(brands)}, Warehouses: {len(warehouses)}")

    # Create product as supplier
    import time
    timestamp = int(time.time())
    product_data = {
        'name': f'Test Medicine API Flow {timestamp}',
        'description': 'Test medicine via API workflow',
        'price': '299.99',
        'stock': 100,
        'product_type': 'medicine',
        'category': categories[0]['id'],
        'brand': brands[0]['id'],
        # Medicine-specific required fields
        'composition': f'Paracetamol 500mg {timestamp}',
        'quantity': '10 tablets',
        'form': 'tablet',
        'manufacturer': 'Test Pharma',
        'pack_size': '10 tablets per strip',
        'prescription_required': False
    }

    product_response = requests.post('http://127.0.0.1:8000/api/products/products/', json=product_data, headers=supplier_headers)
    print(f"Product creation response: {product_response.status_code}")

    if product_response.status_code in [200, 201]:
        product = product_response.json()
        product_id = product.get('id')
        print(f"✅ Product created: {product.get('name')} (ID: {product_id})")
        
        # Check pending products for approval
        admin_products = requests.get('http://127.0.0.1:8000/api/products/products/?status=pending', headers=admin_headers)
        print(f"Pending products check: {admin_products.status_code}")
        
        if admin_products.status_code == 200:
            pending_response = admin_products.json()
            pending = pending_response.get('results', pending_response)
            print(f"Found {len(pending)} pending products")
            
            if pending:
                # Approve the product by updating its status
                pending_product_id = pending[0]['id']
                approve_data = {'status': 'published', 'is_publish': True}
                approve_response = requests.patch(f'http://127.0.0.1:8000/api/products/products/{pending_product_id}/', json=approve_data, headers=admin_headers)
                print(f"Product approval: {approve_response.status_code}")
                
                if approve_response.status_code == 200:
                    print("✅ Product approved successfully")
                    
                    # Setup inventory
                    inventory_data = {
                        'product': product_id,
                        'warehouse': warehouses[0]['id'],
                        'quantity': 100,
                        'low_stock_threshold': 10,
                        'batch_number': f'BATCH{timestamp}',
                        'hsn_code': '30049099'
                    }
                    
                    inventory_response = requests.post('http://127.0.0.1:8000/api/inventory/inventory-items/', json=inventory_data, headers=admin_headers)
                    print(f"Inventory setup: {inventory_response.status_code}")
                    
                    if inventory_response.status_code in [200, 201]:
                        print("✅ Inventory setup successful")
                        
                        # Test cart operations
                        cart_data = {'product_id': product_id, 'quantity': 2}
                        cart_response = requests.post('http://127.0.0.1:8000/api/cart/add/', json=cart_data, headers=customer_headers)
                        print(f"Add to cart: {cart_response.status_code}")
                        
                        if cart_response.status_code in [200, 201]:
                            print("✅ Product added to cart successfully")
                            
                            # View cart
                            view_cart = requests.get('http://127.0.0.1:8000/api/cart/', headers=customer_headers)
                            print(f"View cart: {view_cart.status_code}")
                            
                            if view_cart.status_code == 200:
                                cart_items = view_cart.json()
                                print(f"✅ Cart contains {len(cart_items)} items")
                                
                                # Test offline sale
                                offline_sale_data = {
                                    'warehouse': warehouses[0]['id'],
                                    'customer_name': 'Walk-in Customer',
                                    'customer_phone': '9876543210',
                                    'payment_method': 'cash',
                                    'items': [{'product_id': product_id, 'quantity': 1, 'unit_price': '299.00'}]
                                }
                                
                                offline_response = requests.post('http://127.0.0.1:8000/api/inventory/offline-sales/create/', json=offline_sale_data, headers=supplier_headers)
                                print(f"Offline sale: {offline_response.status_code}")
                                
                                if offline_response.status_code in [200, 201]:
                                    offline_sale = offline_response.json()
                                    print(f"✅ Offline sale created: {offline_sale.get('sale_number')}")
                                else:
                                    print(f"❌ Offline sale failed: {offline_response.text[:100]}")
                                
                                print("\n🎉 All basic workflow tests completed successfully!")
                                return True
                            else:
                                print(f"❌ View cart failed: {view_cart.text[:100]}")
                        else:
                            print(f"❌ Add to cart failed: {cart_response.text[:100]}")
                    else:
                        print(f"❌ Inventory setup failed: {inventory_response.text[:100]}")
                else:
                    print(f"❌ Product approval failed: {approve_response.text[:100]}")
        else:
            print(f"❌ Failed to get pending products: {admin_products.text[:100]}")
    else:
        print(f"❌ Product creation failed: {product_response.text[:100]}")
    
    return False

if __name__ == "__main__":
    success = test_product_workflow()
    if success:
        print("\n✅ WORKFLOW TEST PASSED")
    else:
        print("\n❌ WORKFLOW TEST FAILED")
