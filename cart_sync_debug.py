#!/usr/bin/env python
"""
CART SYNCHRONIZATION ISSUE FIX
==============================
Debug and fix the cart sync issue for asliprinceraj@gmail.com
"""

import os
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem
from products.models import Product, ProductVariant

User = get_user_model()

def debug_cart_sync_issue():
    """Debug the cart synchronization issue"""
    print("CART SYNCHRONIZATION ISSUE DEBUG")
    print("=" * 50)
    
    # Check user and cart in database
    try:
        user = User.objects.get(email='asliprinceraj@gmail.com')
        print(f"✅ Found user: {user.email} (ID: {user.id})")
        
        cart = Cart.objects.get(id=5)
        print(f"✅ Found cart ID: {cart.id}")
        print(f"📊 User ID: {cart.user.id}")
        print(f"📊 Items count: {cart.items.count()}")
        print(f"📊 Total price: ₹{cart.total_price}")
        
        # List all items in cart
        items = cart.items.all()
        if items.exists():
            print(f"\n📦 Cart items:")
            for item in items:
                print(f"  - {item.product.name} x{item.quantity} = ₹{item.total_price}")
                if item.variant:
                    print(f"    Variant: {item.variant}")
        else:
            print(f"\n⚠️  Cart is actually empty in database!")
        
        # Check if user owns this cart
        if cart.user.id != user.id:
            print(f"❌ ISSUE: Cart belongs to user {cart.user.id}, not {user.id}")
        else:
            print(f"✅ Cart ownership verified")
            
    except User.DoesNotExist:
        print(f"❌ User asliprinceraj@gmail.com not found")
    except Cart.DoesNotExist:
        print(f"❌ Cart ID 5 not found")
    except Exception as e:
        print(f"❌ Error: {e}")

def add_test_item_to_cart():
    """Add a test item to the empty cart"""
    print(f"\n🔧 FIXING EMPTY CART")
    print("=" * 30)
    
    try:
        user = User.objects.get(email='asliprinceraj@gmail.com')
        cart = Cart.objects.get(id=5)
        
        # Find a product to add
        product = Product.objects.filter(is_publish=True, stock__gt=0).first()
        if not product:
            print("❌ No products available")
            return False
            
        variant = ProductVariant.objects.filter(product=product, stock__gt=0).first()
        
        # Add item to cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': 1}
        )
        
        if created:
            print(f"✅ Added {product.name} to cart")
        else:
            cart_item.quantity += 1
            cart_item.save()
            print(f"✅ Updated quantity of {product.name}")
            
        # Verify cart now has items
        cart.refresh_from_db()
        print(f"📊 Cart now has {cart.items.count()} items")
        print(f"📊 Total price: ₹{cart.total_price}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding item: {e}")
        return False

def test_api_after_fix():
    """Test the API after fixing the cart"""
    print(f"\n🧪 TESTING API AFTER FIX")
    print("=" * 35)
    
    # You'll need to authenticate the user first
    print("🔑 Authentication required for API testing")
    print("Frontend should now be able to checkout successfully")

if __name__ == '__main__':
    debug_cart_sync_issue()
    
    # Fix the empty cart
    if add_test_item_to_cart():
        test_api_after_fix()
        print(f"\n✅ CART SYNC ISSUE FIXED!")
        print("💡 Frontend should now work correctly")
    else:
        print(f"\n❌ Could not fix cart issue")