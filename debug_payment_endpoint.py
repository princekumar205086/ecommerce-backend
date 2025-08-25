#!/usr/bin/env python
import os
import django
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

import requests
import json
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from cart.models import Cart, CartItem
from products.models import Product, ProductVariant

# Test URL
BASE_URL = 'http://127.0.0.1:8000'

def test_payment_endpoint():
    try:
        # Get or create a test user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'full_name': 'Test User',
                'contact': '1234567890'
            }
        )
        
        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Create a test cart with items
        cart, created = Cart.objects.get_or_create(user=user)
        cart.items.all().delete()  # Clear existing items
        
        # Add a product to cart
        product = Product.objects.first()
        if not product:
            print("❌ No products found. Please seed products first.")
            return
            
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        
        print(f"✅ Created cart {cart.id} with product {product.name}")
        
        # Test payload
        payload = {
            "cart_id": cart.id,
            "shipping_address": {
                "full_name": "Test User",
                "address_line_1": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "12345",
                "country": "India"
            },
            "billing_address": {
                "full_name": "Test User",
                "address_line_1": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "12345",
                "country": "India"
            },
            "payment_method": "razorpay",
            "currency": "INR"
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"🔄 Testing endpoint: {BASE_URL}/api/payments/create-from-cart/")
        print(f"🔑 Using token: {access_token[:20]}...")
        print(f"📦 Cart ID: {cart.id}")
        
        # Make the request
        response = requests.post(
            f'{BASE_URL}/api/payments/create-from-cart/',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Payment created successfully!")
            print(f"📋 Response: {response.json()}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"🔍 Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print("🔍 Raw Error Text:")
                print(response.text)
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Is the Django server running?")
        print("💡 Run: python manage.py runserver")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_payment_endpoint()