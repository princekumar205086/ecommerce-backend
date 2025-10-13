#!/usr/bin/env python
"""
CART CLEARING TEST FOR PATHLOG WALLET
=====================================
This test specifically validates that the cart is properly cleared after Pathlog Wallet checkout.
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem
from products.models import Product, ProductVariant
from payments.models import Payment
from orders.models import Order

User = get_user_model()

def test_cart_clearing():
    print("CART CLEARING TEST FOR PATHLOG WALLET")
    print("=" * 50)
    
    # Get test user
    user = User.objects.get(email='user@example.com')
    print(f"✓ Using test user: {user.email}")
    
    # Set up fresh cart
    cart, created = Cart.objects.get_or_create(user=user)
    cart.clear()  # Clear any existing items
    
    # Add a product to cart
    product = Product.objects.filter(is_publish=True, stock__gt=0).first()
    variant = ProductVariant.objects.filter(product=product, stock__gt=0).first()
    
    cart_item = CartItem.objects.create(
        cart=cart,
        product=product,
        variant=variant,
        quantity=1
    )
    
    print(f"✓ Added {cart_item.quantity}x {product.name} to cart")
    print(f"✓ Cart has {cart.items.count()} items before checkout")
    print(f"✓ Cart total: ₹{cart.total_price}")
    
    # Create Pathlog payment
    payment = Payment.objects.create(
        user=user,
        amount=cart.total_price,
        currency='INR',
        payment_method='pathlog_wallet',
        status='pending',
        cart_data={
            'cart_id': cart.id,
            'total_price': float(cart.total_price),
            'items': [{
                'product_id': product.id,
                'product_name': product.name,
                'variant_id': variant.id,
                'quantity': cart_item.quantity,
                'price': float(variant.price),
                'total': float(cart_item.total_price)
            }]
        },
        shipping_address={
            'name': 'Test User',
            'phone': '9876543210',
            'address': '123 Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'pincode': '123456'
        },
        billing_address={
            'name': 'Test User',
            'phone': '9876543210',
            'address': '123 Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'pincode': '123456'
        }
    )
    
    print(f"✓ Created Pathlog payment: ID {payment.id}")
    
    # Verify wallet and process payment
    payment.verify_pathlog_wallet('9876543210', '123456')
    success, message = payment.process_pathlog_wallet_payment()
    
    if success:
        print(f"✓ Payment processed successfully: {message}")
        
        # Check cart state after payment
        cart.refresh_from_db()
        items_after = cart.items.count()
        
        print(f"ℹ Cart has {items_after} items after checkout")
        
        if items_after == 0:
            print("✅ SUCCESS: Cart was properly cleared!")
        else:
            print("❌ ISSUE: Cart still has items after checkout")
            
            # List remaining items
            for item in cart.items.all():
                print(f"  - {item.quantity}x {item.product.name}")
        
        # Check if order was created
        if payment.order:
            order = payment.order
            print(f"✓ Order created: #{order.order_number}")
            print(f"✓ Order has {order.items.count()} items")
            
            # Verify order items match cart items
            for order_item in order.items.all():
                print(f"  - {order_item.quantity}x {order_item.product.name} @ ₹{order_item.price}")
        else:
            print("❌ No order was created")
            
    else:
        print(f"❌ Payment failed: {message}")
    
    print()
    print("=" * 50)
    print("CART CLEARING TEST RESULTS")
    print("=" * 50)
    
    if success and items_after == 0:
        print("🎉 CART CLEARING WORKS CORRECTLY!")
        print("✅ Cart is properly cleared after Pathlog Wallet checkout")
        return True
    else:
        print("❌ CART CLEARING ISSUE DETECTED!")
        print("🔧 Need to investigate cart clearing logic")
        return False

if __name__ == '__main__':
    result = test_cart_clearing()
    if result:
        print("\nTest PASSED - Cart clearing works correctly!")
    else:
        print("\nTest FAILED - Cart clearing needs attention!")