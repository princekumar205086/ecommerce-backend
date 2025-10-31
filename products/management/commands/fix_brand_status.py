from django.core.management.base import BaseCommand
from products.models import Brand

class Command(BaseCommand):
    help = 'Fix brand publish status - set brands to published status for public API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--all',
            action='store_true', 
            help='Publish ALL brands (use with caution)',
        )
        parser.add_argument(
            '--approved-only',
            action='store_true',
            help='Only publish brands that are already approved status',
        )
        parser.add_argument(
            '--approve-pending',
            action='store_true',
            help='Approve and publish all pending brands',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        publish_all = options['all']
        approved_only = options['approved_only']
        approve_pending = options['approve_pending']
        
        self.stdout.write("=== Brand Publish Status Fix ===")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        total_brands = Brand.objects.count()
        self.stdout.write(f"Total brands in database: {total_brands}")
        
        if total_brands == 0:
            self.stdout.write(self.style.ERROR("No brands found!"))
            return
        
        # Current status
        public_brands = Brand.objects.filter(status__in=['approved', 'published'], is_publish=True)
        pending_brands = Brand.objects.filter(status='pending')
        self.stdout.write(f"Currently published brands: {public_brands.count()}")
        self.stdout.write(f"Pending brands: {pending_brands.count()}")
        
        if approve_pending:
            # Approve and publish all pending brands
            brands_to_update = Brand.objects.filter(status='pending')
            self.stdout.write(f"Pending brands to approve and publish: {brands_to_update.count()}")
            
            if not dry_run:
                updated_count = 0
                for brand in brands_to_update:
                    brand.status = 'published'
                    brand.is_publish = True
                    brand.save()
                    updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Approved and published {updated_count} pending brands"))
            
        elif publish_all:
            # Publish all brands 
            brands_to_update = Brand.objects.filter(is_publish=False)
            self.stdout.write(f"Brands to publish (ALL): {brands_to_update.count()}")
            
            if not dry_run:
                updated_count = 0
                for brand in brands_to_update:
                    brand.status = 'published'
                    brand.is_publish = True
                    brand.save()
                    updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Published {updated_count} brands"))
            
        elif approved_only:
            # Only publish approved brands
            brands_to_update = Brand.objects.filter(status='approved', is_publish=False)
            self.stdout.write(f"Approved brands to publish: {brands_to_update.count()}")
            
            if not dry_run:
                updated_count = brands_to_update.update(is_publish=True)
                self.stdout.write(self.style.SUCCESS(f"Published {updated_count} approved brands"))
        
        else:
            # Default: publish brands with approved or published status but is_publish=False
            brands_to_update = Brand.objects.filter(
                status__in=['approved', 'published'], 
                is_publish=False
            )
            self.stdout.write(f"Approved/Published brands to fix: {brands_to_update.count()}")
            
            if not dry_run:
                updated_count = brands_to_update.update(is_publish=True)
                self.stdout.write(self.style.SUCCESS(f"Fixed {updated_count} brands"))
        
        # Show final status
        if not dry_run:
            final_public_brands = Brand.objects.filter(status__in=['approved', 'published'], is_publish=True)
            self.stdout.write(f"Final published brands count: {final_public_brands.count()}")
        
        self.stdout.write("\nUsage examples:")
        self.stdout.write("  python manage.py fix_brand_status --dry-run")
        self.stdout.write("  python manage.py fix_brand_status --approved-only")
        self.stdout.write("  python manage.py fix_brand_status --approve-pending  # For pending brands")
        self.stdout.write("  python manage.py fix_brand_status --all  # Use with caution")