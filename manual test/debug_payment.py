#!/usr/bin/env python
"""
Debug payment and cart data
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from payments.models import Payment
from cart.models import Cart
from orders.models import Order
from accounts.models import User
import json

def debug_latest_payment():
    """Debug the latest payment and its cart data"""
    
    # Get latest payment
    payment = Payment.objects.filter(payment_method='cod').order_by('-created_at').first()
    
    if not payment:
        print("❌ No COD payments found")
        return
    
    print(f"🔍 Latest COD Payment Debug:")
    print(f"  Payment ID: {payment.id}")
    print(f"  User: {payment.user.email if payment.user else 'None'}")
    print(f"  Status: {payment.status}")
    print(f"  Amount: {payment.amount}")
    print(f"  Cart Data: {payment.cart_data}")
    print(f"  Order: {payment.order}")
    
    # Check if cart exists
    if payment.cart_data:
        cart_id = payment.cart_data.get('cart_id')
        print(f"  Cart ID from data: {cart_id}")
        
        try:
            cart = Cart.objects.get(id=cart_id, user=payment.user)
            print(f"  ✅ Cart exists: ID {cart.id}")
            print(f"  Cart items: {cart.items.count()}")
            for item in cart.items.all():
                print(f"    - {item.product.name} x{item.quantity}")
        except Cart.DoesNotExist:
            print(f"  ❌ Cart {cart_id} not found for user {payment.user.email}")
        except Exception as e:
            print(f"  ❌ Error accessing cart: {e}")
    
    # Check shipping address
    print(f"  Shipping Address: {payment.shipping_address}")
    print(f"  Billing Address: {payment.billing_address}")

def debug_user_carts():
    """Debug user carts"""
    user = User.objects.get(email='testuser@example.com')
    
    print(f"\n🔍 User Cart Debug:")
    print(f"  User: {user.email}")
    
    carts = Cart.objects.filter(user=user)
    print(f"  Total carts: {carts.count()}")
    
    for cart in carts:
        print(f"  Cart {cart.id}: {cart.items.count()} items")
        for item in cart.items.all():
            print(f"    - {item.product.name} x{item.quantity}")

def debug_orders():
    """Debug orders"""
    user = User.objects.get(email='testuser@example.com')
    
    print(f"\n🔍 User Orders Debug:")
    orders = Order.objects.filter(user=user)
    print(f"  Total orders: {orders.count()}")
    
    for order in orders:
        print(f"  Order {order.id}: {order.order_number} - {order.status}")
        print(f"    Payment status: {order.payment_status}")
        print(f"    Total: {order.total}")
        print(f"    Items: {order.items.count()}")

if __name__ == "__main__":
    debug_latest_payment()
    debug_user_carts()
    debug_orders()