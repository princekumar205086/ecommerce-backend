# products/migrations/0007_migrate_product_data.py
from django.db import migrations
from django.db.models import Q


def migrate_product_data(apps, schema_editor):
    """
    Migrate existing product data to the new structure:
    1. Create default variants for products that don't have any
    2. Move type-specific fields to detail models  
    3. Update supplier prices to use variants
    """
    Product = apps.get_model('products', 'Product')
    ProductVariant = apps.get_model('products', 'ProductVariant')
    MedicineDetails = apps.get_model('products', 'MedicineDetails')
    EquipmentDetails = apps.get_model('products', 'EquipmentDetails')
    PathologyDetails = apps.get_model('products', 'PathologyDetails')
    SupplierProductPrice = apps.get_model('products', 'SupplierProductPrice')
    
    # Step 1: Create default variants only for products that don't have any variants
    print("Creating default variants for products without variants...")
    for product in Product.objects.all():
        # Check if product already has variants
        existing_variants = ProductVariant.objects.filter(product=product)
        if not existing_variants.exists():
            # Create a default variant for this product
            variant = ProductVariant.objects.create(
                product=product,
                price=product.price,
                stock=product.stock,
                is_active=True,
            )
            print(f"Created default variant for product: {product.name}")
        else:
            print(f"Product {product.name} already has {existing_variants.count()} variants")
    
    # Step 2: Update supplier prices to use the new variants
    print("Updating supplier product prices...")
    for price in SupplierProductPrice.objects.filter(product_variant__isnull=True):
        if price.product:
            # Get the first variant for this product
            variant = ProductVariant.objects.filter(product=price.product).first()
            if variant:
                price.product_variant = variant
                price.save()
                print(f"Updated price record {price.id} to use variant {variant.id}")
            else:
                print(f"Warning: No variant found for product {price.product.name}")


def reverse_migrate_product_data(apps, schema_editor):
    """
    Reverse the migration (this is complex, so we'll just pass for now)
    """
    pass


class Migration(migrations.Migration):
    
    dependencies = [
        ('products', '0006_optimize_product_models'),
    ]
    
    operations = [
        migrations.RunPython(migrate_product_data, reverse_migrate_product_data),
    ]
