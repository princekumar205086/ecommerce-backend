# inventory/management/commands/sync_stock.py
"""
Management command to synchronize stock levels across the system
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from inventory.models import InventoryItem
from inventory.real_time_sync import RealTimeStockManager
from products.models import Product, ProductVariant


class Command(BaseCommand):
    help = 'Synchronize stock levels between InventoryItem and Product/ProductVariant models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=int,
            help='Sync stock for a specific product ID'
        )
        parser.add_argument(
            '--warehouse-id',
            type=int,
            help='Sync stock for a specific warehouse ID'
        )
        parser.add_argument(
            '--check-alerts',
            action='store_true',
            help='Check and create low stock alerts'
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(f'Starting stock synchronization at {start_time}')
        )

        # Filter inventory items if specific IDs provided
        inventory_items = InventoryItem.objects.select_related('product', 'variant', 'warehouse')
        
        if options['product_id']:
            inventory_items = inventory_items.filter(product_id=options['product_id'])
        
        if options['warehouse_id']:
            inventory_items = inventory_items.filter(warehouse_id=options['warehouse_id'])

        total_items = inventory_items.count()
        self.stdout.write(f'Found {total_items} inventory items to sync')

        synced_products = set()
        synced_variants = set()

        with transaction.atomic():
            for i, item in enumerate(inventory_items, 1):
                try:
                    # Sync product stock field
                    RealTimeStockManager.sync_product_stock_field(item)
                    
                    # Track what we've synced
                    synced_products.add(item.product.id)
                    if item.variant:
                        synced_variants.add(item.variant.id)

                    if i % 100 == 0:
                        self.stdout.write(f'Processed {i}/{total_items} items...')

                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(
                            f'Error syncing item {item.id}: {str(e)}'
                        )
                    )

        # Check for low stock alerts if requested
        if options['check_alerts']:
            self.stdout.write('Checking for low stock alerts...')
            RealTimeStockManager.check_low_stock_alerts()

        end_time = timezone.now()
        duration = end_time - start_time

        self.stdout.write(
            self.style.SUCCESS(
                f'\nStock synchronization completed!\n'
                f'Duration: {duration.total_seconds():.2f} seconds\n'
                f'Products synced: {len(synced_products)}\n'
                f'Variants synced: {len(synced_variants)}\n'
                f'Inventory items processed: {total_items}'
            )
        )
