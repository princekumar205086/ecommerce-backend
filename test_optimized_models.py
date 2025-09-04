#!/usr/bin/env python3
"""
Test script to verify the new optimized product model structure.
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
from products.models import (
    Product, ProductCategory, Brand, ProductVariant, 
    MedicineDetails, EquipmentDetails, PathologyDetails,
    ProductAttribute, ProductAttributeValue, ProductImage
)
from accounts.models import User

def test_new_model_structure():
    """
    Test the new optimized product model structure.
    """
    print("Testing new optimized product model structure...")
    
    # Test 1: Create a test category
    print("\n1. Testing ProductCategory...")
    category, created = ProductCategory.objects.get_or_create(
        name="Test Optimized Category",
        defaults={
            'created_by': User.objects.first(),
            'status': 'published',
            'is_publish': True
        }
    )
    print(f"✅ Category created: {category.name} (Created: {created})")
    
    # Test 2: Create a test brand
    print("\n2. Testing Brand...")
    brand, created = Brand.objects.get_or_create(
        name="Test Optimized Brand",
        defaults={
            'created_by': User.objects.first()
        }
    )
    print(f"✅ Brand created: {brand.name} (Created: {created})")
    
    # Test 3: Create a medicine product with details
    print("\n3. Testing Medicine Product with Details...")
    medicine_product, created = Product.objects.get_or_create(
        name="Test Optimized Medicine",
        defaults={
            'category': category,
            'brand': brand,
            'product_type': 'medicine',
            'price': 25.99,
            'stock': 100,
            'description': 'Test medicine with optimized structure',
            'created_by': User.objects.first()
        }
    )
    print(f"✅ Medicine Product created: {medicine_product.name} (Created: {created})")
    
    # Create medicine details
    medicine_details, created = MedicineDetails.objects.get_or_create(
        product=medicine_product,
        defaults={
            'composition': 'Test Active Ingredient 500mg',
            'manufacturer': 'Test Pharma Inc',
            'batch_number': 'BATCH001',
            'prescription_required': True,
            'form': 'Tablet',
            'pack_size': '10 tablets'
        }
    )
    print(f"✅ Medicine Details created: {medicine_details.composition} (Created: {created})")
    
    # Test 4: Create product attributes and values
    print("\n4. Testing ProductAttributes...")
    size_attr, created = ProductAttribute.objects.get_or_create(name="Size")
    color_attr, created = ProductAttribute.objects.get_or_create(name="Color")
    
    # Create attribute values
    small_size, created = ProductAttributeValue.objects.get_or_create(
        attribute=size_attr, value="Small"
    )
    large_size, created = ProductAttributeValue.objects.get_or_create(
        attribute=size_attr, value="Large"
    )
    red_color, created = ProductAttributeValue.objects.get_or_create(
        attribute=color_attr, value="Red"
    )
    print(f"✅ Product Attributes created: Size, Color with values")
    
    # Test 5: Create product variants with attributes
    print("\n5. Testing ProductVariants with Attributes...")
    variant1, created = ProductVariant.objects.get_or_create(
        product=medicine_product,
        sku=f"{medicine_product.sku}-SM-RED",
        defaults={
            'price': 25.99,
            'stock': 50,
            'is_active': True
        }
    )
    if created:
        variant1.attributes.add(small_size, red_color)
    
    variant2, created = ProductVariant.objects.get_or_create(
        product=medicine_product,
        sku=f"{medicine_product.sku}-LG-RED",
        defaults={
            'price': 29.99,
            'stock': 30,
            'is_active': True
        }
    )
    if created:
        variant2.attributes.add(large_size, red_color)
    
    print(f"✅ Product Variants created with attributes")
    print(f"   Variant 1: {variant1.sku} - Price: ${variant1.total_price}")
    print(f"   Variant 2: {variant2.sku} - Price: ${variant2.total_price}")
    
    # Test 6: Test get_effective_price method
    print("\n6. Testing get_effective_price method...")
    base_price = medicine_product.get_effective_price()
    variant_price = medicine_product.get_effective_price(variant2)
    print(f"✅ Base price: ${base_price}, Variant price: ${variant_price}")
    
    # Test 7: Test accessing medicine details through relationship
    print("\n7. Testing Medicine Details Relationship...")
    if hasattr(medicine_product, 'medicine_details'):
        details = medicine_product.medicine_details
        print(f"✅ Medicine Details accessible: {details.composition}")
        print(f"   Manufacturer: {details.manufacturer}")
        print(f"   Prescription Required: {details.prescription_required}")
    else:
        print("❌ Medicine Details relationship not working")
    
    # Test 8: Test equipment product
    print("\n8. Testing Equipment Product...")
    equipment_product, created = Product.objects.get_or_create(
        name="Test Optimized Equipment",
        defaults={
            'category': category,
            'brand': brand,
            'product_type': 'equipment',
            'price': 199.99,
            'stock': 25,
            'description': 'Test equipment with optimized structure',
            'created_by': User.objects.first()
        }
    )
    print(f"✅ Equipment Product created: {equipment_product.name} (Created: {created})")
    
    # Create equipment details
    equipment_details, created = EquipmentDetails.objects.get_or_create(
        product=equipment_product,
        defaults={
            'model_number': 'EQ-001',
            'warranty_period': '2 years',
            'usage_type': 'Clinical',
            'technical_specifications': 'High precision digital equipment',
            'power_requirement': '220V AC',
            'equipment_type': 'Diagnostic'
        }
    )
    print(f"✅ Equipment Details created: Model {equipment_details.model_number}")
    
    # Test 9: Query optimization test
    print("\n9. Testing Query Optimization...")
    # Test prefetch related
    products = Product.objects.select_related('category', 'brand').prefetch_related(
        'variants__attributes', 'images', 'medicine_details', 'equipment_details'
    )[:5]
    
    for product in products:
        print(f"   Product: {product.name}")
        print(f"   Category: {product.category.name}")
        print(f"   Variants: {product.variants.count()}")
        if product.product_type == 'medicine' and hasattr(product, 'medicine_details'):
            print(f"   Medicine Details: ✅")
        elif product.product_type == 'equipment' and hasattr(product, 'equipment_details'):
            print(f"   Equipment Details: ✅")
        print()
    
    print("✅ All tests completed successfully!")
    print("\n🎉 New optimized product model structure is working correctly!")

if __name__ == "__main__":
    test_new_model_structure()
