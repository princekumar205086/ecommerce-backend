# Generated by Django 5.2 on 2025-06-09 19:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0001_initial'),
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_items', to='products.product'),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inventory_items', to='products.productvariant'),
        ),
        migrations.AddField(
            model_name='inventorytransaction',
            name='inventory_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='inventory.inventoryitem'),
        ),
        migrations.AddField(
            model_name='inventorytransaction',
            name='performed_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventory_items', to='inventory.supplier'),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='warehouse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inventory_items', to='inventory.warehouse'),
        ),
        migrations.AlterUniqueTogether(
            name='inventoryitem',
            unique_together={('product', 'variant', 'warehouse')},
        ),
    ]
