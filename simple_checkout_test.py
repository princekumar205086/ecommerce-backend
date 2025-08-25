import requests
import json
import sys
from pprint import pprint

BASE_URL = 'http://localhost:8000/api'
TOKEN = None

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'


def log_success(message):
    print(f"{GREEN}✓ {message}{ENDC}")


def log_error(message):
    print(f"{RED}✗ {message}{ENDC}")


def log_info(message):
    print(f"{BLUE}ℹ {message}{ENDC}")


def log_warning(message):
    print(f"{YELLOW}⚠ {message}{ENDC}")


def login(email, password):
    url = f"{BASE_URL}/accounts/login/"
    
    payload = {
        "email": email,
        "password": password
    }
    
    log_info(f"Attempting to login as {email}...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        global TOKEN
        TOKEN = response.json().get('token')
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
    url = f"{BASE_URL}/cart/"
    
    log_info("Retrieving cart...")
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        log_success("Retrieved cart")
        return response.json()
    else:
        log_error(f"Failed to retrieve cart: {response.text}")
        return None


def add_to_cart(product_id, quantity=1, variant_id=None):
    url = f"{BASE_URL}/cart/add/"
    
    payload = {
        "product_id": product_id,
        "quantity": quantity
    }
    
    if variant_id:
        payload["variant_id"] = variant_id
    
    log_info(f"Adding product {product_id} to cart...")
    response = requests.post(url, json=payload, headers=get_headers())
    
    if response.status_code in [200, 201]:
        log_success(f"Added product {product_id} to cart")
        return True
    else:
        log_error(f"Failed to add to cart: {response.text}")
        return False


def clear_cart():
    url = f"{BASE_URL}/cart/clear/"
    
    log_info("Clearing cart...")
    response = requests.delete(url, headers=get_headers())
    
    if response.status_code == 204:
        log_success("Cart cleared")
        return True
    else:
        log_error(f"Failed to clear cart: {response.text}")
        return False


def create_order(cart_id, shipping_address, billing_address, payment_method='credit_card'):
    url = f"{BASE_URL}/orders/checkout/"
    
    payload = {
        "cart_id": cart_id,
        "shipping_address": shipping_address,
        "billing_address": billing_address,
        "payment_method": payment_method
    }
    
    log_info("Creating order from cart...")
    response = requests.post(url, json=payload, headers=get_headers())
    
    if response.status_code == 201:
        log_success("Order created successfully")
        return response.json()
    else:
        log_error(f"Failed to create order: {response.text}")
        return None


def create_payment(order_id, amount, currency='INR'):
    url = f"{BASE_URL}/payments/create/"
    
    payload = {
        "order_id": order_id,
        "amount": amount,
        "currency": currency
    }
    
    log_info(f"Creating payment for order {order_id}...")
    response = requests.post(url, json=payload, headers=get_headers())
    
    if response.status_code == 200:
        log_success("Payment created successfully")
        return response.json()
    else:
        log_error(f"Failed to create payment: {response.text}")
        return None


def verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    url = f"{BASE_URL}/payments/verify/"
    
    payload = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature
    }
    
    log_info("Verifying payment...")
    response = requests.post(url, json=payload, headers=get_headers())
    
    if response.status_code == 200:
        log_success("Payment verified successfully")
        return response.json()
    else:
        log_error(f"Failed to verify payment: {response.text}")
        return None


def get_order(order_id):
    url = f"{BASE_URL}/orders/{order_id}/"
    
    log_info(f"Retrieving order {order_id}...")
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        log_success(f"Retrieved order {order_id}")
        return response.json()
    else:
        log_error(f"Failed to retrieve order: {response.text}")
        return None


def get_products():
    url = f"{BASE_URL}/products/"
    
    log_info("Retrieving products...")
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        log_success("Retrieved products")
        return response.json()
    else:
        log_error(f"Failed to retrieve products: {response.text}")
        return None


def test_checkout_flow():
    log_info("=== TESTING COMPLETE CHECKOUT FLOW ===")
    
    # Step 1: Login - try admin first, then testuser if that fails
    if not login("admin@example.com", "admin123"):
        if not login("testuser@example.com", "testpassword123"):
            log_error("Could not log in with any test account")
            return False
    
    # Step 2: Clear cart (if any)
    clear_cart()
    
    # Step 3: Get products to find valid products for cart
    products = get_products()
    if not products or 'results' not in products or not products['results']:
        log_error("No products available for testing")
        return False
    
    # Step 4: Add products to cart
    product1 = products['results'][0]
    product_id1 = product1['id']
    add_to_cart(product_id=product_id1, quantity=2)
    
    if len(products['results']) > 1:
        product2 = products['results'][1]
        product_id2 = product2['id']
        add_to_cart(product_id=product_id2, quantity=1)
    
    # Step 5: Get cart to verify items and total
    cart = get_cart()
    if not cart:
        return False
    
    log_info(f"Cart has {cart.get('total_items', 0)} items with total price: {cart.get('total_price', 0)}")
    
    # Step 6: Create order from cart
    shipping_address = {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main St",
        "address_line2": "Apt 4B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India"
    }
    
    # Use same address for billing in this test
    order = create_order(
        cart_id=cart['id'],
        shipping_address=shipping_address,
        billing_address=shipping_address
    )
    
    if not order:
        return False
    
    log_info(f"Order #{order['order_number']} created with total: {order['total']}")
    
    # Step 7: Create payment for the order
    payment_info = create_payment(
        order_id=order['id'],
        amount=order['total']
    )
    
    if not payment_info:
        return False
    
    log_info(f"Payment initialized with Razorpay Order ID: {payment_info['order_id']}")
    
    # Step 8: Verify payment (with dummy data)
    log_warning("In a real app, the payment would be completed on the frontend.")
    log_warning("We're simulating a successful payment for testing purposes.")
    
    dummy_payment_id = "pay_dummy12345"
    dummy_signature = "abcdef123456789"
    
    verify_result = verify_payment(
        razorpay_order_id=payment_info['order_id'],
        razorpay_payment_id=dummy_payment_id,
        razorpay_signature=dummy_signature
    )
    
    # Step 9: Verify final order status
    updated_order = get_order(order['id'])
    if not updated_order:
        return False
    
    log_info(f"Final order status: {updated_order['status']}")
    log_info(f"Final payment status: {updated_order['payment_status']}")
    
    log_success("=== CHECKOUT FLOW TEST COMPLETED ===")
    return True


if __name__ == "__main__":
    if test_checkout_flow():
        log_success("Checkout flow test completed successfully!")
    else:
        log_error("Checkout flow test failed!")
        sys.exit(1)