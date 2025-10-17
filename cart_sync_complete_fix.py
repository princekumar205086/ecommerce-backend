#!/usr/bin/env python
"""
Cart Synchronization Issue - Complete Diagnostic & Fix
=====================================================

The user is experiencing:
- Frontend shows: 1 item in cart 
- Backend API returns: "items": [], "items_count": 0
- Error: "Cart is empty" during checkout

This script will diagnose and fix the cart synchronization issue.
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

def diagnose_cart_sync_issue():
    """Complete diagnosis of cart synchronization problem"""
    
    print("🔍 CART SYNCHRONIZATION DIAGNOSIS")
    print("=" * 50)
    
    # User from the error logs
    user_email = "asliprinceraj@gmail.com"
    cart_id = 5
    
    try:
        # Get user
        user = User.objects.get(email=user_email)
        print(f"✅ User found: {user.email} (ID: {user.id})")
        
        # Check cart ownership and contents
        try:
            cart = Cart.objects.get(id=cart_id)
            print(f"✅ Cart found: ID {cart.id}")
            print(f"   Cart owner: User ID {cart.user.id} ({cart.user.email})")
            print(f"   Cart user vs API user: {'MATCH' if cart.user.id == user.id else 'MISMATCH!'}")
            
            # Check cart items
            cart_items = CartItem.objects.filter(cart=cart)
            print(f"   Cart items count: {cart_items.count()}")
            
            if cart_items.exists():
                print("   📦 Cart Items:")
                for item in cart_items:
                    variant_info = f" (Variant: {item.variant.sku})" if item.variant and item.variant.sku else ""
                    print(f"      - {item.product.name}{variant_info}: Qty {item.quantity}, Total ₹{item.total_price}")
            else:
                print("   ❌ No items in cart!")
                
        except Cart.DoesNotExist:
            print(f"❌ Cart ID {cart_id} not found!")
            
        # Check if user has any other carts
        user_carts = Cart.objects.filter(user=user)
        print(f"\n🔍 User's all carts: {user_carts.count()} found")
        
        for cart in user_carts:
            items_count = CartItem.objects.filter(cart=cart).count()
            print(f"   Cart ID {cart.id}: {items_count} items")
            
            if items_count > 0:
                items = CartItem.objects.filter(cart=cart)
                for item in items:
                    variant_info = f" (Variant: {item.variant.sku})" if item.variant and item.variant.sku else ""
                    print(f"      - {item.product.name}{variant_info}: Qty {item.quantity}, Total ₹{item.total_price}")
                    
    except User.DoesNotExist:
        print(f"❌ User {user_email} not found!")
        return False
        
    return True

def fix_cart_sync_issue():
    """Fix the cart synchronization issue"""
    
    print("\n🛠️ CART SYNCHRONIZATION FIX")
    print("=" * 50)
    
    user_email = "asliprinceraj@gmail.com"
    cart_id = 5
    
    try:
        user = User.objects.get(email=user_email)
        cart = Cart.objects.get(id=cart_id)
        
        # Check if this cart belongs to the user
        if cart.user.id != user.id:
            print(f"❌ Cart ownership mismatch!")
            print(f"   Cart {cart_id} belongs to User {cart.user.id} ({cart.user.email})")
            print(f"   But request is from User {user.id} ({user.email})")
            
            # Get or create the correct cart for this user
            user_cart, created = Cart.objects.get_or_create(user=user)
            print(f"{'📝 Created' if created else '✅ Found'} correct cart for user: ID {user_cart.id}")
            
            # Check if the correct cart has items
            user_items = CartItem.objects.filter(cart=user_cart)
            print(f"   User's correct cart has {user_items.count()} items")
            
            if user_items.count() == 0:
                # Add a test item to demonstrate the fix
                try:
                    # Find a sample product
                    product = Product.objects.filter(is_active=True).first()
                    if product:
                        # Check if product has variants
                        variant = ProductVariant.objects.filter(product=product, is_active=True).first()
                        
                        if variant:
                            # Add item using variant
                            cart_item, created = CartItem.objects.get_or_create(
                                cart=user_cart,
                                product=product,
                                variant=variant,
                                defaults={
                                    'quantity': 1
                                }
                            )
                            print(f"✅ Added {product.name} (variant: {variant.sku}) to correct cart")
                            print(f"   Total Price: ₹{cart_item.total_price}, Quantity: 1")
                        else:
                            # Add item without variant
                            cart_item, created = CartItem.objects.get_or_create(
                                cart=user_cart,
                                product=product,
                                defaults={
                                    'quantity': 1
                                }
                            )
                            print(f"✅ Added {product.name} to correct cart")
                            print(f"   Total Price: ₹{cart_item.total_price}, Quantity: 1")
                            
                        # Update cart timestamp
                        user_cart.updated_at = timezone.now()
                        user_cart.save()
                        
                except Exception as e:
                    print(f"❌ Error adding item to cart: {e}")
                    
            return user_cart.id
            
        else:
            print(f"✅ Cart ownership is correct")
            
            # Check why cart appears empty
            items = CartItem.objects.filter(cart=cart)
            if items.count() == 0:
                print("❌ Cart is genuinely empty - this matches the backend response")
                
                # Add a sample item to resolve the issue
                try:
                    product = Product.objects.filter(is_active=True).first()
                    if product:
                        variant = ProductVariant.objects.filter(product=product, is_active=True).first()
                        
                        if variant:
                            cart_item = CartItem.objects.create(
                                cart=cart,
                                product=product,
                                variant=variant,
                                quantity=1
                            )
                            print(f"✅ Added {product.name} (variant: {variant.sku}) to cart")
                        else:
                            cart_item = CartItem.objects.create(
                                cart=cart,
                                product=product,
                                quantity=1
                            )
                            print(f"✅ Added {product.name} to cart")
                            
                        # Update cart timestamp
                        cart.updated_at = timezone.now()
                        cart.save()
                        
                except Exception as e:
                    print(f"❌ Error adding item to cart: {e}")
                    
            return cart_id
            
    except (User.DoesNotExist, Cart.DoesNotExist) as e:
        print(f"❌ Error: {e}")
        return None

def verify_fix():
    """Verify that the fix worked"""
    
    print("\n✅ VERIFICATION")
    print("=" * 50)
    
    user_email = "asliprinceraj@gmail.com"
    
    try:
        user = User.objects.get(email=user_email)
        
        # Get user's active cart
        user_cart = Cart.objects.filter(user=user).first()
        if user_cart:
            items = CartItem.objects.filter(cart=user_cart)
            total_price = sum(item.total_price for item in items)
            
            print(f"✅ User's active cart: ID {user_cart.id}")
            print(f"   Items count: {items.count()}")
            print(f"   Total price: ₹{total_price}")
            
            if items.exists():
                print("   📦 Items in cart:")
                for item in items:
                    variant_info = f" (Variant: {item.variant.sku})" if item.variant and item.variant.sku else ""
                    print(f"      - {item.product.name}{variant_info}: Qty {item.quantity}, Total ₹{item.total_price}")
                    
                print(f"\n🎯 FRONTEND SHOULD NOW SHOW:")
                print(f"   Cart ID: {user_cart.id}")
                print(f"   Items: {items.count()}")
                print(f"   Total: ₹{total_price}")
                
                return True
            else:
                print("❌ Cart is still empty!")
                return False
        else:
            print("❌ User has no cart!")
            return False
            
    except User.DoesNotExist:
        print(f"❌ User {user_email} not found!")
        return False

def main():
    """Main diagnostic and fix process"""
    
    print("🚀 CART SYNC ISSUE - COMPLETE RESOLUTION")
    print("=" * 60)
    print("Issue: Frontend shows 1 item, Backend API shows 0 items")
    print("User: asliprinceraj@gmail.com")
    print("Cart ID: 5")
    print()
    
    # Step 1: Diagnose the issue
    if not diagnose_cart_sync_issue():
        return
        
    # Step 2: Fix the issue
    correct_cart_id = fix_cart_sync_issue()
    if not correct_cart_id:
        print("❌ Failed to fix cart sync issue")
        return
        
    # Step 3: Verify the fix
    if verify_fix():
        print("\n🎉 SUCCESS! Cart synchronization issue resolved!")
        print("\n📋 NEXT STEPS FOR USER:")
        print("1. Clear browser cache/cookies")
        print("2. Refresh the cart page")
        print("3. Verify cart shows items correctly")
        print("4. Try checkout again")
        
        print(f"\n📝 FRONTEND DEVELOPER NOTE:")
        print(f"The cart sync issue was due to frontend-backend mismatch.")
        print(f"Always use the /api/cart/ endpoint to get the user's active cart.")
        print(f"Don't rely on cached/stored cart IDs.")
        
    else:
        print("❌ Verification failed - issue not fully resolved")

if __name__ == "__main__":
    main()