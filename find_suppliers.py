#!/usr/bin/env python3
"""
Find suppliers with products and test duty system
"""
import os
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

def find_suppliers_with_products():
    """Find suppliers who actually have published products"""
    
    print("=== FINDING SUPPLIERS WITH PRODUCTS ===\n")
    
    # Get all published products and their creators
    published_products = Product.objects.filter(
        status='published',
        is_publish=True
    ).select_related('created_by')
    
    print(f"Total published products: {published_products.count()}")
    
    # Group by supplier
    suppliers_with_products = {}
    for product in published_products:
        if product.created_by:
            email = product.created_by.email
            role = product.created_by.role
            if email not in suppliers_with_products:
                suppliers_with_products[email] = {
                    'user': product.created_by,
                    'role': role,
                    'products': [],
                    'is_on_duty': product.created_by.is_on_duty
                }
            suppliers_with_products[email]['products'].append(product)
    
    print(f"\nUsers with published products:")
    for email, data in suppliers_with_products.items():
        user = data['user']
        product_count = len(data['products'])
        duty_status = "ON" if data['is_on_duty'] else "OFF"
        print(f"  {email} ({data['role']}) - {product_count} products - Duty: {duty_status}")
    
    # Find the best supplier to test with (one with most products)
    if suppliers_with_products:
        best_supplier_email = max(suppliers_with_products.keys(), 
                                 key=lambda x: len(suppliers_with_products[x]['products']))
        best_supplier_data = suppliers_with_products[best_supplier_email]
        best_supplier = best_supplier_data['user']
        
        print(f"\n🎯 Best supplier to test with:")
        print(f"   Email: {best_supplier.email}")
        print(f"   Role: {best_supplier.role}")
        print(f"   Products: {len(best_supplier_data['products'])}")
        print(f"   Current duty: {'ON' if best_supplier.is_on_duty else 'OFF'}")
        
        # Show some product details
        print(f"\n📦 Sample products:")
        for i, product in enumerate(best_supplier_data['products'][:3]):
            print(f"   {i+1}. {product.name} (ID: {product.id})")
        
        return best_supplier
    else:
        print("No suppliers with products found!")
        return None

if __name__ == "__main__":
    find_suppliers_with_products()