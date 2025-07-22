# inventory/management/commands/create_sample_data.py
"""
Management command to create sample data for testing offline sales
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from accounts.models import User
from products.models import Product, ProductCategory, Brand
from inventory.models import Warehouse, Supplier, InventoryItem
from inventory.offline_sales import OfflineSaleManager


class Command(BaseCommand):
    help = 'Create sample data for testing offline sales functionality'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data for offline sales testing...')

        # Create a supplier user
        supplier, created = User.objects.get_or_create(
            email='supplier@test.com',
            defaults={
                'full_name': 'Test Supplier',
                'role': 'supplier',
                'contact': '9876543210'
            }
        )
        if created:
            supplier.set_password('testpass123')
            supplier.save()
            self.stdout.write(f'Created supplier user: {supplier.email}')

        # Create a warehouse
        warehouse, created = Warehouse.objects.get_or_create(
            name='Main Store',
            defaults={'location': 'Downtown Medical District'}
        )
        if created:
            self.stdout.write(f'Created warehouse: {warehouse.name}')

        # Create a supplier company
        supplier_company, created = Supplier.objects.get_or_create(
            name='MediCorp Suppliers',
            defaults={
                'contact_details': 'Contact: +91-9876543210\nEmail: sales@medicorp.com',
                'gstin': '29ABCDE1234F1Z5',
                'license_number': 'DL20B001234'
            }
        )
        if created:
            self.stdout.write(f'Created supplier company: {supplier_company.name}')

        # Create sample products with inventory
        category, created = ProductCategory.objects.get_or_create(
            name='Medicines',
            defaults={'slug': 'medicines', 'created_by': supplier}
        )
        
        brand, created = Brand.objects.get_or_create(
            name='Generic Pharma',
            defaults={'created_by': supplier}
        )

        # Sample products
        products_data = [
            {
                'name': 'Paracetamol 500mg',
                'price': Decimal('25.00'),
                'stock_qty': 100,
                'product_type': 'medicine'
            },
            {
                'name': 'Blood Pressure Monitor',
                'price': Decimal('1500.00'),
                'stock_qty': 20,
                'product_type': 'equipment'
            },
            {
                'name': 'Digital Thermometer',
                'price': Decimal('350.00'),
                'stock_qty': 50,
                'product_type': 'equipment'
            },
            {
                'name': 'Glucose Test Strips',
                'price': Decimal('450.00'),
                'stock_qty': 75,
                'product_type': 'pathology'
            }
        ]

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    'price': product_data['price'],
                    'stock': product_data['stock_qty'],
                    'category': category,
                    'brand': brand,
                    'product_type': product_data['product_type'],
                    'created_by': supplier,
                    'description': f'Sample {product_data["product_type"]} for testing'
                }
            )
            
            if created:
                self.stdout.write(f'Created product: {product.name}')
                
                # Create inventory item
                inventory_item, inv_created = InventoryItem.objects.get_or_create(
                    product=product,
                    warehouse=warehouse,
                    defaults={
                        'quantity': product_data['stock_qty'],
                        'low_stock_threshold': 10,
                        'supplier': supplier_company,
                        'purchase_price': product_data['price'] * Decimal('0.8')  # 20% margin
                    }
                )
                
                if inv_created:
                    self.stdout.write(f'Created inventory for: {product.name}')

        # Create a sample offline sale
        try:
            sample_items = [
                {
                    'product': Product.objects.get(name='Paracetamol 500mg'),
                    'quantity': 2,
                    'unit_price': Decimal('25.00')
                },
                {
                    'product': Product.objects.get(name='Digital Thermometer'),
                    'quantity': 1,
                    'unit_price': Decimal('350.00')
                }
            ]
            
            customer_data = {
                'name': 'John Doe',
                'phone': '9876543210',
                'email': 'john@example.com'
            }
            
            payment_data = {
                'method': 'cash',
                'reference': '',
                'notes': 'Sample offline sale for testing'
            }
            
            sale = OfflineSaleManager.create_offline_sale(
                vendor=supplier,
                warehouse=warehouse,
                items_data=sample_items,
                customer_data=customer_data,
                payment_data=payment_data
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created sample offline sale: {sale.sale_number} '
                    f'(Total: ₹{sale.total_amount})'
                )
            )
            
        except Exception as e:
            self.stderr.write(f'Error creating sample sale: {str(e)}')

        self.stdout.write(
            self.style.SUCCESS(
                '\nSample data creation completed!\n'
                f'Supplier Login: {supplier.email} / testpass123\n'
                'You can now test offline sales functionality.'
            )
        )
