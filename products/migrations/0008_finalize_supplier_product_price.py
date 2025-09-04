# products/migrations/0008_finalize_supplier_product_price.py
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    
    dependencies = [
        ('products', '0007_migrate_product_data'),
    ]
    
    operations = [
        # Remove the old product field
        migrations.RemoveField(
            model_name='supplierproductprice',
            name='product',
        ),
        # Make product_variant non-nullable
        migrations.AlterField(
            model_name='supplierproductprice',
            name='product_variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_prices', to='products.productvariant'),
        ),
        # Add back the unique constraint
        migrations.AlterUniqueTogether(
            name='supplierproductprice',
            unique_together={('supplier', 'product_variant', 'pincode', 'district')},
        ),
    ]
