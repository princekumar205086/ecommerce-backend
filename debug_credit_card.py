"""
Debug Credit Card Payment Issue
"""

import requests
import json

BASE_URL = 'http://localhost:8000/api'
TEST_EMAIL = 'user@example.com'
TEST_PASSWORD = 'User@123'

def test_credit_card_debug():
    # Authenticate
    auth_response = requests.post(f"{BASE_URL}/token/", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    token = auth_response.json()['access']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Clear cart and add product
    requests.delete(f"{BASE_URL}/cart/clear/", headers=headers)
    
    products_response = requests.get(f"{BASE_URL}/products/products/?search=Omega", headers=headers)
    products = products_response.json()['results']
    product = products[0]
    
    cart_payload = {"product_id": product['id'], "quantity": 1}
    if product.get('variants'):
        cart_payload["variant_id"] = product['variants'][0]['id']
    
    requests.post(f"{BASE_URL}/cart/add/", json=cart_payload, headers=headers)
    
    # Get cart
    cart_response = requests.get(f"{BASE_URL}/cart/", headers=headers)
    cart_data = cart_response.json()
    
    # Create order with credit card
    shipping_address = {
        "name": "Test User",
        "phone": "9876543210",
        "address_line1": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "postal_code": "123456",
        "country": "India"
    }
    
    order_payload = {
        "cart_id": cart_data['id'],
        "shipping_address": shipping_address,
        "billing_address": shipping_address,
        "payment_method": "credit_card",
        "coupon_code": "MEDIXMALL10",
        "notes": "Debug test"
    }
    
    order_response = requests.post(f"{BASE_URL}/orders/checkout/", json=order_payload, headers=headers)
    print(f"Order Creation Response: {order_response.status_code}")
    print(f"Order Data: {order_response.text}")
    
    if order_response.status_code == 201:
        order_data = order_response.json()
        
        # Try payment initialization
        payment_payload = {
            "order_id": order_data['id'],
            "amount": order_data['total'],
            "currency": "INR"
        }
        
        payment_response = requests.post(f"{BASE_URL}/payments/create/", json=payment_payload, headers=headers)
        print(f"\nPayment Creation Response: {payment_response.status_code}")
        print(f"Payment Data: {payment_response.text}")
    
if __name__ == "__main__":
    test_credit_card_debug()