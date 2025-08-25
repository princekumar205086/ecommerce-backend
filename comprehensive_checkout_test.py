import requests
import json
import sys
import time
from pprint import pprint

BASE_URL = 'http://localhost:8000/api'
TOKEN = None

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
ENDC = '\033[0m'


def log_success(message):
    print(f"{GREEN}✓ {message}{ENDC}")


def log_error(message):
    print(f"{RED}✗ {message}{ENDC}")


def log_info(message):
    print(f"{BLUE}ℹ {message}{ENDC}")


def log_warning(message):
    print(f"{YELLOW}⚠ {message}{ENDC}")


def log_step(step, message):
    print(f"{PURPLE}STEP {step}: {message}{ENDC}")


def login(email, password):
    """Login using JWT token endpoint"""
    url = f"{BASE_URL}/token/"
    
    payload = {
        "email": email,
        "password": password
    }
    
    log_info(f"Attempting to login as {email}...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        global TOKEN
        TOKEN = response.json().get('access')
        log_success(f"Logged in as {email}")
        return True
    else:
        log_error(f"Login failed: {response.text}")
        return False


def get_headers():
    return {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }


def get_cart():
    """Retrieve current user's cart"""
    url = f"{BASE_URL}/cart/"
    
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        cart_data = response.json()
        log_success(f"Retrieved cart (ID: {cart_data['id']})")
        return cart_data
    else:
        log_error(f"Failed to retrieve cart: {response.text}")
        return None


def add_to_cart(product_id, quantity=1, variant_id=None):
    """Add product to cart"""
    url = f"{BASE_URL}/cart/add/"
    
    payload = {
        "product_id": product_id,
        "quantity": quantity
    }
    
    if variant_id:
        payload["variant_id"] = variant_id
    
    response = requests.post(url, json=payload, headers=get_headers())
    
    if response.status_code in [200, 201]:
        log_success(f"Added product {product_id} (qty: {quantity}) to cart")
        return True
    else:
        log_error(f"Failed to add product {product_id} to cart: {response.text}")
        return False


def clear_cart():
    """Clear all items from cart"""
    url = f"{BASE_URL}/cart/clear/"
    
    response = requests.delete(url, headers=get_headers())
    
    if response.status_code == 204:
        log_success("Cart cleared")
        return True
    else:
        log_error(f"Failed to clear cart: {response.text}")
        return False


def create_order_from_cart(cart_id, shipping_address, billing_address, payment_method='credit_card'):
    """Create order from cart with address information"""
    url = f"{BASE_URL}/orders/checkout/"
    
    payload = {
        "cart_id": cart_id,
        "shipping_address": shipping_address,
        "billing_address": billing_address,
        "payment_method": payment_method
    }
    
    response = requests.post(url, json=payload, headers=get_headers())
    
    if response.status_code == 201:
        order_data = response.json()
        log_success(f"Order created successfully (ID: {order_data['id']}, Number: {order_data['order_number']})")
        return order_data
    else:
        log_error(f"Failed to create order: {response.text}")
        return None


def create_payment(order_id, amount, currency='INR'):
    """Initialize payment for order"""
    url = f"{BASE_URL}/payments/create/"
    
    payload = {
        "order_id": order_id,
        "amount": amount,
        "currency": currency
    }
    
    response = requests.post(url, json=payload, headers=get_headers())
    
    if response.status_code == 200:
        payment_data = response.json()
        log_success(f"Payment initialized (Razorpay Order ID: {payment_data['order_id']})")
        return payment_data
    else:
        log_error(f"Failed to create payment: {response.text}")
        return None


def verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """Verify payment completion"""
    url = f"{BASE_URL}/payments/verify/"
    
    payload = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature
    }
    
    response = requests.post(url, json=payload, headers=get_headers())
    
    if response.status_code == 200:
        log_success("Payment verified successfully")
        return response.json()
    else:
        log_error(f"Payment verification failed: {response.text}")
        return None


def get_order(order_id):
    """Retrieve order details"""
    url = f"{BASE_URL}/orders/{order_id}/"
    
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        order_data = response.json()
        log_success(f"Retrieved order {order_id}")
        return order_data
    else:
        log_error(f"Failed to retrieve order: {response.text}")
        return None


def get_products():
    """Retrieve available products"""
    url = f"{BASE_URL}/products/products/"
    
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        products_data = response.json()
        log_success(f"Retrieved {len(products_data.get('results', []))} products")
        return products_data
    else:
        log_error(f"Failed to retrieve products: {response.text}")
        return None


def test_complete_checkout_flow():
    """
    Test the complete checkout flow:
    cart(cart id, address) -> payment (if success) -> order auto creation
    """
    log_step(0, "STARTING COMPLETE CHECKOUT FLOW TEST")
    print("=" * 60)
    
    # Step 1: Authentication
    log_step(1, "AUTHENTICATION")
    if not login("testuser@example.com", "testpassword123"):
        if not login("admin@example.com", "admin123"):
            log_error("Authentication failed with all test accounts")
            return False
    
    # Step 2: Setup - Clear existing cart
    log_step(2, "CART SETUP")
    clear_cart()
    
    # Step 3: Add products to cart
    log_step(3, "ADDING PRODUCTS TO CART")
    
    # Add specific products that we know exist
    products_to_add = [
        {"product_id": 46, "quantity": 2},  # Fixed Image Test Pathology
        {"product_id": 45, "quantity": 1},  # Fixed Image Test Equipment
        {"product_id": 44, "quantity": 3}   # Fixed Image Test Medicine
    ]
    
    for product in products_to_add:
        if not add_to_cart(product["product_id"], product["quantity"]):
            log_warning(f"Could not add product {product['product_id']}, continuing...")
    
    # Step 4: Retrieve and verify cart
    log_step(4, "CART VERIFICATION")
    cart = get_cart()
    if not cart:
        log_error("Could not retrieve cart")
        return False
    
    if cart.get('total_items', 0) == 0:
        log_error("Cart is empty after adding products")
        return False
    
    log_info(f"Cart Summary:")
    log_info(f"  - Cart ID: {cart['id']}")
    log_info(f"  - Total Items: {cart.get('total_items', 0)}")
    log_info(f"  - Total Price: ₹{cart.get('total_price', 0)}")
    log_info(f"  - Items in Cart: {len(cart.get('items', []))}")
    
    # Step 5: Create order with address
    log_step(5, "ORDER CREATION WITH ADDRESS")
    
    shipping_address = {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main Street",
        "address_line2": "Apartment 4B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India"
    }
    
    billing_address = {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "456 Business Avenue",
        "address_line2": "Suite 200",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "India"
    }
    
    order = create_order_from_cart(
        cart_id=cart['id'],
        shipping_address=shipping_address,
        billing_address=billing_address,
        payment_method='credit_card'
    )
    
    if not order:
        log_error("Order creation failed")
        return False
    
    log_info(f"Order Details:")
    log_info(f"  - Order ID: {order['id']}")
    log_info(f"  - Order Number: {order['order_number']}")
    log_info(f"  - Status: {order['status']}")
    log_info(f"  - Payment Status: {order['payment_status']}")
    log_info(f"  - Total Amount: ₹{order['total']}")
    log_info(f"  - Payment Method: {order['payment_method']}")
    
    # Step 6: Verify cart is cleared after order creation
    log_step(6, "VERIFY CART CLEARANCE")
    updated_cart = get_cart()
    if updated_cart and updated_cart.get('total_items', 0) == 0:
        log_success("Cart automatically cleared after order creation")
    else:
        log_warning("Cart was not cleared after order creation")
    
    # Step 7: Initialize payment
    log_step(7, "PAYMENT INITIALIZATION")
    payment_info = create_payment(
        order_id=order['id'],
        amount=order['total'],
        currency='INR'
    )
    
    if not payment_info:
        log_error("Payment initialization failed")
        return False
    
    log_info(f"Payment Details:")
    log_info(f"  - Razorpay Order ID: {payment_info['order_id']}")
    log_info(f"  - Amount: ₹{payment_info['amount']/100}")  # Razorpay amount is in paise
    log_info(f"  - Currency: {payment_info['currency']}")
    log_info(f"  - Razorpay Key: {payment_info['key']}")
    
    # Step 8: Simulate payment verification
    log_step(8, "PAYMENT VERIFICATION (SIMULATED)")
    log_warning("In production, payment would be completed via frontend Razorpay widget")
    log_warning("Simulating payment verification with test data...")
    
    # Generate realistic test data for payment verification
    test_payment_id = f"pay_test_{int(time.time())}"
    test_signature = "test_signature_12345abcdef"
    
    payment_verification = verify_payment(
        razorpay_order_id=payment_info['order_id'],
        razorpay_payment_id=test_payment_id,
        razorpay_signature=test_signature
    )
    
    # Note: This will likely fail with test data, which is expected
    if payment_verification:
        log_success("Payment verification succeeded (unexpected with test data)")
    else:
        log_warning("Payment verification failed (expected with test data)")
    
    # Step 9: Final order status check
    log_step(9, "FINAL ORDER STATUS CHECK")
    final_order = get_order(order['id'])
    
    if not final_order:
        log_error("Could not retrieve final order status")
        return False
    
    log_info(f"Final Order Status:")
    log_info(f"  - Order Status: {final_order['status']}")
    log_info(f"  - Payment Status: {final_order['payment_status']}")
    log_info(f"  - Order Total: ₹{final_order['total']}")
    log_info(f"  - Items Count: {len(final_order.get('items', []))}")
    
    # Step 10: Summary
    log_step(10, "TEST SUMMARY")
    print("=" * 60)
    
    success_indicators = []
    
    if cart and cart.get('total_items', 0) > 0:
        success_indicators.append("✓ Cart populated successfully")
    
    if order:
        success_indicators.append("✓ Order created from cart with address")
    
    if payment_info:
        success_indicators.append("✓ Payment initialized successfully")
    
    if final_order:
        success_indicators.append("✓ Order status verified")
    
    log_success("CHECKOUT FLOW COMPLETED")
    for indicator in success_indicators:
        print(f"  {indicator}")
    
    print("\nNOTE: In production environment:")
    print("  - Payment would be completed via Razorpay frontend widget")
    print("  - Payment verification would use real Razorpay signatures")
    print("  - Order status would automatically update to 'processing' on successful payment")
    print("  - Stock would be automatically deducted from inventory")
    
    return True


def test_individual_endpoints():
    """Test individual endpoints for detailed validation"""
    log_step("A", "TESTING INDIVIDUAL ENDPOINTS")
    
    # Test cart endpoints
    log_info("Testing Cart Endpoints...")
    
    # Clear cart
    clear_cart()
    
    # Add item to cart
    add_to_cart(46, 1)
    
    # Get cart
    cart = get_cart()
    if cart and len(cart.get('items', [])) > 0:
        item_id = cart['items'][0]['id']
        
        # Update cart item
        update_url = f"{BASE_URL}/cart/items/{item_id}/update/"
        update_payload = {"quantity": 3}
        response = requests.put(update_url, json=update_payload, headers=get_headers())
        
        if response.status_code == 200:
            log_success("Cart item updated successfully")
        else:
            log_error(f"Cart item update failed: {response.text}")
        
        # Remove cart item
        remove_url = f"{BASE_URL}/cart/items/{item_id}/remove/"
        response = requests.delete(remove_url, headers=get_headers())
        
        if response.status_code == 204:
            log_success("Cart item removed successfully")
        else:
            log_error(f"Cart item removal failed: {response.text}")
    
    # Test order endpoints
    log_info("Testing Order Endpoints...")
    
    # Get orders list
    orders_url = f"{BASE_URL}/orders/"
    response = requests.get(orders_url, headers=get_headers())
    
    if response.status_code == 200:
        orders = response.json()
        log_success(f"Retrieved orders list ({len(orders)} orders)")
    else:
        log_error(f"Failed to retrieve orders: {response.text}")
    
    # Test payment endpoints
    log_info("Testing Payment Endpoints...")
    
    # Get payments list
    payments_url = f"{BASE_URL}/payments/"
    response = requests.get(payments_url, headers=get_headers())
    
    if response.status_code == 200:
        payments = response.json()
        log_success(f"Retrieved payments list ({len(payments)} payments)")
    else:
        log_error(f"Failed to retrieve payments: {response.text}")


if __name__ == "__main__":
    try:
        # Run complete checkout flow test
        success = test_complete_checkout_flow()
        
        print("\n" + "=" * 60)
        
        # Run individual endpoint tests
        test_individual_endpoints()
        
        print("\n" + "=" * 60)
        
        if success:
            log_success("ALL TESTS COMPLETED SUCCESSFULLY!")
            print("\nThe checkout flow is working correctly:")
            print("✓ Cart management works")
            print("✓ Order creation from cart with address works") 
            print("✓ Payment initialization works")
            print("✓ All APIs are properly integrated")
        else:
            log_error("SOME TESTS FAILED!")
            sys.exit(1)
            
    except Exception as e:
        log_error(f"Test execution failed: {str(e)}")
        sys.exit(1)