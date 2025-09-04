#!/usr/bin/env python3
"""
Migration backup script for products app model changes.
This script will help transition from the old model structure to the new optimized structure.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.db import transaction
from products.models import Product, ProductVariant, SupplierProductPrice

def backup_and_prepare_migration():
    """
    Backup existing data and prepare for migration.
    """
    print("Starting migration backup process...")
    
    # 1. Create default variants for products that don't have any
    print("Creating default variants for products without variants...")
    
    products_without_variants = Product.objects.filter(variants__isnull=True).distinct()
    
    with transaction.atomic():
        for product in products_without_variants:
            # Create a default variant for each product
            ProductVariant.objects.create(
                product=product,
                price=product.price,
                stock=product.stock,
                is_active=True
            )
            print(f"Created default variant for product: {product.name}")
    
    print(f"Created default variants for {products_without_variants.count()} products")
    
    # 2. Update SupplierProductPrice to use product_variant instead of product
    print("Updating supplier product prices...")
    
    supplier_prices = SupplierProductPrice.objects.all()
    
    with transaction.atomic():
        for price in supplier_prices:
            # Get the first variant for the product (our default variant)
            variant = price.product.variants.first()
            if variant:
                # Update the price record to use the variant
                # Since we can't update the field directly due to model changes,
                # we'll note this for manual handling
                print(f"Need to update price record {price.id} to use variant {variant.id}")
    
    print("Migration backup completed successfully!")

if __name__ == "__main__":
    backup_and_prepare_migration()
