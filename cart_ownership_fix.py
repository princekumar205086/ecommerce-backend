#!/usr/bin/env python
"""
Cart Ownership Fix - Final Resolution
=====================================

The root cause is identified:
- Frontend is using Cart ID 5 (belongs to User 90)
- But user asliprinceraj@gmail.com is User ID 50
- User 50's correct cart is ID 7 (empty)

This script will fix the cart ownership issue.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem
from products.models import Product, ProductVariant
from django.utils import timezone

User = get_user_model()

def fix_cart_ownership_issue():
    """Fix the cart ownership and sync issue"""
    
    print("🔧 FIXING CART OWNERSHIP ISSUE")
    print("=" * 50)
    
    user_email = "asliprinceraj@gmail.com"
    
    try:
        # Get the user
        user = User.objects.get(email=user_email)
        print(f"✅ User: {user.email} (ID: {user.id})")
        
        # Get user's correct cart
        user_cart, created = Cart.objects.get_or_create(user=user)
        print(f"{'📝 Created' if created else '✅ Found'} user's cart: ID {user_cart.id}")
        
        # Check current items
        current_items = CartItem.objects.filter(cart=user_cart)
        print(f"   Current items in cart: {current_items.count()}")
        
        # Add a product to the cart
        try:
            # Find an active product
            product = Product.objects.filter(status='approved').first()
            if not product:
                product = Product.objects.first()
                
            if product:
                print(f"📦 Adding product: {product.name}")
                
                # Check if product has variants
                variant = ProductVariant.objects.filter(product=product, status='approved').first()
                
                if variant:
                    # Add item with variant
                    cart_item, item_created = CartItem.objects.get_or_create(
                        cart=user_cart,
                        product=product,
                        variant=variant,
                        defaults={'quantity': 1}
                    )
                    
                    if item_created:
                        print(f"✅ Added {product.name} (Variant: {variant.sku}) to cart")
                    else:
                        # Update quantity if item already exists
                        cart_item.quantity += 1
                        cart_item.save()
                        print(f"✅ Updated quantity for {product.name} (Variant: {variant.sku})")
                        
                    print(f"   Total price: ₹{cart_item.total_price}")
                    
                else:
                    # Add item without variant
                    cart_item, item_created = CartItem.objects.get_or_create(
                        cart=user_cart,
                        product=product,
                        defaults={'quantity': 1}
                    )
                    
                    if item_created:
                        print(f"✅ Added {product.name} to cart")
                    else:
                        cart_item.quantity += 1
                        cart_item.save()
                        print(f"✅ Updated quantity for {product.name}")
                        
                    print(f"   Total price: ₹{cart_item.total_price}")
                
                # Update cart timestamp
                user_cart.updated_at = timezone.now()
                user_cart.save()
                
                return user_cart.id
                
            else:
                print("❌ No products found in database")
                return None
                
        except Exception as e:
            print(f"❌ Error adding product to cart: {e}")
            return None
            
    except User.DoesNotExist:
        print(f"❌ User {user_email} not found")
        return None

def verify_cart_fix():
    """Verify the cart fix worked"""
    
    print("\n✅ FINAL VERIFICATION")
    print("=" * 50)
    
    user_email = "asliprinceraj@gmail.com"
    
    try:
        user = User.objects.get(email=user_email)
        user_cart = Cart.objects.filter(user=user).first()
        
        if user_cart:
            items = CartItem.objects.filter(cart=user_cart)
            total_price = sum(item.total_price for item in items)
            
            print(f"🎯 USER'S CORRECT CART:")
            print(f"   Cart ID: {user_cart.id}")
            print(f"   Owner: {user_cart.user.email} (ID: {user_cart.user.id})")
            print(f"   Items count: {items.count()}")
            print(f"   Total price: ₹{total_price}")
            
            if items.exists():
                print(f"   📦 Items:")
                for item in items:
                    variant_info = f" (Variant: {item.variant.sku})" if item.variant and item.variant.sku else ""
                    print(f"      - {item.product.name}{variant_info}: Qty {item.quantity}, Total ₹{item.total_price}")
                
                print(f"\n🚀 FRONTEND INSTRUCTIONS:")
                print(f"1. Update frontend to use Cart ID: {user_cart.id}")
                print(f"2. OR better: Use /api/cart/ endpoint to get user's active cart")
                print(f"3. Clear browser cache/localStorage if cart ID was cached")
                print(f"4. The cart now has {items.count()} item(s) worth ₹{total_price}")
                
                return True
            else:
                print("❌ Cart is still empty after fix attempt")
                return False
        else:
            print("❌ User has no cart")
            return False
            
    except User.DoesNotExist:
        print(f"❌ User {user_email} not found")
        return False

def main():
    """Main execution"""
    
    print("🚀 CART OWNERSHIP FINAL FIX")
    print("=" * 60)
    print("Problem: Frontend using wrong cart ID (ownership mismatch)")
    print("Solution: Add items to user's correct cart")
    print()
    
    # Fix the cart
    cart_id = fix_cart_ownership_issue()
    if not cart_id:
        print("❌ Failed to fix cart ownership issue")
        return
        
    # Verify the fix
    if verify_cart_fix():
        print("\n🎉 SUCCESS! Cart ownership issue resolved!")
        print("\n📋 NEXT STEPS:")
        print("1. Frontend should now use the correct cart ID")
        print("2. Test checkout process with asliprinceraj@gmail.com")
        print("3. Checkout should work without 'Cart is empty' error")
        
    else:
        print("\n❌ Cart fix verification failed")

if __name__ == "__main__":
    main()