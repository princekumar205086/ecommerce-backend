#!/usr/bin/env python
"""
Production Cart Sync Issue Analysis & Fix
=========================================

Based on the production logs:
- User: asliprinceraj@gmail.com (Production User ID: 36)
- Cart ID: 5 (belongs to different user in production)
- Frontend shows 1 item, Backend API shows 0 items
- Error: {"cart_id":["Cart is empty"]}

This script analyzes potential issues and provides fixes for production.
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
from payments.models import Payment
from django.utils import timezone

User = get_user_model()

def analyze_cart_sync_issues():
    """Analyze potential cart synchronization issues"""
    
    print("🔍 CART SYNC ISSUE ANALYSIS")
    print("=" * 50)
    print("Production Issue: Frontend shows 1 item, Backend API shows 0 items")
    print("User: asliprinceraj@gmail.com (Production ID: 36)")
    print("Cart ID: 5")
    print()
    
    print("📋 POTENTIAL ROOT CAUSES:")
    print("1. Cart Ownership Mismatch")
    print("   - Frontend using cart ID that belongs to different user")
    print("   - Session/authentication issues")
    print("   - Cached cart IDs in browser/localStorage")
    print()
    
    print("2. Cart-User Association Problems")
    print("   - User accessing cart from different session")
    print("   - Cart created under different user account")
    print("   - Cookie/JWT token issues")
    print()
    
    print("3. Database Consistency Issues")
    print("   - CartItem objects not properly linked to cart")
    print("   - Orphaned cart items")
    print("   - Transaction rollback issues")
    print()
    
    print("4. API Validation Logic")
    print("   - Cart ownership validation too strict")
    print("   - User-cart relationship not properly validated")
    print("   - API returning wrong cart data")
    print()

def demonstrate_local_cart_issues():
    """Demonstrate cart sync issues in local environment"""
    
    print("🧪 LOCAL CART SYNC DEMONSTRATION")
    print("=" * 50)
    
    # Create test users
    try:
        # Create user similar to production scenario
        test_user, created = User.objects.get_or_create(
            email='test.asliprinceraj@gmail.com',
            defaults={
                'first_name': 'Prince',
                'last_name': 'Kumar',
                'is_active': True
            }
        )
        
        if created:
            test_user.set_password('TestPassword123')
            test_user.save()
            
        print(f"✅ Test user created: {test_user.email} (ID: {test_user.id})")
        
        # Create another user (represents the cart owner)
        other_user, created = User.objects.get_or_create(
            email='other.user@test.com',
            defaults={
                'first_name': 'Other',
                'last_name': 'User',
                'is_active': True
            }
        )
        
        if created:
            other_user.set_password('TestPassword123')
            other_user.save()
            
        print(f"✅ Other user created: {other_user.email} (ID: {other_user.id})")
        
        # Create cart for other user with items
        other_cart, created = Cart.objects.get_or_create(user=other_user)
        print(f"✅ Cart for other user: ID {other_cart.id}")
        
        # Add item to other user's cart
        try:
            product = Product.objects.first()
            if product:
                cart_item, created = CartItem.objects.get_or_create(
                    cart=other_cart,
                    product=product,
                    defaults={'quantity': 1}
                )
                print(f"✅ Added {product.name} to other user's cart")
                print(f"   Cart {other_cart.id} now has {CartItem.objects.filter(cart=other_cart).count()} items")
        except Exception as e:
            print(f"⚠️ Could not add item to cart: {e}")
        
        # Simulate the production issue
        print(f"\n🎭 SIMULATING PRODUCTION ISSUE:")
        print(f"1. Test user {test_user.email} (ID: {test_user.id}) tries to access cart {other_cart.id}")
        print(f"2. Cart {other_cart.id} belongs to {other_user.email} (ID: {other_user.id})")
        print(f"3. Frontend would show items from cart {other_cart.id}")
        print(f"4. Backend API would return empty for user {test_user.id}")
        
        # Demonstrate correct resolution
        test_cart, created = Cart.objects.get_or_create(user=test_user)
        print(f"\n✅ CORRECT RESOLUTION:")
        print(f"   Test user's correct cart: ID {test_cart.id}")
        print(f"   Items in correct cart: {CartItem.objects.filter(cart=test_cart).count()}")
        
        return test_user.id, test_cart.id, other_cart.id
        
    except Exception as e:
        print(f"❌ Error in demonstration: {e}")
        return None, None, None

def provide_production_fixes():
    """Provide fixes for production environment"""
    
    print("\n🛠️ PRODUCTION FIXES")
    print("=" * 50)
    
    print("🔧 BACKEND FIXES ALREADY IMPLEMENTED:")
    print()
    
    print("1. Enhanced Cart Validation (payments/serializers.py)")
    print("   - Added user ID to error messages for debugging")
    print("   - Better cart ownership validation")
    print()
    
    print("2. Auto-Cart Creation (payments/views.py)")
    print("   - Automatically creates cart if user doesn't have one")
    print("   - Uses get_or_create() pattern instead of throwing errors")
    print()
    
    print("3. Improved Error Handling")
    print("   - Enhanced error messages with context")
    print("   - Better logging for debugging production issues")
    print()
    
    print("🚀 FRONTEND FIXES NEEDED:")
    print()
    
    print("1. Always Use User's Active Cart")
    frontend_fix_1 = '''
// WRONG: Using hardcoded cart ID
const cartId = 5; // This causes the issue!

// CORRECT: Get user's active cart from API
async function getUserActiveCart() {
    const response = await fetch('/api/cart/', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
        const cart = await response.json();
        return cart; // This is always the user's correct cart
    }
    throw new Error('Failed to get cart');
}
'''
    print(frontend_fix_1)
    
    print("2. Validate Cart Before Checkout")
    frontend_fix_2 = '''
async function checkoutWithValidation() {
    // Always get fresh cart data
    const cart = await getUserActiveCart();
    
    // Validate cart has items
    if (!cart.items || cart.items.length === 0) {
        throw new Error('Cart is empty. Please add items first.');
    }
    
    // Use the correct cart data for checkout
    const checkoutData = {
        // DON'T include cart_id - let backend use user's active cart
        payment_method: 'razorpay',
        shipping_address: shippingAddress,
        currency: 'INR'
    };
    
    return await createPayment(checkoutData);
}
'''
    print(frontend_fix_2)
    
    print("3. Clear Cart Cache")
    frontend_fix_3 = '''
// Clear any cached cart IDs
localStorage.removeItem('cartId');
sessionStorage.removeItem('cartId');

// Always fetch cart data from API
function clearCartCache() {
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.includes('cart') || key.includes('Cart')) {
            keysToRemove.push(key);
        }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key));
}
'''
    print(frontend_fix_3)

def provide_debugging_commands():
    """Provide debugging commands for production"""
    
    print("\n🔍 PRODUCTION DEBUGGING COMMANDS")
    print("=" * 50)
    
    print("For production server, run these Django shell commands:")
    print()
    
    debug_commands = '''
# 1. Check user and cart ownership
python manage.py shell

from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem

User = get_user_model()

# Find the user
user = User.objects.get(email='asliprinceraj@gmail.com')
print(f"User: {user.email} (ID: {user.id})")

# Check cart 5 ownership
try:
    cart = Cart.objects.get(id=5)
    print(f"Cart 5 owner: {cart.user.email} (ID: {cart.user.id})")
    print(f"Cart items: {CartItem.objects.filter(cart=cart).count()}")
except Cart.DoesNotExist:
    print("Cart 5 not found")

# Get user's correct cart
user_cart = Cart.objects.filter(user=user).first()
if user_cart:
    print(f"User's cart: ID {user_cart.id}")
    print(f"User's cart items: {CartItem.objects.filter(cart=user_cart).count()}")
else:
    print("User has no cart - will be auto-created")

# 2. Fix the issue by adding item to user's correct cart
user_cart, created = Cart.objects.get_or_create(user=user)
print(f"User's cart: ID {user_cart.id} ({'created' if created else 'existing'})")

# Add a product to the cart (replace with actual product ID)
from products.models import Product
product = Product.objects.filter(status='approved').first()
if product:
    cart_item, created = CartItem.objects.get_or_create(
        cart=user_cart,
        product=product,
        defaults={'quantity': 1}
    )
    print(f"Added {product.name} to cart")
    print(f"Cart now has {CartItem.objects.filter(cart=user_cart).count()} items")
'''
    
    print(debug_commands)

def main():
    """Main analysis and fix guide"""
    
    print("🚀 PRODUCTION CART SYNC ISSUE - COMPLETE ANALYSIS")
    print("=" * 70)
    print("Issue: asliprinceraj@gmail.com cart sync problem in production")
    print("Frontend shows 1 item, Backend API shows 0 items")
    print()
    
    # Analyze issues
    analyze_cart_sync_issues()
    
    # Demonstrate locally
    test_user_id, test_cart_id, other_cart_id = demonstrate_local_cart_issues()
    
    # Provide production fixes
    provide_production_fixes()
    
    # Provide debugging commands
    provide_debugging_commands()
    
    print("\n🎯 SUMMARY")
    print("=" * 50)
    print("✅ Root Cause: Cart ownership mismatch")
    print("✅ Backend Fixes: Already implemented (auto-cart creation, better validation)")
    print("⚠️ Frontend Fix Needed: Use /api/cart/ endpoint, don't hardcode cart IDs")
    print("🔧 Production Debug: Run Django shell commands to verify and fix")
    
    print("\n📋 IMMEDIATE ACTIONS:")
    print("1. Run production debugging commands to confirm issue")
    print("2. Add item to user's correct cart if empty")
    print("3. Update frontend to use dynamic cart fetching")
    print("4. Test checkout with asliprinceraj@gmail.com")

if __name__ == "__main__":
    main()