# Generated by Django 5.2 on 2025-06-14 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_alter_brand_options_alter_productauditlog_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='brand',
            name='image',
            field=models.URLField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='productcategory',
            name='icon',
            field=models.URLField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.URLField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='productimage',
            name='image',
            field=models.URLField(),
        ),
    ]
