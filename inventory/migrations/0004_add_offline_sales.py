# Generated by Django 5.2 on 2025-07-22 17:40

import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_alter_inventoryitem_unique_together_and_more'),
        ('products', '0005_product_sku'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OfflineSale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sale_number', models.CharField(editable=False, max_length=50, unique=True)),
                ('customer_name', models.CharField(blank=True, max_length=200)),
                ('customer_phone', models.CharField(blank=True, max_length=20)),
                ('customer_email', models.EmailField(blank=True, max_length=254)),
                ('subtotal', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('card', 'Card'), ('upi', 'UPI'), ('cheque', 'Cheque'), ('bank_transfer', 'Bank Transfer'), ('other', 'Other')], default='cash', max_length=20)),
                ('payment_reference', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('sale_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_cancelled', models.BooleanField(default=False)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_reason', models.TextField(blank=True)),
                ('vendor', models.ForeignKey(limit_choices_to={'role': 'supplier'}, on_delete=django.db.models.deletion.PROTECT, related_name='offline_sales', to=settings.AUTH_USER_MODEL)),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='offline_sales', to='inventory.warehouse')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OfflineSaleItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount_per_item', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('batch_number', models.CharField(blank=True, max_length=100)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='offline_sale_items', to='products.product')),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='inventory.offlinesale')),
                ('variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='offline_sale_items', to='products.productvariant')),
            ],
        ),
        migrations.AddIndex(
            model_name='offlinesale',
            index=models.Index(fields=['vendor', 'sale_date'], name='inventory_o_vendor__fcc5e4_idx'),
        ),
        migrations.AddIndex(
            model_name='offlinesale',
            index=models.Index(fields=['warehouse', 'sale_date'], name='inventory_o_warehou_9ba468_idx'),
        ),
        migrations.AddIndex(
            model_name='offlinesale',
            index=models.Index(fields=['sale_number'], name='inventory_o_sale_nu_964675_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='offlinesaleitem',
            unique_together={('sale', 'product', 'variant', 'batch_number')},
        ),
    ]
