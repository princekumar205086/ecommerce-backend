import requests
import json
import time
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
    
    response = requests.post(url, json=payload, headers=get_headers())
    
    if response.status_code in [200, 201]:
        log_success(f"Added product {product_id} to cart")
        return True
    else:
        log_error(f"Failed to add to cart: {response.text}")
        return False


def clear_cart():
    url = f"{BASE_URL}/cart/clear/"
    
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
    
    response = requests.post(url, json=payload, headers=get_headers())
    
    if response.status_code == 200:
        log_success("Payment verified successfully")
        return response.json()
    else:
        log_error(f"Failed to verify payment: {response.text}")
        return None


def get_order(order_id):
    url = f"{BASE_URL}/orders/{order_id}/"
    
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        log_success(f"Retrieved order {order_id}")
        return response.json()
    else:
        log_error(f"Failed to retrieve order: {response.text}")
        return None


def get_payments():
    url = f"{BASE_URL}/payments/"
    
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        log_success("Retrieved payments")
        return response.json()
    else:
        log_error(f"Failed to retrieve payments: {response.text}")
        return None


def test_checkout_flow():
    log_info("Starting checkout flow test...")
    
    # Step 1: Login
    if not login("user@example.com", "password123"):
        return False
    
    # Step 2: Clear cart (if any)
    clear_cart()
    
    # Step 3: Add products to cart
    add_to_cart(product_id=1, quantity=2)
    add_to_cart(product_id=2, quantity=1)
    
    # Step 4: Get cart to verify items and total
    cart = get_cart()
    if not cart:
        return False
    
    log_info(f"Cart has {cart['total_items']} items with total price: {cart['total_price']}")
    
    # Step 5: Create order from cart
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
    
    # Step 6: Create payment for the order
    payment_info = create_payment(
        order_id=order['id'],
        amount=order['total']
    )
    
    if not payment_info:
        return False
    
    log_info(f"Payment initialized with Razorpay Order ID: {payment_info['order_id']}")
    
    # Simulate payment success with dummy data
    # In a real app, this would be handled by the frontend after user pays
    log_warning("In a real app, the payment would be completed on the frontend.")
    log_warning("We're simulating a successful payment for testing purposes.")
    
    # Step 7: Verify payment (with dummy data)
    # Note: In a real app, these values would come from Razorpay after payment completion
    dummy_payment_id = "pay_dummy12345"
    dummy_signature = "abcdef123456789"
    
    verify_result = verify_payment(
        razorpay_order_id=payment_info['order_id'],
        razorpay_payment_id=dummy_payment_id,
        razorpay_signature=dummy_signature
    )
    
    # Step 8: Verify final order status
    updated_order = get_order(order['id'])
    if not updated_order:
        return False
    
    # This will likely show 'pending' since we used dummy payment data
    log_info(f"Final order status: {updated_order['status']}")
    log_info(f"Final payment status: {updated_order['payment_status']}")
    
    # In real testing with actual Razorpay credentials, payment would succeed
    # and order status would update to 'processing' and payment status to 'paid'
    
    return True


if __name__ == "__main__":
    if test_checkout_flow():
        log_success("Checkout flow test completed successfully!")
    else:
        log_error("Checkout flow test failed!")
        sys.exit(1)

